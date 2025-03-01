/**
 * SphereBot Interactive Chat
 * Provides an interactive AI assistant interface for FamilySphere
 */

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const sphereBotBubble = document.getElementById('spherebot-bubble');
    const sphereBotChat = document.getElementById('spherebot-chat');
    const sphereBotToggle = document.getElementById('spherebot-toggle');
    const sphereBotClose = document.getElementById('spherebot-close');
    const sphereBotMinimize = document.getElementById('spherebot-minimize');
    const chatMessages = document.getElementById('spherebot-messages');
    const messageInput = document.getElementById('spherebot-input');
    const sendButton = document.getElementById('spherebot-send');
    
    // State
    let chatHistory = [];
    let isExpanded = false;
    
    // Initialize
    function init() {
        // Add welcome message
        addBotMessage("Hi there! I'm SphereBot. How can I help you today?");
        
        // Event listeners
        if (sphereBotBubble) {
            sphereBotBubble.addEventListener('click', toggleChat);
        }
        
        if (sphereBotToggle) {
            sphereBotToggle.addEventListener('click', toggleChat);
        }
        
        if (sphereBotClose) {
            sphereBotClose.addEventListener('click', closeChat);
        }
        
        if (sphereBotMinimize) {
            sphereBotMinimize.addEventListener('click', minimizeChat);
        }
        
        if (sendButton && messageInput) {
            sendButton.addEventListener('click', sendMessage);
            messageInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    sendMessage();
                }
            });
        }
        
        // Listen for theme changes
        document.addEventListener('themeChanged', function(e) {
            // Apply any theme-specific styling if needed
            console.log('Theme changed to: ' + e.detail.theme);
        });
    }
    
    // Toggle chat visibility
    function toggleChat() {
        if (!sphereBotChat) return;
        
        isExpanded = !isExpanded;
        
        if (isExpanded) {
            sphereBotChat.classList.add('active');
            sphereBotBubble.classList.add('hidden');
            // Focus on input field
            if (messageInput) {
                setTimeout(() => messageInput.focus(), 300);
            }
        } else {
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
    
    // Minimize chat to bubble
    function minimizeChat() {
        isExpanded = false;
        if (sphereBotChat) sphereBotChat.classList.remove('active');
        if (sphereBotBubble) sphereBotBubble.classList.remove('hidden');
    }
    
    // Send message to SphereBot
    function sendMessage() {
        if (!messageInput || !messageInput.value.trim()) return;
        
        const message = messageInput.value.trim();
        addUserMessage(message);
        messageInput.value = '';
        
        // Show typing indicator
        showTypingIndicator();
        
        // Send to backend
        fetch('/spherebot/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: message }),
        })
        .then(response => response.json())
        .then(data => {
            // Hide typing indicator
            hideTypingIndicator();
            
            // Add bot response
            addBotMessage(data.response);
            
            // Scroll to bottom
            scrollToBottom();
        })
        .catch(error => {
            console.error('Error:', error);
            hideTypingIndicator();
            addBotMessage("I'm sorry, I encountered an error. Please try again.");
            scrollToBottom();
        });
    }
    
    // Add user message to chat
    function addUserMessage(message) {
        if (!chatMessages) return;
        
        const messageElement = document.createElement('div');
        messageElement.className = 'spherebot-message user-message';
        messageElement.innerHTML = `
            <div class="message-content">
                <p>${escapeHtml(message)}</p>
                <span class="message-time">${getCurrentTime()}</span>
            </div>
            <div class="avatar user-avatar">
                <i class="fas fa-user"></i>
            </div>
        `;
        
        chatMessages.appendChild(messageElement);
        chatHistory.push({ sender: 'user', message: message });
        scrollToBottom();
    }
    
    // Add bot message to chat
    function addBotMessage(message) {
        if (!chatMessages) return;
        
        const messageElement = document.createElement('div');
        messageElement.className = 'spherebot-message bot-message';
        messageElement.innerHTML = `
            <div class="avatar bot-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <p>${escapeHtml(message)}</p>
                <span class="message-time">${getCurrentTime()}</span>
            </div>
        `;
        
        chatMessages.appendChild(messageElement);
        chatHistory.push({ sender: 'bot', message: message });
        scrollToBottom();
    }
    
    // Show typing indicator
    function showTypingIndicator() {
        if (!chatMessages) return;
        
        const indicator = document.createElement('div');
        indicator.className = 'spherebot-message bot-message typing-indicator';
        indicator.id = 'typing-indicator';
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
    
    // Hide typing indicator
    function hideTypingIndicator() {
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
    
    // Get current time formatted
    function getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    // Escape HTML to prevent XSS
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    
    // Initialize the chat
    init();
});
