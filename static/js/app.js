/**
 * FamilySphere Main JavaScript
 * Handles UI interactions and SphereBot AI functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize SphereBot
    initSphereBot();
    
    // Initialize tooltips and popovers
    initBootstrapComponents();
    
    // Initialize any page-specific functionality
    initPageSpecific();
});

/**
 * Initialize SphereBot AI functionality
 */
function initSphereBot() {
    const sphereBotBubble = document.getElementById('spherebot-bubble');
    const sphereBotContent = document.getElementById('spherebot-content');
    
    if (!sphereBotBubble) return;
    
    // Toggle expanded state when clicking the bubble
    sphereBotBubble.addEventListener('click', function() {
        // In a full implementation, this would open a chat interface
        // For now, we'll just show a different message
        if (sphereBotContent.textContent.includes('How can I help')) {
            getSphereBot('general');
        } else {
            sphereBotContent.textContent = "Hi there! I'm SphereBot. How can I help you today?";
        }
    });
    
    // Periodically update suggestions based on current page
    setInterval(function() {
        const currentPage = getCurrentPage();
        if (currentPage) {
            getSphereBot(currentPage);
        }
    }, 60000); // Update every minute
}

/**
 * Get SphereBot AI suggestions via API
 * @param {string} context - The current context (page or action)
 */
function getSphereBot(context, query = null) {
    const sphereBotContent = document.getElementById('spherebot-content');
    if (!sphereBotContent) return;
    
    // In a real implementation, this would call the backend API
    // For demo purposes, we'll simulate a response
    fetch('/api/spherebot/suggestion', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        },
        body: JSON.stringify({
            context: context,
            query: query
        }),
    })
    .then(response => response.json())
    .then(data => {
        sphereBotContent.textContent = data.suggestion;
    })
    .catch(error => {
        console.error('Error getting SphereBot suggestion:', error);
    });
}

/**
 * Determine the current page based on URL
 * @returns {string} The current page context
 */
function getCurrentPage() {
    const path = window.location.pathname;
    
    if (path === '/' || path === '/dashboard') return 'dashboard';
    if (path.includes('/calendar')) return 'calendar';
    if (path.includes('/tasks')) return 'tasks';
    if (path.includes('/finances')) return 'finance';
    if (path.includes('/chat')) return 'chat';
    if (path.includes('/memories')) return 'memory';
    if (path.includes('/inventory')) return 'inventory';
    if (path.includes('/health')) return 'health';
    
    return 'general';
}

/**
 * Initialize Bootstrap components
 */
function initBootstrapComponents() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * Initialize page-specific functionality
 */
function initPageSpecific() {
    // Calendar page functionality
    if (window.location.pathname.includes('/calendar')) {
        initCalendar();
    }
    
    // Tasks page functionality
    if (window.location.pathname.includes('/tasks')) {
        initTasksPage();
    }
    
    // Settings page functionality
    if (window.location.pathname.includes('/settings')) {
        initSettingsPage();
    }
}

/**
 * Initialize calendar functionality
 */
function initCalendar() {
    // This would be replaced with a proper calendar library in a real implementation
    console.log('Calendar initialized');
    
    // Example: Add event listeners to calendar events
    const calendarEvents = document.querySelectorAll('.calendar-event');
    calendarEvents.forEach(event => {
        event.addEventListener('click', function() {
            // Show event details
            const eventId = this.getAttribute('data-event-id');
            console.log('Clicked event:', eventId);
            
            // In a real implementation, this would open a modal with event details
        });
    });
}

/**
 * Initialize tasks page functionality
 */
function initTasksPage() {
    console.log('Tasks page initialized');
    
    // Example: Add event listeners to task cards
    const taskCards = document.querySelectorAll('.task-card');
    taskCards.forEach(card => {
        card.addEventListener('click', function() {
            // Show task details
            const taskId = this.getAttribute('data-task-id');
            console.log('Clicked task:', taskId);
            
            // In a real implementation, this would open a modal with task details
        });
    });
}

/**
 * Initialize settings page functionality
 */
function initSettingsPage() {
    console.log('Settings page initialized');
    
    // Example: Theme switcher
    const themeSwatches = document.querySelectorAll('.theme-swatch');
    themeSwatches.forEach(swatch => {
        swatch.addEventListener('click', function() {
            const theme = this.getAttribute('data-theme');
            console.log('Selected theme:', theme);
            
            // Remove active class from all swatches
            themeSwatches.forEach(s => s.classList.remove('active'));
            
            // Add active class to selected swatch
            this.classList.add('active');
            
            // In a real implementation, this would update the user's theme preference
        });
    });
}
