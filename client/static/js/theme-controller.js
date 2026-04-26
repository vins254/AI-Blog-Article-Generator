/**
 * ContentFlow — Professional Theme Controller
 * Ensures instant theme 'reflection' across the entire application.
 */
(function() {
    // 1. Immediate Execution: Apply theme before the browser paints the body.
    // This prevents the "white flash" when loading dark mode.
    const savedTheme = localStorage.getItem('cf_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);

    const applyTheme = (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('cf_theme', theme);
        
        const toggle = document.getElementById('themeToggle');
        if (toggle) {
            // Swap icon: Moon for Light mode (implies switching to Dark), Sun for Dark mode.
            toggle.innerHTML = theme === 'light' 
                ? '<i data-lucide="moon"></i>' 
                : '<i data-lucide="sun"></i>';
            
            // Re-initialize Lucide icons
            if (window.lucide) {
                window.lucide.createIcons();
            }
        }
    };

    // 2. DOM Ready Logic
    window.addEventListener('DOMContentLoaded', () => {
        console.log("ContentFlow: Theme Engine Initialized. Mode:", savedTheme);
        
        const toggle = document.getElementById('themeToggle');
        if (toggle) {
            // Setup initial button state
            applyTheme(savedTheme);
            
            toggle.addEventListener('click', () => {
                const current = document.documentElement.getAttribute('data-theme');
                const next = current === 'light' ? 'dark' : 'light';
                console.log("ContentFlow: Toggling Theme to", next);
                applyTheme(next);
            });
        }
    });
})();
