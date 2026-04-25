/**
 * ContentFlow — Engineered Theme Controller
 * Manages the transition between 'The Studio' (Dark) and 'The Editorial' (Light).
 */
(function() {
    const applyTheme = (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('cf_theme', theme);
    };

    const savedTheme = localStorage.getItem('cf_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);

    window.addEventListener('DOMContentLoaded', () => {
        const toggle = document.getElementById('themeToggle');
        if (toggle) {
            toggle.addEventListener('click', () => {
                const current = document.documentElement.getAttribute('data-theme');
                applyTheme(current === 'light' ? 'dark' : 'light');
            });
        }
        
        // Initial Lucide check
        if (window.lucide) {
            window.lucide.createIcons();
        }
    });
})();
