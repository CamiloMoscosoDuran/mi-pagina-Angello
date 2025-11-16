document.addEventListener('DOMContentLoaded', function() {
    const toggleBtn = document.getElementById('chatbot-toggle');
    const chatbotBox = document.getElementById('chatbot-box');
    const closeBtn = document.getElementById('chatbot-close');
    const chatForm = document.getElementById('chatbot-form');
    const chatMessages = document.getElementById('chatbot-messages');
    
    // Elementos del chatbot
    const stepName = document.getElementById('chatbot-step-name');
    const stepMessage = document.getElementById('chatbot-step-message');
    const inputName = document.getElementById('chatbot-input-name');
    const inputMsg = document.getElementById('chatbot-input');
    const nextBtn = document.getElementById('chatbot-next');

    // **Nombre del usuario registrado**
    let userName = "Usuario"; // Se actualizará cuando el usuario ingrese su nombre
    let initialGreetingSent = false; 
    
    // LocalStorage para persistir el historial del chat
    const CHAT_STORAGE_KEY = 'chatbot_messages';
    const GREETING_STORAGE_KEY = 'chatbot_initial_greeting';
    const USERNAME_STORAGE_KEY = 'chatbot_username'; 

    // Función para enviar un mensaje al chat
    function appendMessage(text, cls) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message ' + cls;
        msgDiv.textContent = text;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Guardar mensaje en localStorage
        saveMessageToStorage(text, cls);
    }

    // Función para guardar mensajes en localStorage
    function saveMessageToStorage(text, cls) {
        try {
            const messages = getStoredMessages();
            const timestamp = new Date().toISOString();
            messages.push({
                text: text,
                class: cls,
                timestamp: timestamp
            });
            
            // Limitar el historial a los últimos 50 mensajes
            if (messages.length > 50) {
                messages.splice(0, messages.length - 50);
            }
            
            localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messages));
        } catch (error) {
            console.warn('No se pudo guardar el mensaje en localStorage:', error);
        }
    }

    // Función para obtener mensajes guardados
    function getStoredMessages() {
        try {
            const stored = localStorage.getItem(CHAT_STORAGE_KEY);
            return stored ? JSON.parse(stored) : [];
        } catch (error) {
            console.warn('No se pudieron cargar los mensajes guardados:', error);
            return [];
        }
    }

    // Función para cargar historial del chat
    function loadChatHistory() {
        const messages = getStoredMessages();
        const today = new Date().toDateString();
        
        // Filtrar mensajes del día actual (opcional)
        const todayMessages = messages.filter(msg => {
            const msgDate = new Date(msg.timestamp).toDateString();
            return msgDate === today;
        });
        
        // Si hay mensajes del día, cargarlos
        if (todayMessages.length > 0) {
            chatMessages.innerHTML = ''; // Limpiar mensajes existentes
            todayMessages.forEach(msg => {
                const msgDiv = document.createElement('div');
                msgDiv.className = 'message ' + msg.class;
                msgDiv.textContent = msg.text;
                chatMessages.appendChild(msgDiv);
            });
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    // Función para limpiar historial del chat
    function clearChatHistory() {
        try {
            localStorage.removeItem(CHAT_STORAGE_KEY);
            chatMessages.innerHTML = '';
            // Enviar saludo inicial de nuevo
            appendMessage(`¡Hola ${userName}! ¿Cómo te podemos ayudar?`, 'bot-message');
        } catch (error) {
            console.warn('No se pudo limpiar el historial:', error);
        }
    }

    // Función para guardar/cargar el nombre del usuario
    function saveUserName(name) {
        try {
            localStorage.setItem(USERNAME_STORAGE_KEY, name);
        } catch (error) {
            console.warn('No se pudo guardar el nombre del usuario:', error);
        }
    }

    function loadUserName() {
        try {
            const savedName = localStorage.getItem(USERNAME_STORAGE_KEY);
            if (savedName) {
                userName = savedName;
            }
        } catch (error) {
            console.warn('No se pudo cargar el nombre del usuario:', error);
        }
    }

    // Función para verificar si ya se envió el saludo inicial
    function checkInitialGreeting() {
        try {
            const greetingSent = localStorage.getItem(GREETING_STORAGE_KEY);
            const today = new Date().toDateString();
            const savedDate = localStorage.getItem(GREETING_STORAGE_KEY + '_date');
            
            // Si el saludo se envió hoy, marcarlo como enviado
            if (greetingSent === 'true' && savedDate === today) {
                initialGreetingSent = true;
            } else {
                // Si es un nuevo día, resetear el saludo
                initialGreetingSent = false;
                localStorage.setItem(GREETING_STORAGE_KEY, 'false');
            }
        } catch (error) {
            console.warn('No se pudo verificar el estado del saludo inicial:', error);
        }
    }

    function markGreetingAsSent() {
        try {
            const today = new Date().toDateString();
            localStorage.setItem(GREETING_STORAGE_KEY, 'true');
            localStorage.setItem(GREETING_STORAGE_KEY + '_date', today);
            initialGreetingSent = true;
        } catch (error) {
            console.warn('No se pudo marcar el saludo como enviado:', error);
        }
    }

    // ===================================================================

    function botReply(message) {
        const msg = message.toLowerCase(); // Convertir a minúsculas para facilitar la búsqueda

        // Comandos especiales del sistema
        if (/limpiar chat|nueva conversacion|borrar historial/i.test(msg)) {
            clearChatHistory();
            return "✅ Historial del chat limpiado. ¡Empecemos de nuevo!";
        } else if (/exportar chat|descargar historial/i.test(msg)) {
            window.exportChatHistory();
            return "📁 Historial exportado a la consola. Presiona F12 para verlo.";
        }

        // Respuestas de saludo y despedida
        else if (/hola|buenas/i.test(msg)) {
            return `¡Hola ${userName}! Bienvenido a El Restaurante Angello . ¿En qué puedo ayudarte?`;
        } else if (/adiós|bye|chau/i.test(msg)) {
            return "¡Hasta luego! Esperamos verte pronto en el Restaurante Angello. 😊";
        } 
        
        // ** 1. MENÚ / COMIDA / PLATOS **
        else if (/menú|carta|platos|comida|que venden|que ofrecen/i.test(msg)) {
            return "Nuestro menú es variado. Tenemos: Pollo a la Leña 🍗 , Pastas en salsa al alfredo, bolognesa y al pesto 🍴 , Pizzas 🍕. ¿Te interesa alguno en particular?";
        } 
        // ** 2. HORARIOS **
        else if (/horario|abren|cierran|a que hora/i.test(msg)) {
            return "Abrimos de Martes a Domingo de 3:00 PM a 11:00 PM."; 
        } 
        // ** 3. RESERVAS **
        else if (/reservar|reserva|mesa/i.test(msg)) {
            return "¡Claro! Puedes reservar una mesa llamando al (01) 555-1234 o directamente en nuestra web (link-de-reservas.com). ¿Para cuántas personas sería?";
        }
        // ** 4. UBICACIÓN / DIRECCIÓN **
        else if (/donde se ubican|dirección|como llego/i.test(msg)) {
            return "¡Nos ubicamos en Miguel Grau, San Vicente de Cañete 15701! Estamos justo al lado del Parque Principal.";
        }
        // ** 5. METODOS DE PAGO **
        else if (/pagar|pago|tarjeta|aceptan/i.test(msg)) {
            return "Aceptamos efectivo, tarjetas de crédito/débito (Visa, Mastercard) y pagos por Yape/Plin.";
        }
        // ** 6. ALERGIAS / DIETAS (NUEVA RESPUESTA) **
        else if (/alergia|gluten|vegetariano|vegano|dieta/i.test(msg)) {
            return "Por el momento, no tenemos opciones estrictamente vegetarianas o veganas en nuestro menú. Por favor, consulta con nuestro personal al momento de ordenar.";
        }
        // ** Fallback (Respuesta por defecto) **
        else {
            return "Gracias por tu mensaje. No entendí tu consulta. ¿Podrías preguntar sobre el menú, horarios, reservas o ubicación? ¡Con gusto te ayudo!";
        }
    }
    // ====================================================================
    
    // Inicialización del chatbot
    function initializeChatbot() {
        // Cargar nombre de usuario guardado
        loadUserName();
        
        // Verificar estado del saludo inicial
        checkInitialGreeting();
        
        // Cargar historial de chat si existe
        loadChatHistory();
    }
    
    // Llamar a la inicialización
    initializeChatbot();

    // Lógica para mostrar/ocultar chatbot
    toggleBtn.addEventListener('click', () => {
        chatbotBox.classList.toggle('hidden');
        
        if (!chatbotBox.classList.contains('hidden')) {
            // Verificar si ya hay historial cargado o si ya se envió el saludo
            const existingMessages = chatMessages.children.length;
            
            if (existingMessages === 0 && !initialGreetingSent) {
                // Mostrar el paso de nombre al abrir el chatbot por primera vez
                stepName.classList.remove('hidden');
                stepMessage.classList.add('hidden');
                inputName.focus();
            } else {
                // Si ya hay historial o el saludo fue enviado, ir directo a mensajes
                stepName.classList.add('hidden');
                stepMessage.classList.remove('hidden');
                if (inputMsg) {
                    inputMsg.focus();
                }
            }
        }
    });
    
    closeBtn.addEventListener('click', () => {
        chatbotBox.classList.add('hidden');
    });

    // Manejar el paso del nombre
    nextBtn.addEventListener('click', (e) => {
        e.preventDefault();
        const name = inputName.value.trim();
        if (!name) {
            alert('Por favor, ingresa tu nombre');
            return;
        }
        
        userName = name;
        saveUserName(userName); // Guardar nombre en localStorage
        stepName.classList.add('hidden');
        stepMessage.classList.remove('hidden');
        
        // Limpiar mensajes previos y enviar saludo personalizado
        chatMessages.innerHTML = '';
        appendMessage(`¡Hola ${userName}! Bienvenido a El Restaurante Angello. ¿En qué puedo ayudarte?`, 'bot-message');
        markGreetingAsSent(); // Marcar saludo como enviado
        inputMsg.focus();
    });

    // Manejar envío de mensajes
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const text = inputMsg.value.trim();
        if (!text) return;

        appendMessage(text, 'user-message');
        setTimeout(() => {
            appendMessage(botReply(text), 'bot-message');
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 600);
        inputMsg.value = '';
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
    
    // Función global para limpiar el historial del chat (puede ser llamada desde consola)
    window.clearChatHistory = clearChatHistory;
    
    // Función para exportar historial del chat (opcional)
    window.exportChatHistory = function() {
        const messages = getStoredMessages();
        const exportData = {
            userName: userName,
            messages: messages,
            exportDate: new Date().toISOString()
        };
        console.log('Historial del chat:', exportData);
        return exportData;
    };
});
