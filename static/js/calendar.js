/**
 * FamilySphere Calendar JavaScript
 * Handles calendar functionality including color-coding, recurring events, and RSVP
 */

document.addEventListener('DOMContentLoaded', function() {
    initFullCalendar();
    setupEventListeners();
    setupRecurringEvents();
    setupRSVPSystem();
    setupReminderSystem();
    setupPrintFunctionality();
    setupTemplateSystem();
});

/**
 * Get CSRF token from cookie or meta tag
 * @returns {string} CSRF token
 */
function getCsrfToken() {
    // Try to get from cookie first
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrf_token='))
        ?.split('=')[1];
    
    if (cookieValue) {
        return cookieValue;
    }
    
    // Fall back to meta tag
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    return metaTag ? metaTag.getAttribute('content') : '';
}

/**
 * Initialize FullCalendar library
 */
function initFullCalendar() {
    const calendarEl = document.getElementById('family-calendar');
    if (!calendarEl) return;

    // Get events from data attribute
    const eventsData = JSON.parse(calendarEl.getAttribute('data-events') || '[]');
    
    // Process events to add color based on category
    const coloredEvents = eventsData.map(event => {
        // Assign colors based on event category
        let color;
        switch(event.category?.toLowerCase()) {
            case 'family':
                color = '#4285F4'; // Blue
                break;
            case 'work':
                color = '#EA4335'; // Red
                break;
            case 'school':
                color = '#FBBC05'; // Yellow
                break;
            case 'sports':
                color = '#34A853'; // Green
                break;
            case 'health':
                color = '#8E24AA'; // Purple
                break;
            case 'social':
                color = '#FB8C00'; // Orange
                break;
            default:
                color = '#9E9E9E'; // Gray
        }
        
        // Add border for shared events
        let borderColor = color;
        if (event.shared) {
            borderColor = '#FF5722'; // Deep Orange
        }
        
        return {
            ...event,
            backgroundColor: color,
            borderColor: borderColor,
            textColor: getContrastColor(color)
        };
    });
    
    // Initialize FullCalendar
    window.familyCalendar = new FullCalendar.Calendar(calendarEl, {
        initialView: localStorage.getItem('calendarView') || 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: ''
        },
        events: coloredEvents,
        editable: true,
        selectable: true,
        selectMirror: true,
        dayMaxEvents: true,
        weekNumbers: true,
        navLinks: true,
        businessHours: {
            daysOfWeek: [1, 2, 3, 4, 5], // Monday - Friday
            startTime: '08:00',
            endTime: '18:00'
        },
        nowIndicator: true,
        eventTimeFormat: {
            hour: '2-digit',
            minute: '2-digit',
            meridiem: 'short'
        },
        views: {
            dayGridMonth: {
                dayMaxEventRows: 6
            },
            timeGrid: {
                dayMaxEventRows: 6
            }
        },
        eventClick: handleEventClick,
        dateClick: handleDateClick,
        eventDrop: handleEventDrop,
        eventResize: handleEventResize,
        eventDidMount: function(info) {
            // Add tooltip with event details
            const tooltip = new bootstrap.Tooltip(info.el, {
                title: `${info.event.title}${info.event.extendedProps.location ? ' @ ' + info.event.extendedProps.location : ''}`,
                placement: 'top',
                trigger: 'hover',
                container: 'body'
            });
            
            // Add reminder icon if event has reminders
            if (info.event.extendedProps.has_reminder) {
                const reminderIcon = document.createElement('i');
                reminderIcon.className = 'fas fa-bell ms-1';
                reminderIcon.style.fontSize = '0.8em';
                info.el.querySelector('.fc-event-title').appendChild(reminderIcon);
            }
        }
    });
    
    window.familyCalendar.render();
}

/**
 * Handle event click - show event details
 */
function handleEventClick(info) {
    // Get event details
    const event = info.event;
    const eventId = event.id;
    
    // Fetch event details from server
    fetch(`/event/${eventId}`)
        .then(response => response.json())
        .then(data => {
            showEventModal(data);
        })
        .catch(error => {
            console.error('Error fetching event details:', error);
        });
}

/**
 * Handle date click - create new event
 */
function handleDateClick(info) {
    // Set the date in the add event form
    const addEventModal = document.getElementById('add-event-modal');
    if (addEventModal) {
        const dateInput = addEventModal.querySelector('#event-date');
        if (dateInput) {
            dateInput.value = info.dateStr;
        }
        
        // Show the modal
        const modal = new bootstrap.Modal(addEventModal);
        modal.show();
    } else {
        // Redirect to add event page with date pre-filled
        window.location.href = `/add_event?date=${info.dateStr}`;
    }
}

/**
 * Handle event drag and drop
 */
function handleEventDrop(info) {
    updateEventDates(info.event);
}

/**
 * Handle event resize
 */
function handleEventResize(info) {
    updateEventDates(info.event);
}

/**
 * Update event dates after drag or resize
 */
function updateEventDates(event) {
    const eventId = event.id;
    const newStart = event.start.toISOString().split('T')[0];
    const newEnd = event.end ? event.end.toISOString().split('T')[0] : null;
    
    // Send update to server
    fetch('/update_event_dates', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            event_id: eventId,
            start_date: newStart,
            end_date: newEnd
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Event updated successfully', 'success');
        } else {
            showToast('Failed to update event', 'danger');
            // Revert the change
            window.familyCalendar.refetchEvents();
        }
    })
    .catch(error => {
        console.error('Error updating event:', error);
        showToast('Error updating event', 'danger');
        // Revert the change
        window.familyCalendar.refetchEvents();
    });
}

/**
 * Show event details in modal
 * @param {Object} eventData - Event data
 */
function showEventModal(eventData) {
    fetch(`/event/${eventData.id}`)
        .then(response => response.json())
        .then(event => {
            const modal = document.getElementById('event-details-modal');
            
            if (!modal) return;
            
            // Set event details
            document.getElementById('event-title').textContent = event.title;
            document.getElementById('event-description').textContent = event.description || 'No description provided';
            document.getElementById('event-date').textContent = formatDate(event.date);
            document.getElementById('event-time').textContent = event.time ? formatTime(event.time) : 'All day';
            
            // Set modal title
            document.getElementById('eventDetailsModalLabel').textContent = event.title;
            
            // Handle RSVP section
            const rsvpSection = document.getElementById('event-rsvp-section');
            if (event.rsvp_enabled) {
                rsvpSection.style.display = 'block';
                
                // Set up RSVP buttons
                const rsvpButtons = document.querySelectorAll('.rsvp-btn');
                rsvpButtons.forEach(button => {
                    button.addEventListener('click', function() {
                        const response = this.getAttribute('data-response');
                        handleRSVP(event.id, response);
                    });
                });
                
                // Display RSVP responses
                const rsvpResponsesEl = document.getElementById('event-rsvp-responses');
                rsvpResponsesEl.innerHTML = renderRSVPResponses(event.rsvp_responses);
            } else {
                rsvpSection.style.display = 'none';
            }
            
            // Handle reminder section
            const reminderSection = document.getElementById('event-reminder-section');
            const reminderInfoEl = document.getElementById('event-reminder-info');
            const editReminderBtn = document.getElementById('edit-reminder-btn');
            const addReminderBtn = document.getElementById('add-reminder-btn');
            const removeReminderBtn = document.getElementById('remove-reminder-btn');
            
            if (event.reminder_enabled) {
                reminderSection.style.display = 'block';
                editReminderBtn.style.display = 'inline-block';
                addReminderBtn.style.display = 'none';
                removeReminderBtn.style.display = 'inline-block';
                
                // Format reminder time
                let reminderText = '';
                const reminderMinutes = parseInt(event.reminder_time);
                
                if (reminderMinutes < 60) {
                    reminderText = `${reminderMinutes} minutes before`;
                } else if (reminderMinutes === 60) {
                    reminderText = '1 hour before';
                } else if (reminderMinutes < 1440) {
                    reminderText = `${reminderMinutes / 60} hours before`;
                } else if (reminderMinutes === 1440) {
                    reminderText = '1 day before';
                } else if (reminderMinutes < 10080) {
                    reminderText = `${reminderMinutes / 1440} days before`;
                } else {
                    reminderText = `${reminderMinutes / 10080} weeks before`;
                }
                
                // Format notification method
                let notificationMethod = '';
                switch (event.notification_method) {
                    case 'app':
                        notificationMethod = 'In-app notification';
                        break;
                    case 'email':
                        notificationMethod = 'Email';
                        break;
                    case 'both':
                        notificationMethod = 'In-app and email';
                        break;
                    default:
                        notificationMethod = 'In-app notification';
                }
                
                reminderInfoEl.innerHTML = `
                    <p>You will be reminded <strong>${reminderText}</strong> via <strong>${notificationMethod}</strong>.</p>
                `;
            } else {
                reminderSection.style.display = 'block';
                editReminderBtn.style.display = 'none';
                addReminderBtn.style.display = 'inline-block';
                removeReminderBtn.style.display = 'none';
                
                reminderInfoEl.innerHTML = `
                    <p>No reminder set for this event.</p>
                `;
            }
            
            // Set up reminder button handlers
            editReminderBtn.onclick = function() {
                showEditReminderModal(event);
            };
            
            addReminderBtn.onclick = function() {
                showAddReminderModal(event);
            };
            
            removeReminderBtn.onclick = function() {
                if (confirm('Are you sure you want to remove this reminder?')) {
                    updateReminderPreferences(event.id, false);
                }
            };
            
            // Show delete button if user can edit
            const deleteButton = document.getElementById('delete-event-btn');
            if (deleteButton) {
                if (event.can_edit) {
                    deleteButton.style.display = 'block';
                    deleteButton.onclick = function() {
                        if (confirm('Are you sure you want to delete this event?')) {
                            deleteEvent(event.id);
                        }
                    };
                } else {
                    deleteButton.style.display = 'none';
                }
            }
            
            // Show the modal
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        })
        .catch(error => {
            console.error('Error fetching event details:', error);
            showToast('Error loading event details', 'danger');
        });
}

/**
 * Show edit reminder modal
 * @param {Object} event - Event data
 */
function showEditReminderModal(event) {
    // This would show a modal to edit reminder settings
    // For simplicity, we'll just use the update_reminder_preferences endpoint directly
    
    const reminderTime = prompt('Reminder time (minutes before event):', event.reminder_time);
    if (reminderTime === null) return;
    
    const notificationMethod = prompt('Notification method (app, email, both):', event.notification_method);
    if (notificationMethod === null) return;
    
    updateReminderPreferences(event.id, true, reminderTime, notificationMethod);
}

/**
 * Show add reminder modal
 * @param {Object} event - Event data
 */
function showAddReminderModal(event) {
    // Get default reminder preferences from localStorage
    const defaultReminderTime = localStorage.getItem('defaultReminderTime') || '60';
    const defaultNotificationMethod = localStorage.getItem('defaultNotificationMethod') || 'app';
    
    const reminderTime = prompt('Reminder time (minutes before event):', defaultReminderTime);
    if (reminderTime === null) return;
    
    const notificationMethod = prompt('Notification method (app, email, both):', defaultNotificationMethod);
    if (notificationMethod === null) return;
    
    updateReminderPreferences(event.id, true, reminderTime, notificationMethod);
}

/**
 * Update reminder preferences
 * @param {string} eventId - Event ID
 * @param {boolean} enabled - Whether reminder is enabled
 * @param {string} reminderTime - Reminder time in minutes before event
 * @param {string} notificationMethod - Notification method (app, email, both)
 */
function updateReminderPreferences(eventId, enabled, reminderTime = null, notificationMethod = null) {
    const data = {
        event_id: eventId,
        reminder_enabled: enabled
    };
    
    if (enabled) {
        data.reminder_time = reminderTime;
        data.notification_method = notificationMethod;
    }
    
    fetch('/update_reminder_preferences', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Reminder preferences updated', 'success');
            
            // Close the event modal
            const eventModal = document.getElementById('event-details-modal');
            const bsEventModal = bootstrap.Modal.getInstance(eventModal);
            bsEventModal.hide();
            
            // Refresh the calendar
            window.location.reload();
        } else {
            showToast(`Error: ${data.message}`, 'danger');
        }
    })
    .catch(error => {
        console.error('Error updating reminder preferences:', error);
        showToast('Error updating reminder preferences', 'danger');
    });
}

/**
 * Format date for display
 */
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

/**
 * Format time for display
 */
function formatTime(timeStr) {
    const [hours, minutes] = timeStr.split(':');
    const date = new Date();
    date.setHours(parseInt(hours, 10));
    date.setMinutes(parseInt(minutes, 10));
    
    return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
}

/**
 * Render RSVP responses
 */
function renderRSVPResponses(responses) {
    if (!responses || responses.length === 0) {
        return '<p>No responses yet</p>';
    }
    
    let html = '<ul class="list-group">';
    
    // Group responses by type
    const yes = responses.filter(r => r.response === 'yes');
    const maybe = responses.filter(r => r.response === 'maybe');
    const no = responses.filter(r => r.response === 'no');
    
    if (yes.length > 0) {
        html += `<li class="list-group-item list-group-item-success">Yes (${yes.length}): ${yes.map(r => r.username).join(', ')}</li>`;
    }
    
    if (maybe.length > 0) {
        html += `<li class="list-group-item list-group-item-warning">Maybe (${maybe.length}): ${maybe.map(r => r.username).join(', ')}</li>`;
    }
    
    if (no.length > 0) {
        html += `<li class="list-group-item list-group-item-danger">No (${no.length}): ${no.map(r => r.username).join(', ')}</li>`;
    }
    
    html += '</ul>';
    return html;
}

/**
 * Handle RSVP button click
 */
function handleRSVP(eventId, response) {
    // Send RSVP to server
    fetch('/event_rsvp', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            event_id: eventId,
            response: response
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the RSVP responses display
            const responsesEl = document.getElementById('event-rsvp-responses');
            if (responsesEl) {
                responsesEl.innerHTML = renderRSVPResponses(data.responses);
            }
            
            // Highlight the selected button
            const buttons = document.querySelectorAll('.rsvp-btn');
            buttons.forEach(button => {
                button.classList.remove('active');
            });
            const selectedButton = document.querySelector(`.rsvp-btn[data-response="${response}"]`);
            if (selectedButton) {
                selectedButton.classList.add('active');
            }
            
            showToast('RSVP submitted successfully', 'success');
        } else {
            showToast('Failed to submit RSVP', 'danger');
        }
    })
    .catch(error => {
        console.error('Error submitting RSVP:', error);
        showToast('Error submitting RSVP', 'danger');
    });
}

/**
 * Delete an event
 */
function deleteEvent(eventId) {
    fetch(`/delete_event/${eventId}`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Close the modal
            const modal = document.getElementById('event-details-modal');
            const bsModal = bootstrap.Modal.getInstance(modal);
            bsModal.hide();
            
            // Remove the event from the calendar
            const event = window.familyCalendar.getEventById(eventId);
            if (event) {
                event.remove();
            }
            
            showToast('Event deleted successfully', 'success');
        } else {
            showToast('Failed to delete event', 'danger');
        }
    })
    .catch(error => {
        console.error('Error deleting event:', error);
        showToast('Error deleting event', 'danger');
    });
}

/**
 * Setup event listeners for calendar controls
 */
function setupEventListeners() {
    // Event listeners for event details modal
    document.querySelectorAll('.event-rsvp-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const eventId = this.getAttribute('data-event-id');
            const response = this.getAttribute('data-response');
            handleRSVP(eventId, response);
        });
    });

    // Event listener for import calendar button
    const importBtn = document.getElementById('calendar-import');
    if (importBtn) {
        importBtn.addEventListener('click', function() {
            const importModal = new bootstrap.Modal(document.getElementById('import-calendar-modal'));
            importModal.show();
        });
    }

    // Event listener for export calendar button
    const exportBtn = document.querySelector('.export-calendar-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            const exportModal = new bootstrap.Modal(document.getElementById('exportModal'));
            exportModal.show();
        });
    }

    // Event listener for template dropdown
    const templateDropdown = document.getElementById('templateDropdown');
    if (templateDropdown) {
        templateDropdown.addEventListener('click', loadTemplatesForDropdown);
    }

    // Event listener for filter toggle
    const toggleFiltersBtn = document.getElementById('toggle-filters');
    if (toggleFiltersBtn) {
        toggleFiltersBtn.addEventListener('click', function() {
            const filterBody = document.getElementById('filter-body');
            if (filterBody) {
                if (filterBody.style.display === 'none') {
                    filterBody.style.display = 'block';
                    this.innerHTML = '<i class="fas fa-chevron-up"></i> Hide Filters';
                } else {
                    filterBody.style.display = 'none';
                    this.innerHTML = '<i class="fas fa-chevron-down"></i> Show Filters';
                }
            }
        });
    }

    // Event listener for apply filters button
    const applyFiltersBtn = document.getElementById('apply-filters');
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', function() {
            applyFilters();
        });
    }

    // Event listener for reset filters button
    const resetFiltersBtn = document.getElementById('reset-filters');
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', function() {
            resetFilters();
        });
    }

    // Event listener for view selector
    const viewSelector = document.getElementById('calendar-view-selector');
    if (viewSelector) {
        viewSelector.addEventListener('change', function() {
            const calendarApi = getCalendarApi();
            if (calendarApi) {
                calendarApi.changeView(this.value);
                // Save preference to localStorage
                localStorage.setItem('calendarViewPreference', this.value);
            }
        });

        // Set initial value from localStorage if available
        const savedView = localStorage.getItem('calendarViewPreference');
        if (savedView) {
            viewSelector.value = savedView;
            // Apply the saved view
            const calendarApi = getCalendarApi();
            if (calendarApi) {
                calendarApi.changeView(savedView);
            }
        }
    }
}

/**
 * Setup recurring events functionality
 */
function setupRecurringEvents() {
    // Toggle recurring options in add/edit event form
    const recurringCheckbox = document.getElementById('event-recurring');
    if (recurringCheckbox) {
        recurringCheckbox.addEventListener('change', function() {
            const recurringOptions = document.getElementById('recurring-options');
            if (recurringOptions) {
                recurringOptions.style.display = this.checked ? 'block' : 'none';
            }
        });
    }
}

/**
 * Setup RSVP system
 */
function setupRSVPSystem() {
    // RSVP functionality is handled by event listeners in setupEventListeners()
}

/**
 * Setup reminder system
 */
function setupReminderSystem() {
    // Check for reminders periodically
    checkForReminders();
    
    // Check for reminders every minute
    setInterval(checkForReminders, 60000);
}

/**
 * Check for due reminders
 */
function checkForReminders() {
    fetch('/check_reminders')
        .then(response => response.json())
        .then(data => {
            if (data.reminders && data.reminders.length > 0) {
                data.reminders.forEach(reminder => {
                    showReminderNotification(reminder);
                });
            }
        })
        .catch(error => {
            console.error('Error checking reminders:', error);
        });
}

/**
 * Show reminder notification
 * @param {Object} reminder - Reminder data
 */
function showReminderNotification(reminder) {
    const notificationId = `reminder-${reminder.event_id}`;
    
    // Check if notification was already shown
    if (localStorage.getItem(notificationId)) {
        return;
    }
    
    // Show toast notification
    showToast(`
        <div class="d-flex align-items-center">
            <i class="fas fa-bell me-2"></i>
            <div>
                <strong>Reminder:</strong> ${reminder.title}<br>
                <small>${reminder.event_date}</small>
            </div>
        </div>
    `, 'primary');
    
    // Mark notification as shown
    localStorage.setItem(notificationId, 'true');
    
    // Remove from localStorage after 10 minutes to prevent duplicates
    setTimeout(() => {
        localStorage.removeItem(notificationId);
    }, 600000);
}

/**
 * Setup template system
 */
function setupTemplateSystem() {
    // Add event listener for template items
    document.addEventListener('click', function(e) {
        if (e.target && e.target.classList.contains('template-dropdown-item')) {
            e.preventDefault();
            const templateId = e.target.getAttribute('data-template-id');
            if (templateId) {
                useTemplate(templateId);
            }
        }
    });
}

/**
 * Load templates for dropdown menu
 */
function loadTemplatesForDropdown() {
    const dropdownMenu = document.querySelector('ul[aria-labelledby="templateDropdown"]');
    const loadingItem = document.getElementById('loading-templates');
    
    if (!dropdownMenu || !loadingItem) return;
    
    // Only load if we haven't already or if it's been more than 5 minutes
    const lastLoadTime = parseInt(localStorage.getItem('templatesLastLoaded') || '0');
    const currentTime = Date.now();
    
    if (currentTime - lastLoadTime > 300000 || !document.querySelector('.template-item')) {
        // Make AJAX request to get templates
        fetch('/api/calendar_templates')
            .then(response => response.json())
            .then(data => {
                // Remove loading indicator
                loadingItem.style.display = 'none';
                
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
                loadingItem.innerHTML = `
                    <i class="fas fa-exclamation-triangle text-danger me-1"></i>
                    Error loading templates
                `;
            });
    } else {
        // Templates already loaded, just show them
        loadingItem.style.display = 'none';
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
    // Get current date from calendar
    const calendarApi = getCalendarApi();
    let dateParam = '';
    
    if (calendarApi) {
        const currentDate = calendarApi.getDate();
        dateParam = `&date=${formatDateForUrl(currentDate)}`;
    }
    
    // Redirect to the add event page with template ID
    window.location.href = `/calendar/add?template_id=${templateId}${dateParam}`;
}

/**
 * Format date for URL parameter (YYYY-MM-DD)
 * @param {Date} date - Date object
 * @returns {string} - Formatted date string
 */
function formatDateForUrl(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * Get calendar API instance
 * @returns {Object|null} - FullCalendar API instance or null
 */
function getCalendarApi() {
    const calendarEl = document.getElementById('family-calendar');
    if (!calendarEl) return null;
    
    const calendarInstance = calendarEl._calendar;
    return calendarInstance ? calendarInstance.getApi() : null;
}

/**
 * Import external calendar
 */
function importExternalCalendar() {
    const modal = document.getElementById('import-calendar-modal');
    if (!modal) return;
    
    // Show the modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

/**
 * Setup print functionality
 */
function setupPrintFunctionality() {
    const printButton = document.getElementById('print-calendar');
    if (!printButton) return;
    
    printButton.addEventListener('click', function() {
        // Get current view and date range
        const view = window.familyCalendar.view;
        const viewType = view.type.includes('Month') ? 'month' : 
                         view.type.includes('Week') ? 'week' : 
                         view.type.includes('Day') ? 'day' : 'list';
        const startDate = view.activeStart.toISOString().split('T')[0];
        const endDate = view.activeEnd.toISOString().split('T')[0];
        
        // Get current category filter
        const category = document.getElementById('event-category-filter')?.value || 'all';
        
        // Construct URL with query parameters
        let url = `/print_calendar?view=${viewType}&start_date=${startDate}&end_date=${endDate}&category=${category}&autoprint=true`;
        
        // Open in new window
        window.open(url, '_blank');
    });
}

/**
 * Get contrasting text color (black or white) based on background color
 * @param {string} hexColor - Hex color code
 * @returns {string} - Black or white color code
 */
function getContrastColor(hexColor) {
    // Remove # if present
    hexColor = hexColor.replace('#', '');
    
    // Convert to RGB
    const r = parseInt(hexColor.substr(0, 2), 16);
    const g = parseInt(hexColor.substr(2, 2), 16);
    const b = parseInt(hexColor.substr(4, 2), 16);
    
    // Calculate luminance
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    
    // Return black for bright colors, white for dark colors
    return luminance > 0.5 ? '#000000' : '#FFFFFF';
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    const toastContainer = document.getElementById('toast-container');
    if (toastContainer) {
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: 3000
        });
        bsToast.show();
        
        // Remove from DOM after hiding
        toast.addEventListener('hidden.bs.toast', function() {
            toast.remove();
        });
    }
}
