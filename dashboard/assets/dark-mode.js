/**
 * Dark Mode Toggle Handler with Dynamic Inline Style Replacement
 * Handles dark mode state with localStorage persistence and inline style color swapping
 */

(function() {
    'use strict';
    
    // Color mappings for dark mode
    const colorMappings = {
        // Background colors
        '#ffffff': '#1A1F26',
        '#fafafa': '#0F1419',
        '#f3f4f6': '#0F1419',
        '#f9fafb': '#1A1F26',
        '#eff6ff': '#1e3a5f',
        'rgb(255, 255, 255)': 'rgb(26, 31, 38)',
        'rgb(250, 250, 250)': 'rgb(15, 20, 25)',
        'rgb(243, 244, 246)': 'rgb(15, 20, 25)',
        
        // Text colors
        '#0f172a': '#F7FAFC',
        '#64748b': '#A0AEC0',
        '#94a3b8': '#A0AEC0',
        '#6b7280': '#A0AEC0',
        '#111827': '#F7FAFC',
        'rgb(15, 23, 42)': 'rgb(247, 250, 252)',
        'rgb(100, 116, 139)': 'rgb(160, 174, 192)',
        
        // Keep functional colors (success, error, etc.)
        // These should remain the same or be slightly adjusted
        '#3b82f6': '#42A5F5',  // Blue - slightly brighter
        '#10b981': '#10b981',  // Green - keep same
        '#ef4444': '#ef4444',  // Red - keep same
        '#dc2626': '#ef4444',  // Red - keep same
        '#059669': '#10b981',  // Green - keep same
        
        // Background for colored elements
        '#fee2e2': '#3d1f1f',  // Light red bg -> dark red bg
        '#d1fae5': '#1f3d2f',  // Light green bg -> dark green bg
    };
    
    // Reverse mappings for light mode
    const reverseMappings = {};
    for (const [light, dark] of Object.entries(colorMappings)) {
        reverseMappings[dark] = light;
    }
    
    // Check for saved user preference or default to light mode
    const savedTheme = localStorage.getItem('theme') || 'light';
    
    console.log('[Dark Mode] Initializing with theme:', savedTheme);
    
    // Apply saved theme on page load
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        setTimeout(() => applyDarkModeColors(), 100);
    }
    
    // Function to swap colors in inline styles
    function swapInlineColors(isDark) {
        const mappings = isDark ? colorMappings : reverseMappings;
        const elements = document.querySelectorAll('[style]');
        
        elements.forEach(element => {
            const style = element.style;
            
            // Swap background colors
            if (style.backgroundColor) {
                const currentColor = style.backgroundColor;
                const rgbMatch = currentColor.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
                
                if (rgbMatch) {
                    const hexColor = rgbToHex(parseInt(rgbMatch[1]), parseInt(rgbMatch[2]), parseInt(rgbMatch[3]));
                    if (mappings[hexColor]) {
                        style.backgroundColor = mappings[hexColor];
                    }
                } else if (mappings[currentColor]) {
                    style.backgroundColor = mappings[currentColor];
                }
            }
            
            // Swap background shorthand
            if (style.background && style.background.startsWith('#')) {
                const currentColor = style.background;
                if (mappings[currentColor]) {
                    style.background = mappings[currentColor];
                }
            }
            
            // Swap text colors
            if (style.color) {
                const currentColor = style.color;
                const rgbMatch = currentColor.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
                
                if (rgbMatch) {
                    const hexColor = rgbToHex(parseInt(rgbMatch[1]), parseInt(rgbMatch[2]), parseInt(rgbMatch[3]));
                    if (mappings[hexColor]) {
                        style.color = mappings[hexColor];
                    }
                } else if (mappings[currentColor]) {
                    style.color = mappings[currentColor];
                }
            }
            
            // Swap border colors
            if (style.borderColor) {
                const currentColor = style.borderColor;
                if (mappings[currentColor]) {
                    style.borderColor = mappings[currentColor];
                }
            }
        });
        
        console.log('[Dark Mode] Swapped colors in', elements.length, 'elements');
    }
    
    // Helper function to convert RGB to hex
    function rgbToHex(r, g, b) {
        return '#' + [r, g, b].map(x => {
            const hex = x.toString(16);
            return hex.length === 1 ? '0' + hex : hex;
        }).join('');
    }
    
    // Apply dark mode colors
    function applyDarkModeColors() {
        console.log('[Dark Mode] Applying dark mode colors');
        swapInlineColors(true);
    }
    
    // Apply light mode colors
    function applyLightModeColors() {
        console.log('[Dark Mode] Applying light mode colors');
        swapInlineColors(false);
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
            e.stopPropagation();
            toggleDarkMode();
        });
        
        console.log('[Dark Mode] Toggle button initialized');
    }
    
    // Toggle dark mode
    function toggleDarkMode() {
        const wasDark = document.body.classList.contains('dark-mode');
        const isDark = !wasDark;
        
        // Toggle class
        document.body.classList.toggle('dark-mode');
        
        // Swap inline colors
        if (isDark) {
            applyDarkModeColors();
        } else {
            applyLightModeColors();
        }
        
        // Save preference
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        
        console.log('[Dark Mode] Toggled to:', isDark ? 'dark' : 'light');
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDarkModeToggle);
    } else {
        initDarkModeToggle();
    }
    
    // Re-apply colors when Dash re-renders
    const observer = new MutationObserver(function(mutations) {
        const isDark = document.body.classList.contains('dark-mode');
        if (isDark) {
            swapInlineColors(true);
        }
    });
    
    // Observe the entire document for changes
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['style']
    });
    
    // Also try to initialize after Dash finishes rendering
    setTimeout(initDarkModeToggle, 1000);
})();
