# FamilySphere Real-Time Features

This document outlines the real-time functionality implemented in FamilySphere using Supabase's real-time subscriptions.

## Overview

FamilySphere now supports real-time updates for chat messages, allowing family members to communicate instantly without needing to refresh the page or poll the server for updates.

## Technical Implementation

### Real-Time Chat

The real-time chat functionality is implemented using Supabase's real-time subscriptions, which are built on top of Phoenix Channels and provide a WebSocket-based connection to the database.

#### Key Components:

1. **Frontend JavaScript Client (`realtime-chat.js`)**
   - Manages WebSocket connections to Supabase
   - Subscribes to database changes
   - Updates the UI in real-time when new messages are received
   - Handles sending messages, creating threads, and voting on polls

2. **Backend API Endpoints**
   - `/api/supabase/client`: Provides Supabase configuration to the frontend
   - `/api/user/<user_id>/name`: Retrieves user information for message display
   - Existing chat endpoints (`/send_message`, `/get_messages`, etc.) continue to work for initial data loading and message sending

3. **Database Tables**
   - `chats`: Stores all chat messages
   - `chat_threads`: Organizes messages into conversation threads

### How It Works

1. When a user loads the chat page, the JavaScript client initializes a connection to Supabase using the credentials provided by the `/api/supabase/client` endpoint.

2. The client subscribes to the `chats` table, listening for `INSERT` events that indicate new messages.

3. When a user sends a message (via the form submission), the message is sent to the server using the existing `/send_message` endpoint, which inserts it into the database.

4. Supabase detects this insert and broadcasts it to all connected clients subscribed to that table.

5. Each client receives the new message via the WebSocket connection and updates its UI accordingly, without requiring a page refresh.

## User Experience Improvements

- **Instant Messaging**: Messages appear immediately for all family members
- **Real-Time Indicators**: Visual feedback shows when real-time functionality is active
- **Thread Support**: Messages can be organized into threads for better conversation management
- **Poll Functionality**: Create polls and see votes update in real-time

## Security Considerations

- Supabase client credentials (anon key) are provided only to authenticated users
- User verification ensures that users can only access messages from their own family
- All API endpoints require authentication via Flask-Login

## Future Enhancements

1. **Typing Indicators**: Show when family members are typing
2. **Read Receipts**: Indicate when messages have been seen
3. **Real-Time Notifications**: Extend real-time functionality to other parts of the application
4. **Offline Support**: Queue messages when offline and send when connection is restored

## Troubleshooting

If real-time updates are not working:

1. Check browser console for errors
2. Verify that Supabase credentials are correctly configured in `.env`
3. Ensure that the user is properly authenticated
4. Check network tab for WebSocket connection status
