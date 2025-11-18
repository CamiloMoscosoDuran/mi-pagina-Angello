from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
import json
from decimal import Decimal

app = Flask(__name__)

# ----------------------------------------------------------------------
# 🔐 CLAVE SECRETA Y CONFIG BD
# ----------------------------------------------------------------------
app.secret_key = 'TU_CLAVE_SECRETA_SUPER_LARGA_Y_COMPLEJA'

DB_HOST = 'angello.ctfnsorvnxz2.us-east-1.rds.amazonaws.com'
DB_USER = 'admin'
DB_PASSWORD = 'angello1234'
DB_NAME = 'dbangello'

# ----------------------------------------------------------------------
# 🔹 FUNCIÓN DE CONEXIÓN A BD
# ----------------------------------------------------------------------
def get_db_connection():
    try:
        conexion = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False
        )
        return conexion
    except Exception as e:
        print("❌ Error al conectar con la base de datos:", e)
        return None

# ------------------------------
# Helper: inicializar carrito
# ------------------------------
def ensure_cart():
    if 'cart' not in session:
        session['cart'] = []  # lista de items {id,name,price,qty,img}
        session.modified = True

def cart_count():
    ensure_cart()
    return sum(int(i.get('qty',1)) for i in session['cart'])

def cart_total():
    ensure_cart()
    total = Decimal('0.00')
    for item in session['cart']:
        total += Decimal(str(item.get('price', 0))) * int(item.get('qty',1))
    return float(total)

# ----------------------------------------------------------------------
# 🔹 RUTAS DE AUTENTICACIÓN
# ----------------------------------------------------------------------
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        print('🔵 [DEBUG] POST recibido en /registro')
        nombre = request.form.get('nombre')
        apellidos = request.form.get('apellidos')
        usuario = request.form.get('usuario')
        dni = request.form.get('dni')
        correo = request.form.get('correo')
        contrasena = request.form.get('contrasena')
        print(f'🔵 [DEBUG] Datos recibidos: nombre={nombre}, apellidos={apellidos}, usuario={usuario}, dni={dni}, correo={correo}')

        contrasena_hash = generate_password_hash(contrasena)

        conn = get_db_connection()
        if not conn:
            print('🔴 [ERROR] No se pudo conectar a la base de datos')
            return render_template("registro.html", error="No se pudo conectar a la base de datos.")

        try:
            with conn.cursor() as cursor:
                print('🟢 [DEBUG] Conexión a BD exitosa, insertando en Registro...')
                cursor.execute("""
                    INSERT INTO Registro (nombre, apellidos, usuario, dni, correo)
                    VALUES (%s, %s, %s, %s, %s)
                """, (nombre, apellidos, usuario, dni, correo))
                print('🟢 [DEBUG] Insert en Registro OK, insertando en Usuarios...')
                cursor.execute("""
                    INSERT INTO Usuarios (nombre, correo, contrasena_hash)
                    VALUES (%s, %s, %s)
                """, (nombre, correo, contrasena_hash))
                conn.commit()
                print('✅ [DEBUG] Registro completado y commit hecho')
                flash('¡Cuenta creada exitosamente! Ahora solo inicia sesión.', 'success')
                return redirect(url_for('inicio_secion'))

        except Exception as e:
            print("❌ ERROR REGISTRO:", e)
            conn.rollback()
            return render_template("registro.html",
                error="Hubo un error al registrarte. Verifica tus datos.")

        finally:
            conn.close()
            print('🔵 [DEBUG] Conexión cerrada')

    return render_template("registro.html")




@app.route('/inicio_secion', methods=['GET', 'POST'])
def inicio_secion():
    success_message = request.args.get('success')

    if session.get('loggedin'):
        return redirect(url_for('inicio_premium'))

    if request.method == 'POST':
        correo = request.form['correo']
        contrasena = request.form['contrasena']

        conn = get_db_connection()
        if conn is None:
            flash('Error de conexión a la base de datos.', 'error')
            return render_template('inicio_secion.html', loggedin=False)

        try:

            with conn.cursor() as cursor:
                sql = "SELECT id, nombre, correo, contrasena_hash FROM Usuarios WHERE correo = %s"
                cursor.execute(sql, (correo,))
                user = cursor.fetchone()

                # Buscar apodo/usuario en Registro
                apodo = None
                if user:
                    cursor.execute("SELECT usuario FROM Registro WHERE correo = %s", (correo,))
                    reg = cursor.fetchone()
                    if reg:
                        apodo = reg['usuario']

            if user and check_password_hash(user['contrasena_hash'], contrasena):
                session['loggedin'] = True
                session['id'] = user['id']
                session['nombre'] = apodo if apodo else user['nombre']
                session['apodo'] = apodo if apodo else user['nombre']
                return redirect(url_for('inicio_premium'))
            else:
                flash('Correo o contraseña incorrectos.', 'error')
                return render_template('inicio_secion.html', loggedin=False)

        except Exception as e:
            print(f"❌ Error al iniciar sesión: {e}")
            flash('Error interno del servidor.', 'error')
            return render_template('inicio_secion.html', loggedin=False)
        finally:
            conn.close()

    return render_template('inicio_secion.html', success=success_message,
                           loggedin=session.get('loggedin', False), nombre=session.get('nombre'))


@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('inicio'))

# ----------------------------------------------------------------------
# 🔹 RUTAS PRINCIPALES
# ----------------------------------------------------------------------
@app.route('/')
@app.route('/inicio')
def inicio():
    if session.get('loggedin'):
        return redirect(url_for('inicio_premium'))
    return render_template('inicio.html', loggedin=False, nombre=None)


@app.route('/inicio-premium')
def inicio_premium():
    if not session.get('loggedin'):
        flash('Debes iniciar sesión para acceder al contenido Premium.', 'error')
        return redirect(url_for('inicio_secion'))
    return render_template('inicio_premium.html', loggedin=True,
                           nombre=session.get('nombre'), success=request.args.get('success'))


@app.route('/promociones')
def promociones():
    if not session.get('loggedin'):
        flash('Esta sección es exclusiva para miembros.', 'error')
        return redirect(url_for('inicio_secion'))
    return render_template('promociones.html', loggedin=True, nombre=session.get('nombre'))


@app.route('/nuestra-historia')
def historia():
    return render_template('historia.html',
                           loggedin=session.get('loggedin', False),
                           nombre=session.get('nombre'))

# ----------------------------------------------------------------------
# 🔹 RUTAS DE CARTAS
# ----------------------------------------------------------------------
@app.route('/nuestra-carta')
def cartas():
    loggedin = session.get('loggedin', False)
    nombre = session.get('nombre') if loggedin else None
    return render_template('cartas.html', loggedin=loggedin, nombre=nombre)

@app.route('/carta/pollos')
def carta_pollo():
    if not session.get('loggedin'):
        flash('Debes iniciar sesión para ver el menú de Pollos.', 'error')
        return redirect(url_for('inicio_secion'))
    return render_template('carta_pollo.html', loggedin=True, nombre=session.get('nombre'))

@app.route('/carta/pizzas')
def carta_pizza():
    if not session.get('loggedin'):
        flash('Debes iniciar sesión para ver el menú de Pizzas.', 'error')
        return redirect(url_for('inicio_secion'))
    return render_template('carta_pizza.html', loggedin=True, nombre=session.get('nombre'))

@app.route('/carta/pastas')
def carta_pasta():
    if not session.get('loggedin'):
        flash('Debes iniciar sesión para ver el menú de Pastas.', 'error')
        return redirect(url_for('inicio_secion'))
    return render_template('carta_pasta.html', loggedin=True, nombre=session.get('nombre'))

@app.route('/carta/bebidas')
def carta_bebidas():
    if not session.get('loggedin'):
        flash('Debes iniciar sesión para ver el menú de Bebidas.', 'error')
        return redirect(url_for('inicio_secion'))
    return render_template('carta_bebidas.html', loggedin=True, nombre=session.get('nombre'))

@app.route('/carta/entradas')
def carta_entradas():
    if not session.get('loggedin'):
        flash('Debes iniciar sesión para ver el menú de Entradas.', 'error')
        return redirect(url_for('inicio_secion'))
    return render_template('carta_entradas.html', loggedin=True, nombre=session.get('nombre'))

@app.route('/carta/ensaladas')
def carta_ensaladas():
    if not session.get('loggedin'):
        flash('Debes iniciar sesión para ver el menú de Ensaladas.', 'error')
        return redirect(url_for('inicio_secion'))
    return render_template('carta_ensaladas.html', loggedin=True, nombre=session.get('nombre'))

@app.route('/delivery_carta')
def delivery_carta():
    productos = [
        {"id": 1, "nombre": "Inka Cola 500ml", "precio": 4.50, "imagen": "image/bebidas/inka500.png"},
        {"id": 2, "nombre": "Coca Cola 500ml", "precio": 4.50, "imagen": "image/bebidas/coca500.png"}
    ]
    return render_template('delivery_carta.html', productos=productos)

# ----------------------------------------------------------------------
# 🔹 RUTAS DEL CARRITO (AJAX / SESSION)
# ----------------------------------------------------------------------
@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    if not session.get('loggedin'):
        return jsonify({"error": "login_required"}), 403

    data = request.get_json() or request.form
    prod_id = data.get('id')
    name = data.get('name')
    price = float(data.get('price', 0))
    img = data.get('img', '')
    qty = int(data.get('qty', 1))

    ensure_cart()
    cart = session['cart']

    # buscar por id
    found = False
    for it in cart:
        if it.get('id') == prod_id:
            it['qty'] = int(it.get('qty', 1)) + qty
            found = True
            break

    if not found:
        cart.append({"id": prod_id, "name": name, "price": price, "qty": qty, "img": img})

    session['cart'] = cart
    session.modified = True

    return jsonify({"success": True, "cart_count": cart_count(), "total": cart_total()})

@app.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    ensure_cart()
    data = request.get_json() or request.form
    prod_id = data.get('id')

    if not prod_id:
        return jsonify({"error": "missing_id"}), 400

    session['cart'] = [i for i in session['cart'] if i['id'] != prod_id]
    session.modified = True

    return jsonify({
        "success": True,
        "cart_count": cart_count(),
        "total": cart_total()
    })

@app.route('/carrito')
def carrito():
    ensure_cart()
    return render_template(
        'carrito.html',
        cart=session['cart'],
        total=cart_total(),
        cart_count=cart_count(),
        loggedin=session.get('loggedin', False),
        nombre=session.get('nombre')
    )

@app.route('/carrito_pago')
def carrito_pago():
    ensure_cart()
    carrito = session.get('cart', [])
    total = cart_total()

    return render_template("carrito_pago.html",
                           carrito=carrito,
                           total=total,
                           loggedin=session.get("loggedin"),
                           nombre=session.get("nombre"),
                           cart_count=cart_count())

# ----------------------------------------------------------------------
# 🔹 RUTAS DE PAGO / CONFIRMACIÓN
# ----------------------------------------------------------------------
@app.route('/confirmacion_pago', methods=['GET','POST'])
def confirmacion_pago():
    # GET: mostrar QR y datos
    if request.method == 'GET':
        ensure_cart()
        if not session.get('cart'):
            flash('Tu carrito está vacío.', 'error')
            return redirect(url_for('cartas'))
        # mostramos QR (ya tienes imagen) y total
        return render_template('confirmacion_pago.html', total=cart_total(), cart=session['cart'], cart_count=cart_count(), loggedin=session.get('loggedin', False))

    # POST: recibir confirmación simulada desde el front (cuando pago real llegue)
    # Esperamos {"method":"yape"|"tarjeta", "confirm": true, "direccion": "..."}
    data = request.get_json() or request.form
    confirmed = data.get('confirm') in ['1','true', True, 'true']
    payment_method = data.get('method', 'yape')
    direccion = data.get('direccion', '')

    if not confirmed:
        return jsonify({"success": False, "message": "Pago no confirmado"}), 400

    # Guardar pedido en DB
    conn = get_db_connection()
    order_id = None
    try:
        with conn.cursor() as cursor:
            detalle = json.dumps(session.get('cart', []), ensure_ascii=False)
            sql = "INSERT INTO Pedidos (nombre_cliente, telefono, direccion, detalle_pedido) VALUES (%s, %s, %s, %s)"
            # si el usuario está logueado usar su nombre/phone si tienes (por ahora solo nombre)
            nombre_cliente = session.get('nombre') or data.get('nombre') or 'Cliente Delivery'
            telefono = data.get('telefono', '')
            cursor.execute(sql, (nombre_cliente, telefono, direccion, detalle))
            conn.commit()
            order_id = cursor.lastrowid
    except Exception as e:
        print("❌ Error al guardar pedido en confirmacion:", e)
        conn.rollback()
        return jsonify({"success": False, "message": "Error al guardar pedido"}), 500
    finally:
        conn.close()

    # vaciar carrito
    session['cart'] = []
    session.modified = True

    return jsonify({"success": True, "order_id": order_id})

# Seguimiento
@app.route('/seguimiento')
def seguimiento():
    # mostrar página de seguimiento. Puede recibir ?order_id=xx
    order_id = request.args.get('order_id')
    # podrías consultar estado en DB; por ahora devolvemos datos simulados
    estado = "En preparación" if order_id else "Pedido no encontrado"
    return render_template('seguimiento.html', order_id=order_id, estado=estado, cart_count=cart_count(), loggedin=session.get('loggedin', False))

# ----------------------------------------------------------------------
# 🔹 RUTA DELIVERY
# ----------------------------------------------------------------------
@app.route('/delivery', methods=['GET', 'POST'])
def delivery():
    loggedin = session.get('loggedin', False)
    nombre = session.get('nombre') if loggedin else None

    if request.method == 'POST':
        nombre_cliente = request.form['nombre']
        telefono = request.form['telefono']
        direccion = request.form['direccion']
        pedido = request.form['pedido']

        conn = get_db_connection()
        if conn is None:
            flash('Error al conectar con la base de datos.', 'error')
            return render_template('delivery.html', loggedin=loggedin, nombre=nombre)

        try:
            with conn.cursor() as cursor:
                sql = """
                INSERT INTO Pedidos (nombre_cliente, telefono, direccion, detalle_pedido)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (nombre_cliente, telefono, direccion, pedido))
                conn.commit()
                flash('✅ Pedido enviado con éxito. Te llamaremos pronto.', 'success')
        except Exception as e:
            print(f"❌ Error al guardar pedido: {e}")
            flash('❌ Error interno al procesar tu pedido.', 'error')
        finally:
            conn.close()

    return render_template('delivery.html', loggedin=loggedin, nombre=nombre)
# ----------------------------------------------------------------------
# 🔹 RUTA DE RESERVAS
# ----------------------------------------------------------------------
@app.route('/reserva', methods=['GET', 'POST'])
def reserva():
    loggedin = session.get('loggedin', False)
    nombre_usuario = session.get('nombre')
    message = None

    if request.method == 'POST':
        # Datos del formulario
        nombre = request.form.get('nombre')
        celular = request.form.get('celular')
        fecha = request.form.get('fecha')
        hora = request.form.get('hora')
        cantidad_personas = request.form.get('cantidad_personas')
        mensaje = request.form.get('mensaje')
        usuario_id = session.get('id', None)  # Si está logueado, sino None

        # Conectar a MySQL
        conn = get_db_connection()
        if conn is None:
            message = 'Error de conexión a la base de datos. Inténtalo más tarde.'
        else:
            try:
                with conn.cursor() as cursor:
                    sql = """
                    INSERT INTO Reservas (fecha, hora, nombre, celular, cantidad_personas, mensaje, usuario_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (fecha, hora, nombre, celular, cantidad_personas, mensaje, usuario_id))
                    conn.commit()  # Se guarda en MySQL

                    # 🔹 Redirigir a la confirmación usando GET con parámetros
                    return redirect(url_for('reserva_confirmada', 
                                            nombre=nombre,
                                            fecha=fecha,
                                            hora=hora,
                                            cantidad_personas=cantidad_personas,
                                            mensaje=mensaje))
            except Exception as e:
                print(f"❌ Error al registrar la reserva: {e}")
                message = '❌ Error interno al procesar la reserva.'
            finally:
                conn.close()

    # GET o si hubo error
    return render_template('reservadf.html',
                           message=message,
                           loggedin=loggedin,
                           nombre=nombre_usuario)


# ----------------------------------------------------------------------
# 🔹 RUTA RESERVA CONFIRMADA
# ----------------------------------------------------------------------
@app.route('/reserva_confirmada')
def reserva_confirmada():
    # Tomar datos desde URL (GET)
    nombre = request.args.get('nombre')
    fecha = request.args.get('fecha')
    hora = request.args.get('hora')
    cantidad_personas = request.args.get('cantidad_personas')
    mensaje = request.args.get('mensaje')

    return render_template('reserva_confirmada.html',
                           nombre=nombre,
                           fecha=fecha,
                           hora=hora,
                           cantidad_personas=cantidad_personas,
                           mensaje=mensaje)

# ----------------------------------------------------------------------
# 🔹 FORMULARIO DE SUSCRIPCIÓN
# ----------------------------------------------------------------------
@app.route('/formulario', methods=['GET', 'POST'])
def formulario():
    if request.method == 'POST':
        conn = get_db_connection()
        if conn is None:
            return "Error de conexión a la base de datos."

        try:
            nombre = request.form['nombre']
            apellidos = request.form['apellidos']
            dni = request.form['dni']
            correo = request.form['correo']
            telefono = request.form['telefono']

            with conn.cursor() as cursor:
                sql = """
                INSERT INTO Suscriptores (nombre, apellidos, dni, correo, telefono)
                VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (nombre, apellidos, dni, correo, telefono))
                conn.commit()

            return redirect(url_for('registro', message='¡Suscripción exitosa! Crea tu cuenta para acceder a la experiencia completa.'))

        except Exception as e:
            print("❌ Error al guardar los datos:", e)
            return "Error al guardar en la base de datos."
        finally:
            conn.close()

    return render_template('formulario.html',
                           loggedin=session.get('loggedin', False),
                           nombre=session.get('nombre'))

# ----------------------------------------------------------------------
# 🔹 TEST DE CONEXIÓN A BD
# ----------------------------------------------------------------------
@app.route('/test-db')
def test_db():
    conn = get_db_connection()
    if conn is None:
        return "❌ Error al conectar con la base: Revisa los logs."
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM Usuarios;")
            resultado = cursor.fetchone()
        return f"✅ Conexión exitosa. Usuarios registrados: {resultado['total']}"
    except Exception as e:
        return f"❌ Error al consultar la base: {e}"
    finally:
        conn.close()


    session.modified = True

    return jsonify({
        "ok": True,
        "cart_count": len(session["cart"])
    })


@app.route("/sincronizar-carrito", methods=["POST"])
def sincronizar_carrito():
    data = request.get_json()
    session["cart"] = data.get("carrito", [])
    session.modified = True
    return "ok", 200

@app.route("/cart_remove", methods=["POST"])
def cart_remove():
    data = request.get_json()
    product_name = data.get("nombre")

    if "cart" in session:
        session["cart"] = [p for p in session["cart"] if p["nombre"] != product_name]
        session.modified = True

    return jsonify({"success": True})


@app.route("/fix-cart")
def fix_cart():
    session["cart"] = []
    session.modified = True
    return "Carrito limpiado"



# ----------------------------------------------------------------------
# 🚀 EJECUTAR SERVIDOR
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)



