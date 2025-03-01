/**
 * FamilySphere Real-time Chat
 * Implements Supabase real-time subscriptions for chat functionality
 */

class RealtimeChat {
    constructor(familyId, userId, username) {
        this.familyId = familyId;
        this.userId = userId;
        this.username = username;
        this.lastTimestamp = null;
        this.threadId = 'all';
        this.supabaseClient = null;
        this.subscription = null;
    }

    /**
     * Initialize the Supabase client and set up real-time subscriptions
     */
    async initialize() {
        try {
            // Get Supabase client from the server
            const response = await fetch('/api/supabase/client');
            const data = await response.json();
            
            if (!data.success) {
                console.error('Failed to get Supabase client:', data.error);
                return;
            }
            
            // Initialize Supabase client with anon key
            this.supabaseClient = supabase.createClient(data.supabaseUrl, data.supabaseKey);
            
            // Set up real-time subscription
            this.subscribeToChats();
            
            console.log('Real-time chat initialized successfully');
        } catch (error) {
            console.error('Error initializing real-time chat:', error);
        }
    }

    /**
     * Subscribe to chat messages for the family
     */
    subscribeToChats() {
        if (!this.supabaseClient) {
            console.error('Supabase client not initialized');
            return;
        }
        
        // Unsubscribe from any existing subscription
        if (this.subscription) {
            this.supabaseClient.removeSubscription(this.subscription);
        }
        
        // Subscribe to the chats table for this family
        this.subscription = this.supabaseClient
            .from('chats')
            .on('INSERT', this.handleNewMessage.bind(this))
            .subscribe();
            
        console.log('Subscribed to chat messages');
    }

    /**
     * Handle new chat messages from the real-time subscription
     * @param {Object} payload - The payload from Supabase real-time
     */
    handleNewMessage(payload) {
        const message = payload.new;
        
        // Skip if message is not for this family
        if (message.family_id !== this.familyId) {
            return;
        }
        
        // Skip if message is for a different thread than the current one
        if (this.threadId !== 'all' && message.thread_id !== this.threadId) {
            return;
        }
        
        // Format and display the message
        this.displayMessage({
            id: message.id,
            message: message.message,
            sender_id: message.sender_id,
            sender_name: message.sender_id === this.userId ? this.username : 'Loading...',
            timestamp: message.timestamp,
            thread_id: message.thread_id,
            is_poll: message.is_poll,
            poll_options: message.poll_options
        });
        
        // Update last timestamp
        this.lastTimestamp = message.timestamp;
        
        // Get sender name if not the current user
        if (message.sender_id !== this.userId) {
            this.fetchSenderName(message.sender_id);
        }
    }

    /**
     * Fetch the sender's name from the server
     * @param {string} senderId - The ID of the message sender
     */
    async fetchSenderName(senderId) {
        try {
            const response = await fetch(`/api/user/${senderId}/name`);
            const data = await response.json();
            
            if (data.success) {
                // Update sender name in the UI
                document.querySelectorAll(`.message-sender-${senderId}`).forEach(el => {
                    el.textContent = data.username;
                });
            }
        } catch (error) {
            console.error('Error fetching sender name:', error);
        }
    }

    /**
     * Display a message in the chat UI
     * @param {Object} message - The message object to display
     */
    displayMessage(message) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;
        
        const isCurrentUser = message.sender_id === this.userId;
        const messageClass = isCurrentUser ? 'message-outgoing' : 'message-incoming';
        
        const messageElement = document.createElement('div');
        messageElement.className = `message-bubble ${messageClass}`;
        messageElement.setAttribute('data-message-id', message.id);
        
        let messageContent = `<div class="message-content">${message.message}</div>`;
        
        // Handle polls
        if (message.is_poll && message.poll_options) {
            const options = message.poll_options.split(',');
            let pollHtml = '<div class="poll-options">';
            
            options.forEach(option => {
                pollHtml += `
                    <div class="poll-option" data-option="${option}" data-message-id="${message.id}">
                        ${option} <span class="poll-count">0</span>
                    </div>
                `;
            });
            
            pollHtml += '</div>';
            messageContent += pollHtml;
        }
        
        const timestamp = new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageElement.innerHTML = `
            ${messageContent}
            <div class="message-meta">
                <span class="message-sender message-sender-${message.sender_id}">${message.sender_name}</span>
                <span class="message-time">${timestamp}</span>
            </div>
        `;
        
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Add event listeners for poll options
        if (message.is_poll) {
            messageElement.querySelectorAll('.poll-option').forEach(option => {
                option.addEventListener('click', this.handlePollVote.bind(this));
            });
        }
    }

    /**
     * Handle voting on a poll
     * @param {Event} event - The click event
     */
    async handlePollVote(event) {
        const option = event.currentTarget.getAttribute('data-option');
        const messageId = event.currentTarget.getAttribute('data-message-id');
        
        try {
            const response = await fetch('/vote_poll', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: `chat_id=${messageId}&option=${encodeURIComponent(option)}`
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update vote counts in the UI
                const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
                if (messageElement) {
                    const voteData = data.vote_counts;
                    
                    for (const [opt, count] of Object.entries(voteData)) {
                        const optionElement = messageElement.querySelector(`[data-option="${opt}"] .poll-count`);
                        if (optionElement) {
                            optionElement.textContent = count;
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Error voting on poll:', error);
        }
    }

    /**
     * Switch to a different chat thread
     * @param {string} threadId - The ID of the thread to switch to, or 'all' for all threads
     */
    switchThread(threadId) {
        this.threadId = threadId;
        this.lastTimestamp = null;
        
        // Clear chat messages
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.innerHTML = '';
        }
        
        // Load initial messages for the thread
        this.loadInitialMessages();
    }

    /**
     * Load initial messages for the current thread
     */
    async loadInitialMessages() {
        try {
            const url = this.threadId === 'all' 
                ? '/get_messages' 
                : `/get_messages?thread_id=${this.threadId}`;
                
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.messages && data.messages.length > 0) {
                const chatMessages = document.getElementById('chatMessages');
                if (chatMessages) {
                    chatMessages.innerHTML = '';
                    
                    data.messages.forEach(message => {
                        this.displayMessage(message);
                    });
                    
                    // Update last timestamp
                    this.lastTimestamp = data.messages[data.messages.length - 1].timestamp;
                }
            }
        } catch (error) {
            console.error('Error loading initial messages:', error);
        }
    }

    /**
     * Send a new chat message
     * @param {string} message - The message text
     * @param {string} threadId - The thread ID, or 'new' for a new thread
     * @param {string} threadName - The name of the new thread (if creating one)
     * @param {boolean} isPoll - Whether this is a poll
     * @param {string} pollOptions - Comma-separated poll options
     */
    async sendMessage(message, threadId = null, threadName = null, isPoll = false, pollOptions = null) {
        if (!message) return;
        
        const formData = new FormData();
        formData.append('message', message);
        
        if (threadId) {
            formData.append('thread_id', threadId);
        }
        
        if (threadId === 'new' && threadName) {
            formData.append('thread_name', threadName);
        }
        
        if (isPoll) {
            formData.append('is_poll', 'true');
            formData.append('poll_options', pollOptions);
        }
        
        try {
            const response = await fetch('/send_message', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Clear the message input
                const messageInput = document.getElementById('messageInput');
                if (messageInput) {
                    messageInput.value = '';
                }
                
                // If this was a new thread, switch to it
                if (threadId === 'new' && data.thread_id) {
                    this.switchThread(data.thread_id);
                }
            }
        } catch (error) {
            console.error('Error sending message:', error);
        }
    }
}

// Initialize real-time chat when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the chat page
    if (window.location.pathname.includes('/chat')) {
        // Get user and family info from the page
        const familyId = document.getElementById('familyId')?.value;
        const userId = document.getElementById('userId')?.value;
        const username = document.getElementById('username')?.value;
        
        if (familyId && userId && username) {
            // Initialize real-time chat
            window.realtimeChat = new RealtimeChat(familyId, userId, username);
            window.realtimeChat.initialize();
            
            // Set up message form submission
            const messageForm = document.getElementById('messageForm');
            if (messageForm) {
                messageForm.addEventListener('submit', function(e) {
                    e.preventDefault();
                    
                    const messageInput = document.getElementById('messageInput');
                    const threadSelect = document.getElementById('threadSelect');
                    
                    if (messageInput && messageInput.value.trim()) {
                        window.realtimeChat.sendMessage(
                            messageInput.value.trim(),
                            threadSelect ? threadSelect.value : null
                        );
                    }
                });
            }
            
            // Set up thread switching
            const threadSelect = document.getElementById('threadSelect');
            if (threadSelect) {
                threadSelect.addEventListener('change', function() {
                    window.realtimeChat.switchThread(this.value);
                });
            }
            
            // Load initial messages
            window.realtimeChat.loadInitialMessages();
        }
    }
});
