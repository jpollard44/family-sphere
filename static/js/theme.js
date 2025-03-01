/**
 * FamilySphere Theme Management
 * Handles theme switching between light and dark modes
 */

document.addEventListener('DOMContentLoaded', function() {
    // Theme elements
    const themeToggle = document.getElementById('theme-toggle');
    const htmlElement = document.documentElement;
    
    // Initialize theme
    initializeTheme();
    
    // Theme toggle click handler
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            toggleTheme();
        });
    }
    
    /**
     * Initialize theme based on saved preference or system preference
     */
    function initializeTheme() {
        // Check for saved theme preference
        const savedTheme = localStorage.getItem('theme');
        
        if (savedTheme) {
            applyTheme(savedTheme);
        } else {
            // Check if user prefers dark mode
            const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
            const initialTheme = prefersDarkMode ? 'dark' : 'light';
            applyTheme(initialTheme);
        }
        
        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            if (!localStorage.getItem('theme')) {
                const newTheme = e.matches ? 'dark' : 'light';
                applyTheme(newTheme);
            }
        });
    }
    
    /**
     * Toggle between light and dark themes
     */
    function toggleTheme() {
        const currentTheme = htmlElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        applyTheme(newTheme);
        
        // Save user preference
        localStorage.setItem('theme', newTheme);
        
        // Trigger a custom event that other components can listen for
        document.dispatchEvent(new CustomEvent('themeChanged', { 
            detail: { theme: newTheme } 
        }));
    }
    
    /**
     * Apply theme to document and update UI
     */
    function applyTheme(theme) {
        // Set theme attribute
        htmlElement.setAttribute('data-theme', theme);
        
        // Update theme toggle icon
        updateThemeIcon(theme);
        
        // Add transition class to body for smooth color transitions
        document.body.classList.add('theme-transition');
        
        // Remove transition class after transition completes
        setTimeout(() => {
            document.body.classList.remove('theme-transition');
        }, 500);
    }
    
    /**
     * Update the theme toggle icon based on current theme
     */
    function updateThemeIcon(theme) {
        if (themeToggle) {
            const icon = themeToggle.querySelector('i');
            if (theme === 'dark') {
                icon.classList.remove('fa-moon');
                icon.classList.add('fa-sun');
                themeToggle.setAttribute('title', 'Switch to Light Mode');
            } else {
                icon.classList.remove('fa-sun');
                icon.classList.add('fa-moon');
                themeToggle.setAttribute('title', 'Switch to Dark Mode');
            }
        }
    }
});
