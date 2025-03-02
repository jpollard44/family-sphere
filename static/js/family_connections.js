/**
 * FamilySphere Family Connections JavaScript
 * Handles all family connection interactions and real-time updates
 */

// Family Connections Management
class FamilyConnections {
    constructor() {
        this.initializeEventListeners();
        this.loadConnections();
        this.loadPendingRequests();
    }

    initializeEventListeners() {
        // Connect form submission
        $('#connect-form').on('submit', (e) => this.handleConnectionRequest(e));

        // Request response buttons
        $(document).on('click', '.accept-request', (e) => this.handleRequestResponse(e, 'accept'));
        $(document).on('click', '.reject-request', (e) => this.handleRequestResponse(e, 'reject'));

        // Share item buttons
        $(document).on('click', '.share-item', (e) => this.handleShareItem(e));
        $(document).on('click', '.unshare-item', (e) => this.handleUnshareItem(e));

        // Search families input
        $('#family-search').on('input', (e) => this.handleFamilySearch(e));
    }

    async loadConnections() {
        try {
            const response = await fetch('/api/family/connections');
            if (!response.ok) throw new Error('Failed to load connections');
            
            const data = await response.json();
            this.displayConnections(data.data);
        } catch (error) {
            console.error('Error loading connections:', error);
            showToast('error', 'Failed to load family connections');
        }
    }

    async loadPendingRequests() {
        try {
            const response = await fetch('/api/family/connections/requests');
            if (!response.ok) throw new Error('Failed to load requests');
            
            const data = await response.json();
            this.displayRequests(data.data);
        } catch (error) {
            console.error('Error loading requests:', error);
            showToast('error', 'Failed to load connection requests');
        }
    }

    async handleConnectionRequest(e) {
        e.preventDefault();
        const familyCode = $('#family-code').val().trim();
        
        try {
            const response = await fetch('/api/family/connections/request', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ family_id: familyCode })
            });

            const data = await response.json();
            
            if (!response.ok) throw new Error(data.error || 'Failed to send request');
            
            showToast('success', 'Connection request sent successfully');
            $('#family-code').val('');
            this.loadPendingRequests();
        } catch (error) {
            console.error('Error sending request:', error);
            showToast('error', error.message);
        }
    }

    async handleRequestResponse(e, action) {
        e.preventDefault();
        const requestId = $(e.target).data('request-id');

        try {
            const response = await fetch('/api/family/connections/respond', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    request_id: requestId,
                    action: action
                })
            });

            const data = await response.json();
            
            if (!response.ok) throw new Error(data.error || `Failed to ${action} request`);
            
            showToast('success', `Connection request ${action}ed`);
            this.loadPendingRequests();
            if (action === 'accept') this.loadConnections();
        } catch (error) {
            console.error(`Error ${action}ing request:`, error);
            showToast('error', error.message);
        }
    }

    async handleShareItem(e) {
        e.preventDefault();
        const itemId = $(e.target).data('item-id');
        const itemType = $(e.target).data('item-type');
        const selectedFamilies = $('#share-families-modal').find('input:checked').map(function() {
            return $(this).val();
        }).get();

        if (!selectedFamilies.length) {
            showToast('warning', 'Please select at least one family to share with');
            return;
        }

        try {
            const response = await fetch('/api/family/connections/share', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    item_id: itemId,
                    type: itemType,
                    family_ids: selectedFamilies
                })
            });

            const data = await response.json();
            
            if (!response.ok) throw new Error(data.error || 'Failed to share item');
            
            showToast('success', 'Item shared successfully');
            $('#share-families-modal').modal('hide');
            this.refreshItemDisplay(itemType);
        } catch (error) {
            console.error('Error sharing item:', error);
            showToast('error', error.message);
        }
    }

    async handleUnshareItem(e) {
        e.preventDefault();
        const itemId = $(e.target).data('item-id');
        const itemType = $(e.target).data('item-type');
        const familyId = $(e.target).data('family-id');

        try {
            const response = await fetch('/api/family/connections/unshare', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    item_id: itemId,
                    type: itemType,
                    family_ids: [familyId]
                })
            });

            const data = await response.json();
            
            if (!response.ok) throw new Error(data.error || 'Failed to unshare item');
            
            showToast('success', 'Item unshared successfully');
            this.refreshItemDisplay(itemType);
        } catch (error) {
            console.error('Error unsharing item:', error);
            showToast('error', error.message);
        }
    }

    handleFamilySearch(e) {
        const searchTerm = e.target.value.toLowerCase();
        $('.family-card').each(function() {
            const familyName = $(this).find('.family-name').text().toLowerCase();
            $(this).toggle(familyName.includes(searchTerm));
        });
    }

    displayConnections(connections) {
        const container = $('#connected-families');
        container.empty();

        if (!connections.length) {
            container.append('<p class="text-muted">No connected families yet</p>');
            return;
        }

        connections.forEach(connection => {
            const family = connection.families;
            const card = `
                <div class="family-card card mb-3">
                    <div class="card-body">
                        <h5 class="family-name card-title">${family.name}</h5>
                        <p class="card-text">
                            <small class="text-muted">Connected since: ${new Date(connection.connected_date).toLocaleDateString()}</small>
                        </p>
                        <div class="btn-group">
                            <button class="btn btn-outline-primary btn-sm share-settings" 
                                    data-family-id="${family.id}">
                                Sharing Settings
                            </button>
                            <button class="btn btn-outline-danger btn-sm disconnect" 
                                    data-family-id="${family.id}">
                                Disconnect
                            </button>
                        </div>
                    </div>
                </div>
            `;
            container.append(card);
        });
    }

    displayRequests(requests) {
        const container = $('#pending-requests');
        container.empty();

        if (!requests.length) {
            container.append('<p class="text-muted">No pending requests</p>');
            return;
        }

        requests.forEach(request => {
            const isIncoming = request.requested_family_id === currentFamilyId;
            const otherFamily = isIncoming ? request.requesting_family : request.requested_family;
            
            const card = `
                <div class="request-card card mb-3">
                    <div class="card-body">
                        <h5 class="card-title">${otherFamily.name}</h5>
                        <p class="card-text">
                            <small class="text-muted">
                                ${isIncoming ? 'Incoming request' : 'Outgoing request'} • 
                                ${new Date(request.request_date).toLocaleDateString()}
                            </small>
                        </p>
                        ${isIncoming ? `
                            <div class="btn-group">
                                <button class="btn btn-success btn-sm accept-request" 
                                        data-request-id="${request.id}">
                                    Accept
                                </button>
                                <button class="btn btn-danger btn-sm reject-request" 
                                        data-request-id="${request.id}">
                                    Reject
                                </button>
                            </div>
                        ` : `
                            <button class="btn btn-outline-secondary btn-sm cancel-request" 
                                    data-request-id="${request.id}">
                                Cancel Request
                            </button>
                        `}
                    </div>
                </div>
            `;
            container.append(card);
        });
    }

    refreshItemDisplay(itemType) {
        // Refresh the specific item type's display
        switch (itemType) {
            case 'events':
                if (typeof Calendar !== 'undefined') Calendar.loadEvents();
                break;
            case 'tasks':
                if (typeof TaskManager !== 'undefined') TaskManager.loadTasks();
                break;
            case 'photos':
                if (typeof PhotoGallery !== 'undefined') PhotoGallery.loadPhotos();
                break;
            case 'shopping_lists':
                if (typeof ShoppingList !== 'undefined') ShoppingList.loadLists();
                break;
            case 'emergency_contacts':
                if (typeof EmergencyContacts !== 'undefined') EmergencyContacts.loadContacts();
                break;
        }
    }
}

// Initialize family connections when document is ready
$(document).ready(() => {
    window.FamilyConnections = new FamilyConnections();
});

/**
 * Initialize Bootstrap components
 */
function initializeBootstrapComponents() {
    // Initialize all tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize all popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * Load connected families
 */
function loadConnectedFamilies() {
    fetch('/api/family_connections/connected')
        .then(response => response.json())
        .then(data => {
            updateConnectedFamiliesUI(data.families);
        })
        .catch(error => {
            console.error('Error loading connected families:', error);
            showToast('Error loading connected families', 'error');
        });
}

/**
 * Update connected families UI
 */
function updateConnectedFamiliesUI(families) {
    const container = document.getElementById('connected-families');
    if (!container) return;

    container.innerHTML = families.map(family => `
        <div class="col-md-6 mb-4">
            <div class="card h-100">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <h5 class="card-title">${family.name}</h5>
                        <div class="dropdown">
                            <button class="btn btn-link" type="button" data-bs-toggle="dropdown">
                                <i class="fas fa-ellipsis-v"></i>
                            </button>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="#" onclick="showSharingSettings('${family.id}')">
                                    <i class="fas fa-cog me-2"></i>Sharing Settings
                                </a></li>
                                <li><a class="dropdown-item" href="#" onclick="disconnectFamily('${family.id}')">
                                    <i class="fas fa-unlink me-2"></i>Disconnect
                                </a></li>
                            </ul>
                        </div>
                    </div>
                    <p class="card-text">
                        <small class="text-muted">Connected since ${new Date(family.connected_date).toLocaleDateString()}</small>
                    </p>
                    <div class="mt-3">
                        <h6>Shared Features:</h6>
                        <div class="d-flex flex-wrap gap-2">
                            ${family.shared_features.map(feature => 
                                `<span class="badge bg-primary">${feature}</span>`
                            ).join('')}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `).join('');

    // Update the counter
    document.getElementById('connected-count').textContent = families.length;
}

/**
 * Load connection requests
 */
function loadConnectionRequests() {
    fetch('/api/family_connections/requests')
        .then(response => response.json())
        .then(data => {
            updateRequestsUI(data);
        })
        .catch(error => {
            console.error('Error loading connection requests:', error);
            showToast('Error loading connection requests', 'error');
        });
}

/**
 * Update requests UI
 */
function updateRequestsUI(data) {
    // Update incoming requests
    const incomingContainer = document.getElementById('incoming-requests');
    if (incomingContainer) {
        incomingContainer.innerHTML = data.incoming.map(request => `
            <div class="card mb-3">
                <div class="card-body">
                    <h5 class="card-title">${request.family_name}</h5>
                    <p class="card-text">
                        <small class="text-muted">Requested on ${new Date(request.request_date).toLocaleDateString()}</small>
                    </p>
                    <div class="btn-group">
                        <button class="btn btn-success btn-sm" onclick="acceptRequest('${request.id}')">
                            <i class="fas fa-check me-1"></i>Accept
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="rejectRequest('${request.id}')">
                            <i class="fas fa-times me-1"></i>Reject
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    // Update outgoing requests
    const outgoingContainer = document.getElementById('outgoing-requests');
    if (outgoingContainer) {
        outgoingContainer.innerHTML = data.outgoing.map(request => `
            <div class="card mb-3">
                <div class="card-body">
                    <h5 class="card-title">${request.family_name}</h5>
                    <p class="card-text">
                        <small class="text-muted">Sent on ${new Date(request.request_date).toLocaleDateString()}</small>
                    </p>
                    <button class="btn btn-outline-danger btn-sm" onclick="cancelRequest('${request.id}')">
                        <i class="fas fa-times me-1"></i>Cancel Request
                    </button>
                </div>
            </div>
        `).join('');
    }

    // Update the counter and badge
    const totalPending = data.incoming.length + data.outgoing.length;
    document.getElementById('pending-count').textContent = totalPending;
    document.getElementById('requests-badge').textContent = totalPending;
}

/**
 * Load shared items
 */
function loadSharedItems() {
    const endpoints = {
        calendar: '/api/family_connections/shared/events',
        tasks: '/api/family_connections/shared/tasks',
        photos: '/api/family_connections/shared/photos',
        shopping: '/api/family_connections/shared/shopping',
        emergency: '/api/family_connections/shared/emergency'
    };

    // Load data for each shared category
    Object.entries(endpoints).forEach(([category, endpoint]) => {
        fetch(endpoint)
            .then(response => response.json())
            .then(data => {
                updateSharedItemsUI(category, data);
            })
            .catch(error => {
                console.error(`Error loading shared ${category}:`, error);
                showToast(`Error loading shared ${category}`, 'error');
            });
    });
}

/**
 * Update shared items UI
 */
function updateSharedItemsUI(category, data) {
    const containers = {
        calendar: 'shared-events-list',
        tasks: 'shared-tasks-list',
        photos: 'shared-photos-grid',
        shopping: 'shared-shopping-lists',
        emergency: 'shared-emergency-contacts'
    };

    const container = document.getElementById(containers[category]);
    if (!container) return;

    // Update the shared items count
    let totalShared = 0;
    Object.values(data).forEach(items => totalShared += items.length);
    document.getElementById('shared-count').textContent = totalShared;

    // Render items based on category
    switch (category) {
        case 'calendar':
            renderSharedEvents(container, data.events);
            break;
        case 'tasks':
            renderSharedTasks(container, data.tasks);
            break;
        case 'photos':
            renderSharedPhotos(container, data.photos);
            break;
        case 'shopping':
            renderSharedShoppingLists(container, data.lists);
            break;
        case 'emergency':
            renderSharedEmergencyContacts(container, data.contacts);
            break;
    }
}

/**
 * Send a connection request
 */
function sendConnectionRequest(event) {
    event.preventDefault();
    const familyCode = document.getElementById('family-code').value;

    fetch('/api/family_connections/request', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': getCsrfToken()
        },
        body: JSON.stringify({ family_code: familyCode })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Connection request sent successfully', 'success');
            document.getElementById('family-code').value = '';
            loadConnectionRequests();
        } else {
            showToast(data.message || 'Error sending connection request', 'error');
        }
    })
    .catch(error => {
        console.error('Error sending connection request:', error);
        showToast('Error sending connection request', 'error');
    });

    return false;
}

/**
 * Accept a connection request
 */
function acceptRequest(requestId) {
    fetch(`/api/family_connections/accept/${requestId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Connection request accepted', 'success');
            loadConnectedFamilies();
            loadConnectionRequests();
        } else {
            showToast(data.message || 'Error accepting request', 'error');
        }
    })
    .catch(error => {
        console.error('Error accepting request:', error);
        showToast('Error accepting request', 'error');
    });
}

/**
 * Reject a connection request
 */
function rejectRequest(requestId) {
    showConfirmationModal(
        'Are you sure you want to reject this connection request?',
        () => {
            fetch(`/api/family_connections/reject/${requestId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': getCsrfToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast('Connection request rejected', 'success');
                    loadConnectionRequests();
                } else {
                    showToast(data.message || 'Error rejecting request', 'error');
                }
            })
            .catch(error => {
                console.error('Error rejecting request:', error);
                showToast('Error rejecting request', 'error');
            });
        }
    );
}

/**
 * Cancel a connection request
 */
function cancelRequest(requestId) {
    showConfirmationModal(
        'Are you sure you want to cancel this connection request?',
        () => {
            fetch(`/api/family_connections/cancel/${requestId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': getCsrfToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast('Connection request cancelled', 'success');
                    loadConnectionRequests();
                } else {
                    showToast(data.message || 'Error cancelling request', 'error');
                }
            })
            .catch(error => {
                console.error('Error cancelling request:', error);
                showToast('Error cancelling request', 'error');
            });
        }
    );
}

/**
 * Show sharing settings modal
 */
function showSharingSettings(familyId) {
    fetch(`/api/family_connections/sharing/${familyId}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('sharing-family-id').value = familyId;
            
            // Set checkbox states
            Object.entries(data.settings).forEach(([feature, enabled]) => {
                const checkbox = document.getElementById(`share-${feature}`);
                if (checkbox) checkbox.checked = enabled;
            });

            // Show the modal
            const modal = new bootstrap.Modal(document.getElementById('sharingSettingsModal'));
            modal.show();
        })
        .catch(error => {
            console.error('Error loading sharing settings:', error);
            showToast('Error loading sharing settings', 'error');
        });
}

/**
 * Save sharing settings
 */
function saveSharingSettings() {
    const familyId = document.getElementById('sharing-family-id').value;
    const settings = {
        calendar: document.getElementById('share-calendar').checked,
        tasks: document.getElementById('share-tasks').checked,
        photos: document.getElementById('share-photos').checked,
        shopping: document.getElementById('share-shopping').checked,
        emergency: document.getElementById('share-emergency').checked,
        documents: document.getElementById('share-documents').checked
    };

    fetch(`/api/family_connections/sharing/${familyId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': getCsrfToken()
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Sharing settings updated successfully', 'success');
            bootstrap.Modal.getInstance(document.getElementById('sharingSettingsModal')).hide();
            loadConnectedFamilies();
            loadSharedItems();
        } else {
            showToast(data.message || 'Error updating sharing settings', 'error');
        }
    })
    .catch(error => {
        console.error('Error saving sharing settings:', error);
        showToast('Error saving sharing settings', 'error');
    });
}

/**
 * Disconnect from a family
 */
function disconnectFamily(familyId) {
    showConfirmationModal(
        'Are you sure you want to disconnect from this family? All shared items will be removed.',
        () => {
            fetch(`/api/family_connections/disconnect/${familyId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': getCsrfToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast('Family disconnected successfully', 'success');
                    loadConnectedFamilies();
                    loadSharedItems();
                } else {
                    showToast(data.message || 'Error disconnecting family', 'error');
                }
            })
            .catch(error => {
                console.error('Error disconnecting family:', error);
                showToast('Error disconnecting family', 'error');
            });
        }
    );
}

/**
 * Copy family code to clipboard
 */
function copyFamilyCode() {
    const codeInput = document.getElementById('your-family-code');
    codeInput.select();
    document.execCommand('copy');
    showToast('Family code copied to clipboard', 'success');
}

/**
 * Show confirmation modal
 */
function showConfirmationModal(message, onConfirm) {
    const modal = document.getElementById('confirmationModal');
    document.getElementById('confirmation-message').textContent = message;
    document.getElementById('confirm-action-btn').onclick = () => {
        onConfirm();
        bootstrap.Modal.getInstance(modal).hide();
    };
    new bootstrap.Modal(modal).show();
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
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        document.body.removeChild(toast);
    });
}

/**
 * Get CSRF token
 */
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

/**
 * Setup real-time updates using Supabase
 */
function setupRealtimeUpdates() {
    // Subscribe to family connection changes
    supabase
        .from('family_connections')
        .on('*', payload => {
            console.log('Family connection changed:', payload);
            loadConnectedFamilies();
            loadConnectionRequests();
        })
        .subscribe();

    // Subscribe to shared item changes
    const sharedTables = [
        'shared_events',
        'shared_tasks',
        'shared_photos',
        'shared_shopping_lists',
        'shared_emergency_contacts'
    ];

    sharedTables.forEach(table => {
        supabase
            .from(table)
            .on('*', payload => {
                console.log(`${table} changed:`, payload);
                loadSharedItems();
            })
            .subscribe();
    });
}

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips and popovers
    initializeBootstrapComponents();
    
    // Load initial data
    loadConnectedFamilies();
    loadConnectionRequests();
    loadSharedItems();
    
    // Setup real-time updates
    setupRealtimeUpdates();
});
