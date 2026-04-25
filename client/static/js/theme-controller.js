/**
 * ContentFlow — Modern Theme Controller
 * Manages Pure Black/White theme state with Lucide icon integration.
 */
(function() {
    const applyTheme = (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('cf_theme', theme);
        
        const toggle = document.getElementById('themeToggle');
        if (toggle) {
            // Update the icon based on the new theme
            toggle.innerHTML = theme === 'light' 
                ? '<i data-lucide="moon"></i>' 
                : '<i data-lucide="sun"></i>';
            
            // Re-initialize Lucide to render the new icon
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
            // Initial render
            applyTheme(savedTheme);
            
            toggle.addEventListener('click', () => {
                const current = document.documentElement.getAttribute('data-theme');
                applyTheme(current === 'light' ? 'dark' : 'light');
            });
        }
    });
})();
