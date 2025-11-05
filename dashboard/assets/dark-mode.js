/**
 * Dark Mode Toggle Handler
 * Handles dark mode state with localStorage persistence
 */

(function() {
    'use strict';
    
    // Check for saved user preference or default to light mode
    const savedTheme = localStorage.getItem('theme') || 'light';
    
    // Apply saved theme on page load
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
    }
    
    // Wait for DOM to be ready
    function initDarkModeToggle() {
        const toggleButton = document.getElementById('dark-mode-toggle');
        
        if (!toggleButton) {
            // Button not found, try again in a moment
            setTimeout(initDarkModeToggle, 100);
            return;
        }
        
        // Add click handler
        toggleButton.addEventListener('click', function(e) {
            e.preventDefault();
            toggleDarkMode();
        });
        
        console.log('Dark mode toggle initialized');
    }
    
    // Toggle dark mode
    function toggleDarkMode() {
        const isDark = document.body.classList.toggle('dark-mode');
        
        // Save preference
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        
        console.log('Dark mode:', isDark ? 'enabled' : 'disabled');
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDarkModeToggle);
    } else {
        initDarkModeToggle();
    }
    
    // Also try to initialize after Dash finishes rendering
    setTimeout(initDarkModeToggle, 1000);
    setTimeout(initDarkModeToggle, 2000);
})();
