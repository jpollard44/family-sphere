/**
 * Calendar Templates JavaScript
 * Handles functionality for creating, editing, and using calendar event templates
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize template management
    initTemplateManagement();
    
    // Initialize template usage in calendar view
    if (document.getElementById('calendar')) {
        initCalendarTemplateIntegration();
    }
});

/**
 * Initialize template management functionality
 */
function initTemplateManagement() {
    // Toggle time inputs based on all-day checkbox
    const allDayCheckbox = document.getElementById('all_day');
    if (allDayCheckbox) {
        const timeInputs = document.getElementById('time-inputs');
        
        function toggleTimeInputs() {
            if (allDayCheckbox.checked) {
                timeInputs.style.display = 'none';
            } else {
                timeInputs.style.display = 'flex';
            }
        }
        
        allDayCheckbox.addEventListener('change', toggleTimeInputs);
        toggleTimeInputs();
        
        // Reset form button
        const resetButton = document.getElementById('reset-form');
        if (resetButton) {
            resetButton.addEventListener('click', function() {
                document.getElementById('template-form').reset();
                document.getElementById('template_id').value = '';
                toggleTimeInputs();
            });
        }
    }
    
    // Edit template buttons
    document.querySelectorAll('.edit-template').forEach(button => {
        button.addEventListener('click', function() {
            const templateId = this.getAttribute('data-template-id');
            const templateName = this.getAttribute('data-template-name');
            const eventTitle = this.getAttribute('data-event-title');
            const eventCategory = this.getAttribute('data-event-category');
            const eventLocation = this.getAttribute('data-event-location');
            const eventDescription = this.getAttribute('data-event-description');
            const allDay = this.getAttribute('data-all-day') === 'true';
            const eventTime = this.getAttribute('data-event-time');
            const eventEndTime = this.getAttribute('data-event-end-time');
            const recurrencePattern = this.getAttribute('data-recurrence-pattern');
            
            document.getElementById('template_id').value = templateId;
            document.getElementById('template_name').value = templateName;
            document.getElementById('event_title').value = eventTitle;
            document.getElementById('event_category').value = eventCategory;
            document.getElementById('event_location').value = eventLocation;
            document.getElementById('event_description').value = eventDescription;
            document.getElementById('all_day').checked = allDay;
            document.getElementById('event_time').value = eventTime;
            document.getElementById('event_end_time').value = eventEndTime;
            document.getElementById('recurrence_pattern').value = recurrencePattern;
            
            if (allDayCheckbox) toggleTimeInputs();
            
            // Scroll to form
            document.getElementById('template-form').scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
    
    // Delete template buttons
    document.querySelectorAll('.delete-template').forEach(button => {
        button.addEventListener('click', function() {
            const templateId = this.getAttribute('data-template-id');
            const templateName = this.getAttribute('data-template-name');
            
            document.getElementById('delete_template_id').value = templateId;
            document.getElementById('delete-template-name').textContent = templateName;
            
            const deleteModal = new bootstrap.Modal(document.getElementById('deleteTemplateModal'));
            deleteModal.show();
        });
    });
    
    // Sample template buttons
    document.querySelectorAll('.create-sample-template').forEach(button => {
        button.addEventListener('click', function() {
            const templateName = this.getAttribute('data-template-name');
            const eventTitle = this.getAttribute('data-event-title');
            const eventCategory = this.getAttribute('data-event-category');
            const eventLocation = this.getAttribute('data-event-location');
            const eventDescription = this.getAttribute('data-event-description');
            const allDay = this.getAttribute('data-all-day') === 'true';
            const eventTime = this.getAttribute('data-event-time');
            const eventEndTime = this.getAttribute('data-event-end-time');
            const recurrencePattern = this.getAttribute('data-recurrence-pattern');
            
            document.getElementById('template_name').value = templateName;
            document.getElementById('event_title').value = eventTitle;
            document.getElementById('event_category').value = eventCategory;
            document.getElementById('event_location').value = eventLocation;
            document.getElementById('event_description').value = eventDescription;
            document.getElementById('all_day').checked = allDay;
            document.getElementById('event_time').value = eventTime;
            document.getElementById('event_end_time').value = eventEndTime;
            document.getElementById('recurrence_pattern').value = recurrencePattern;
            
            if (allDayCheckbox) toggleTimeInputs();
            
            // Scroll to form
            document.getElementById('template-form').scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
}

/**
 * Initialize template integration with the calendar view
 */
function initCalendarTemplateIntegration() {
    // Add template button to calendar toolbar if it doesn't exist
    const calendarToolbar = document.querySelector('.fc-toolbar-chunk:last-child');
    if (calendarToolbar && !document.getElementById('template-dropdown-button')) {
        // Create template dropdown button
        const templateButton = document.createElement('div');
        templateButton.className = 'btn-group ms-2';
        templateButton.innerHTML = `
            <button id="template-dropdown-button" type="button" class="btn btn-outline-primary dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false">
                <i class="fas fa-clipboard-list me-1"></i> Templates
            </button>
            <ul class="dropdown-menu dropdown-menu-end" id="template-dropdown-menu">
                <li><h6 class="dropdown-header">Event Templates</h6></li>
                <li><a class="dropdown-item" href="${window.location.pathname}templates">
                    <i class="fas fa-cog me-1"></i> Manage Templates
                </a></li>
                <li><hr class="dropdown-divider"></li>
                <li><div class="dropdown-item text-center" id="loading-templates">
                    <div class="spinner-border spinner-border-sm text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <span class="ms-2">Loading templates...</span>
                </div></li>
            </ul>
        `;
        calendarToolbar.appendChild(templateButton);
        
        // Load templates when dropdown is opened
        const templateDropdown = document.getElementById('template-dropdown-button');
        templateDropdown.addEventListener('click', loadTemplatesForDropdown);
    }
}

/**
 * Load templates for the dropdown menu
 */
function loadTemplatesForDropdown() {
    const dropdownMenu = document.getElementById('template-dropdown-menu');
    const loadingItem = document.getElementById('loading-templates');
    
    // Only load if we haven't already or if it's been more than 5 minutes
    const lastLoadTime = parseInt(localStorage.getItem('templatesLastLoaded') || '0');
    const currentTime = Date.now();
    
    if (currentTime - lastLoadTime > 300000 || !document.querySelector('.template-item')) {
        // Make AJAX request to get templates
        fetch('/api/calendar_templates')
            .then(response => response.json())
            .then(data => {
                // Remove loading indicator
                if (loadingItem) loadingItem.remove();
                
                // Remove existing template items
                document.querySelectorAll('.template-item').forEach(item => item.remove());
                
                // Add templates to dropdown
                if (data.templates && data.templates.length > 0) {
                    data.templates.forEach(template => {
                        const templateItem = document.createElement('li');
                        templateItem.className = 'template-item';
                        templateItem.innerHTML = `
                            <a class="dropdown-item template-dropdown-item" href="#" 
                               data-template-id="${template.id}"
                               data-template-name="${template.template_name}">
                                <i class="fas fa-${getCategoryIcon(template.event_category)} me-1"></i>
                                ${template.template_name}
                            </a>
                        `;
                        dropdownMenu.appendChild(templateItem);
                        
                        // Add click event to use template
                        templateItem.querySelector('.template-dropdown-item').addEventListener('click', function(e) {
                            e.preventDefault();
                            useTemplate(this.getAttribute('data-template-id'));
                        });
                    });
                } else {
                    // No templates message
                    const noTemplatesItem = document.createElement('li');
                    noTemplatesItem.className = 'template-item';
                    noTemplatesItem.innerHTML = `
                        <span class="dropdown-item text-muted">
                            <i class="fas fa-info-circle me-1"></i>
                            No templates available
                        </span>
                    `;
                    dropdownMenu.appendChild(noTemplatesItem);
                }
                
                // Store last load time
                localStorage.setItem('templatesLastLoaded', currentTime.toString());
            })
            .catch(error => {
                console.error('Error loading templates:', error);
                if (loadingItem) {
                    loadingItem.innerHTML = `
                        <i class="fas fa-exclamation-triangle text-danger me-1"></i>
                        Error loading templates
                    `;
                }
            });
    }
}

/**
 * Get icon for event category
 * @param {string} category - Event category
 * @returns {string} - Font Awesome icon name
 */
function getCategoryIcon(category) {
    const icons = {
        'Family': 'home',
        'Work': 'briefcase',
        'School': 'graduation-cap',
        'Health': 'heartbeat',
        'Social': 'users',
        'Sports': 'running',
        'Other': 'calendar'
    };
    
    return icons[category] || 'calendar';
}

/**
 * Use a template to create a new event
 * @param {string} templateId - Template ID
 */
function useTemplate(templateId) {
    // Redirect to the add event page with template ID
    window.location.href = `/calendar/add?template_id=${templateId}`;
}
