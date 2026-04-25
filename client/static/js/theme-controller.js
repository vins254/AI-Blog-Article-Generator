/**
 * ContentFlow — Shared Theme Controller
 * Manages Light/Dark mode state and persistence.
 */
(function() {
    const applyTheme = (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('cf_theme', theme);
        const toggle = document.getElementById('themeToggle');
        if (toggle) {
            toggle.textContent = theme === 'light' ? 'Dark Mode' : 'Light Mode';
        }
    };

    const savedTheme = localStorage.getItem('cf_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);

    window.addEventListener('DOMContentLoaded', () => {
        const toggle = document.getElementById('themeToggle');
        if (toggle) {
            toggle.textContent = savedTheme === 'light' ? 'Dark Mode' : 'Light Mode';
            toggle.addEventListener('click', () => {
                const current = document.documentElement.getAttribute('data-theme');
                applyTheme(current === 'light' ? 'dark' : 'light');
            });
        }
    });
})();
