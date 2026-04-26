/**
 * ContentFlow — Robust Theme Controller
 * Manages Light/Dark mode transitions with Lucide icon swapping.
 */
(function() {
    const applyTheme = (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('cf_theme', theme);
        
        const toggle = document.getElementById('themeToggle');
        if (toggle) {
            // Swap the icon based on the current theme
            toggle.innerHTML = theme === 'light' 
                ? '<i data-lucide="moon"></i>' 
                : '<i data-lucide="sun"></i>';
            
            // Re-render Lucide icons
            if (window.lucide) {
                window.lucide.createIcons();
            }
        }
    };

    const savedTheme = localStorage.getItem('cf_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);

    window.addEventListener('DOMContentLoaded', () => {
        const toggle = document.getElementById('themeToggle');
        if (toggle) {
            // Initial icon setup
            applyTheme(savedTheme);
            
            toggle.addEventListener('click', () => {
                const current = document.documentElement.getAttribute('data-theme');
                applyTheme(current === 'light' ? 'dark' : 'light');
            });
        }
    });
})();
