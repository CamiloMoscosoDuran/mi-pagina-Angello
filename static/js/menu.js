// static/js/menu.js
// Lógica para convertir el bloque de acciones del nav en un menú móvil

document.addEventListener('DOMContentLoaded', function() {
    function initResponsiveNav() {
        const NAV_BREAKPOINT = 768; // px
        const navs = document.querySelectorAll('nav');

        navs.forEach(nav => {
            // tratar de encontrar el bloque de acciones (último div dentro del nav)
            const actions = nav.querySelector('div:last-of-type');
            if (!actions) return;

            const toggle = document.createElement('button');
            toggle.setAttribute('aria-expanded', 'false');
            toggle.setAttribute('aria-label', 'Abrir menu');
            // clases de utilidad (Tailwind no siempre necesarias aquí)
            toggle.className = 'nav-toggle';
            // estilos inline garantizan visibilidad inicial y posición
            Object.assign(toggle.style, {
                background: 'transparent',
                border: '2px solid rgba(255,255,255,0.08)',
                padding: '6px 8px',
                display: 'none',
                position: 'absolute',
                top: '8px',
                right: '12px',
                zIndex: 9999,
                color: 'white',
                cursor: 'pointer'
            });
            toggle.innerHTML = '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 6h14M3 10h14M3 14h14" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';

            // asegurar que el nav tenga position:relative para que toggle absoluto funcione
            if (getComputedStyle(nav).position === 'static') {
                nav.style.position = 'relative';
            }

            // insertar justo antes del bloque de acciones
            nav.insertBefore(toggle, actions);

            // crear contenedor del menu movil (donde moveremos nodos reales)
            const menuContainer = document.createElement('div');
            menuContainer.className = 'nav-mobile-menu';
            Object.assign(menuContainer.style, {
                display: 'none',
                position: 'absolute',
                top: (nav.offsetHeight + 8) + 'px',
                right: '12px',
                background: 'rgba(0,0,0,0.9)',
                padding: '8px',
                borderRadius: '8px',
                zIndex: 9998,
                minWidth: '140px'
            });

            // insert menuContainer in nav
            nav.appendChild(menuContainer);

            // candidate elements to move: children of actions (right block) then last children of left block
            const leftBlock = nav.querySelector('div:first-of-type');
            const rightBlock = actions;

            // map to remember original parent and nextSibling for restoration
            const originalPos = new Map();

            function getMoveCandidates() {
                const rightChildren = Array.from(rightBlock.children).filter(el => el.tagName === 'A' || el.tagName === 'BUTTON');
                const leftChildren = leftBlock ? Array.from(leftBlock.children).filter(el => el.tagName === 'A' || el.tagName === 'BUTTON') : [];
                // order: last of rightChildren first, then last of leftChildren
                return rightChildren.slice().reverse().concat(leftChildren.slice().reverse());
            }

            function measureVisibleWidth() {
                // measure sum width of logo + visible nav items (excluding those already moved to menuContainer)
                const logo = nav.querySelector('a img') ? nav.querySelector('a img').parentElement : null;
                let w = 0;
                if (logo) w += logo.getBoundingClientRect().width + 12;
                // include children in left and right blocks that are still in nav
                const items = Array.from(nav.querySelectorAll('a, button')).filter(el => nav.contains(el) && !menuContainer.contains(el));
                items.forEach(it => {
                    // skip the logo anchor
                    if (it.querySelector && it.querySelector('img')) return;
                    const r = it.getBoundingClientRect();
                    w += r.width + 12; // small gap
                });
                return w;
            }

            function moveToMenu(el) {
                if (!originalPos.has(el)) {
                    originalPos.set(el, { parent: el.parentElement, nextSibling: el.nextSibling });
                }
                menuContainer.appendChild(el);
                // ensure menu item styling
                el.style.display = 'block';
                el.style.padding = '6px 8px';
                el.style.color = 'white';
                el.style.textDecoration = 'none';
            }

            function moveBack(el) {
                const info = originalPos.get(el);
                if (!info) return;
                if (info.nextSibling && info.parent.contains(info.nextSibling)) {
                    info.parent.insertBefore(el, info.nextSibling);
                } else {
                    info.parent.appendChild(el);
                }
                // remove inline menu styles we added
                el.style.display = '';
                el.style.padding = '';
                el.style.color = '';
                el.style.textDecoration = '';
                originalPos.delete(el);
            }

            // En pantallas pequeñas mostramos toggle y transferimos enlaces según ancho
            function setMobileState(isMobile) {
                const NAV_RESERVE = 24; // padding reserve
                if (isMobile) {
                    toggle.style.display = 'block';
                    // keep menu hidden by default; toggle will open it
                    menuContainer.style.display = 'none';
                    toggle.setAttribute('aria-expanded', 'false');
                    // compute available width for nav items
                    const navWidth = nav.clientWidth;
                    const logo = nav.querySelector('a img') ? nav.querySelector('a img').parentElement : null;
                    const logoW = logo ? logo.getBoundingClientRect().width + 12 : 0;
                    const available = navWidth - logoW - NAV_RESERVE - 60; // 60 for toggle and breathing room

                    // move items while visible width exceeds available
                    let visible = measureVisibleWidth();
                    const candidates = getMoveCandidates();
                    let i = 0;
                    while (visible > available && i < candidates.length) {
                        const el = candidates[i];
                        // if element is still in nav (not yet moved), move it
                        if (nav.contains(el) && !menuContainer.contains(el)) {
                            visible -= (el.getBoundingClientRect().width + 12);
                            moveToMenu(el);
                        }
                        i++;
                    }

                    // try to move back items from menu to nav if space allows (in order they were moved)
                    let movedBack = true;
                    while (movedBack) {
                        movedBack = false;
                        const nextToRestore = menuContainer.firstElementChild;
                        if (!nextToRestore) break;
                        const wnext = nextToRestore.getBoundingClientRect().width + 12;
                        visible = measureVisibleWidth();
                        if (visible + wnext <= available) {
                            moveBack(nextToRestore);
                            movedBack = true;
                        }
                    }
                } else {
                    // restaurar todo: mover todos los hijos del menuContainer a sus posiciones originales
                    Array.from(menuContainer.children).forEach(ch => moveBack(ch));
                    menuContainer.style.display = 'none';
                    toggle.style.display = 'none';
                    toggle.setAttribute('aria-expanded', 'false');
                }
                // ajustar top del menuContainer por si cambió el nav height
                menuContainer.style.top = (nav.offsetHeight + 8) + 'px';
            }

            toggle.addEventListener('click', function() {
                const opened = toggle.getAttribute('aria-expanded') === 'true';
                if (opened) {
                    // cerrar menu
                    menuContainer.style.display = 'none';
                    toggle.setAttribute('aria-expanded', 'false');
                } else {
                    // abrir menu
                    menuContainer.style.display = 'block';
                    toggle.setAttribute('aria-expanded', 'true');
                }
            });

            function onResize() {
                setMobileState(window.innerWidth < NAV_BREAKPOINT);
                // ajustar top del menuContainer por si cambió el nav height
                menuContainer.style.top = (nav.offsetHeight + 8) + 'px';
            }

            window.addEventListener('resize', onResize);
            onResize();
        });
    }

    initResponsiveNav();
});

