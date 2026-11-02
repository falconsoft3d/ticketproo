/* Modo claro / oscuro.
   Se carga en <head> (sin defer) para aplicar el tema antes de pintar y evitar el destello.
   Preferencia guardada en localStorage ('ap-theme'); si no hay, sigue al sistema. */
(function () {
    var KEY = 'ap-theme';
    var root = document.documentElement;
    var media = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;

    function stored() {
        try { return localStorage.getItem(KEY); } catch (e) { return null; }
    }

    function apply(theme) {
        root.setAttribute('data-theme', theme);
        root.setAttribute('data-bs-theme', theme);
    }

    function current() {
        return stored() || (media && media.matches ? 'dark' : 'light');
    }

    apply(current());

    // Si el usuario no eligió nada, seguir los cambios del sistema
    if (media && media.addEventListener) {
        media.addEventListener('change', function () {
            if (!stored()) apply(current());
        });
    }

    // Iconos laterales del panel: ocultos salvo que el usuario los active
    var SIDE_KEY = 'ap-side-icons';
    try { if (localStorage.getItem(SIDE_KEY) === 'on') root.setAttribute('data-side-icons', 'on'); } catch (e) {}

    window.apToggleSideIcons = function () {
        var on = root.getAttribute('data-side-icons') !== 'on';
        if (on) root.setAttribute('data-side-icons', 'on'); else root.removeAttribute('data-side-icons');
        try { localStorage.setItem(SIDE_KEY, on ? 'on' : 'off'); } catch (e) {}
    };

    window.apToggleTheme = function () {
        var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        try { localStorage.setItem(KEY, next); } catch (e) {}
        apply(next);
    };
})();
