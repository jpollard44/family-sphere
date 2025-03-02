/**
 * SphereBot Interactive Chat
 * Provides an interactive AI assistant interface for FamilySphere
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const sphereBotBubble = document.getElementById('spherebot-bubble');
    const sphereBotChat = document.getElementById('spherebot-chat');
    const sphereBotMinimize = document.getElementById('spherebot-minimize');
    const sphereBotClose = document.getElementById('spherebot-close');
    const chatMessages = document.getElementById('spherebot-messages');
    const messageInput = document.getElementById('spherebot-input');
    const sendButton = document.getElementById('spherebot-send');
    
    // State
    let isExpanded = false;
    let chatHistory = [];
    
    // Helper Functions
    function getCurrentTime() {
        const now = new Date();
        let hours = now.getHours();
        const minutes = now.getMinutes().toString().padStart(2, '0');
        const ampm = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12;
        hours = hours ? hours : 12; // the hour '0' should be '12'
        return `${hours}:${minutes} ${ampm}`;
    }
    
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    
    function getCsrfToken() {
        // Try to get the token from the meta tag
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag && metaTag.getAttribute('content')) {
            return metaTag.getAttribute('content');
        }
        
        // If no meta tag, try to get from cookie
        const csrfCookie = document.cookie.split('; ').find(row => row.startsWith('csrf_token='));
        if (csrfCookie) {
            return csrfCookie.split('=')[1];
        }
        
        console.error('CSRF token not found in meta tag or cookies');
        return '';
    }
    
    // Function to send query to SphereBot and display response
    function querySphereBot() {
        const query = messageInput.value.trim();
        if (!query) return;

        // Add user message to chat
        addMessageToChat('user', query);
        
        // Show typing indicator
        showTypingIndicator();
        
        // Get CSRF token
        const csrfToken = getCsrfToken();
        console.log('Using CSRF token:', csrfToken);
        
        // Send query to server
        fetch('/spherebot/test_query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ query: query }),
            credentials: 'same-origin'
        })
        .then(response => {
            console.log('Response status:', response.status);
            console.log('Response headers:', response.headers);
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Remove typing indicator
            removeTypingIndicator();
            
            // Display response
            if (data.error) {
                addMessageToChat('bot', `Error: ${data.error}`);
                console.error('SphereBot error:', data.error);
            } else if (data.response) {
                // Add the bot response to chat
                addMessageToChat('bot', data.response);
            } else {
                addMessageToChat('bot', 'No response from SphereBot');
            }
            
            // Clear input field
            messageInput.value = '';
            
            // Scroll to bottom
            scrollToBottom();
        })
        .catch(error => {
            console.error('Error querying SphereBot:', error);
            removeTypingIndicator();
            addMessageToChat('bot', 'Error communicating with SphereBot. Please try again later.');
            scrollToBottom();
        });
    }

    // Function to add message to chat
    function addMessageToChat(sender, message) {
        if (!chatMessages) return;
        
        const messageElement = document.createElement('div');
        messageElement.className = 'spherebot-message';
        
        if (sender === 'user') {
            messageElement.classList.add('user-message');
            messageElement.innerHTML = `
                <div class="message-content">
                    <p>${escapeHtml(message)}</p>
                    <span class="message-time">${getCurrentTime()}</span>
                </div>
                <div class="avatar user-avatar">
                    <i class="fas fa-user"></i>
                </div>
            `;
        } else {
            messageElement.classList.add('bot-message');
            
            // Format the bot message (convert markdown to HTML)
            let formattedMessage = message;
            
            // Replace markdown-style links with HTML links
            formattedMessage = formattedMessage.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
            
            // Replace markdown-style bold with HTML bold
            formattedMessage = formattedMessage.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
            
            // Replace markdown-style italic with HTML italic
            formattedMessage = formattedMessage.replace(/\*([^*]+)\*/g, '<em>$1</em>');
            
            // Replace markdown-style lists with HTML lists
            formattedMessage = formattedMessage.replace(/^- (.+)$/gm, '<li>$1</li>');
            
            // Wrap list items in ul tags
            if (formattedMessage.includes('<li>')) {
                formattedMessage = '<ul>' + formattedMessage + '</ul>';
                // Fix nested lists
                formattedMessage = formattedMessage.replace(/<\/ul>(\s*)<ul>/g, '$1');
            }
            
            // Replace newlines with <br> tags
            formattedMessage = formattedMessage.replace(/\n/g, '<br>');
            
            messageElement.innerHTML = `
                <div class="avatar bot-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="message-content">
                    <p>${formattedMessage}</p>
                    <span class="message-time">${getCurrentTime()}</span>
                </div>
            `;
        }
        
        chatMessages.appendChild(messageElement);
        chatHistory.push({ sender: sender, message: message });
    }
    
    // Function to show typing indicator
    function showTypingIndicator() {
        if (!chatMessages) return;
        
        const indicator = document.createElement('div');
        indicator.id = 'typing-indicator';
        indicator.className = 'spherebot-message bot-message';
        indicator.innerHTML = `
            <div class="avatar bot-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(indicator);
        scrollToBottom();
    }
    
    // Function to remove typing indicator
    function removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
    
    // Scroll chat to bottom
    function scrollToBottom() {
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }
    
    // Initialize
    function init() {
        // Add welcome message
        if (chatMessages) {
            addMessageToChat('bot', 'Hi there! I\'m SphereBot. How can I help you today?');
        }
        
        // Event listeners
        if (sphereBotBubble) {
            sphereBotBubble.addEventListener('click', function() {
                console.log('SphereBot bubble clicked');
                toggleChat();
            });
        }
        
        if (sphereBotMinimize) {
            sphereBotMinimize.addEventListener('click', function() {
                console.log('SphereBot minimize clicked');
                minimizeChat();
            });
        }
        
        if (sphereBotClose) {
            sphereBotClose.addEventListener('click', function() {
                console.log('SphereBot close clicked');
                closeChat();
            });
        }
        
        if (sendButton && messageInput) {
            sendButton.addEventListener('click', function(e) {
                e.preventDefault();
                querySphereBot();
            });
            
            messageInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    querySphereBot();
                }
            });
        }
    }
    
    // Toggle chat visibility
    function toggleChat() {
        if (!sphereBotChat) {
            console.error('SphereBot chat element not found');
            return;
        }
        
        isExpanded = !isExpanded;
        
        if (isExpanded) {
            console.log('Opening SphereBot chat');
            sphereBotChat.classList.add('active');
            sphereBotBubble.classList.add('hidden');
            // Focus on input field
            if (messageInput) {
                messageInput.focus();
            }
        } else {
            console.log('Closing SphereBot chat');
            sphereBotChat.classList.remove('active');
            sphereBotBubble.classList.remove('hidden');
        }
    }
    
    // Close chat completely
    function closeChat() {
        isExpanded = false;
        if (sphereBotChat) sphereBotChat.classList.remove('active');
        if (sphereBotBubble) sphereBotBubble.classList.remove('hidden');
    }
    
    // Minimize chat
    function minimizeChat() {
        isExpanded = false;
        if (sphereBotChat) sphereBotChat.classList.remove('active');
        if (sphereBotBubble) sphereBotBubble.classList.remove('hidden');
    }
    
    // Initialize the chat
    init();
});
