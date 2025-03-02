-- Family Connections SQL Migration for Supabase

-- Table for family connection requests
CREATE TABLE IF NOT EXISTS family_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    requester_family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    target_family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, accepted, rejected
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(requester_family_id, target_family_id)
);

-- Table for shared calendar events
CREATE TABLE IF NOT EXISTS shared_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    shared_with_family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    shared_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permission_level VARCHAR(20) NOT NULL DEFAULT 'view', -- view, edit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(event_id, shared_with_family_id)
);

-- Table for shared tasks
CREATE TABLE IF NOT EXISTS shared_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    shared_with_family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    shared_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permission_level VARCHAR(20) NOT NULL DEFAULT 'view', -- view, edit, assign
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(task_id, shared_with_family_id)
);

-- Table for inter-family messages
CREATE TABLE IF NOT EXISTS family_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sender_family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    sender_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipient_family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    message_type VARCHAR(20) NOT NULL DEFAULT 'text', -- text, poll, image
    poll_options JSONB, -- For poll type messages
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for message poll responses
CREATE TABLE IF NOT EXISTS family_message_poll_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id UUID NOT NULL REFERENCES family_messages(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    selected_option VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(message_id, user_id)
);

-- Table for shared photo albums
CREATE TABLE IF NOT EXISTS shared_albums (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    album_name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by_family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    created_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for shared album access
CREATE TABLE IF NOT EXISTS shared_album_access (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    album_id UUID NOT NULL REFERENCES shared_albums(id) ON DELETE CASCADE,
    family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    permission_level VARCHAR(20) NOT NULL DEFAULT 'view', -- view, contribute, admin
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(album_id, family_id)
);

-- Table for shared album photos
CREATE TABLE IF NOT EXISTS shared_album_photos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    album_id UUID NOT NULL REFERENCES shared_albums(id) ON DELETE CASCADE,
    photo_url TEXT NOT NULL,
    caption TEXT,
    uploaded_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    uploaded_by_family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for photo comments
CREATE TABLE IF NOT EXISTS shared_photo_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    photo_id UUID NOT NULL REFERENCES shared_album_photos(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    comment TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for photo reactions
CREATE TABLE IF NOT EXISTS shared_photo_reactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    photo_id UUID NOT NULL REFERENCES shared_album_photos(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    reaction VARCHAR(20) NOT NULL, -- like, love, laugh, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(photo_id, user_id)
);

-- Table for shared shopping lists
CREATE TABLE IF NOT EXISTS shared_shopping_lists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    list_name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by_family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    created_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for shared shopping list access
CREATE TABLE IF NOT EXISTS shared_shopping_list_access (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    list_id UUID NOT NULL REFERENCES shared_shopping_lists(id) ON DELETE CASCADE,
    family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    permission_level VARCHAR(20) NOT NULL DEFAULT 'view', -- view, edit, admin
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(list_id, family_id)
);

-- Table for shared shopping list items
CREATE TABLE IF NOT EXISTS shared_shopping_list_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    list_id UUID NOT NULL REFERENCES shared_shopping_lists(id) ON DELETE CASCADE,
    item_name VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit VARCHAR(50),
    notes TEXT,
    is_purchased BOOLEAN NOT NULL DEFAULT FALSE,
    purchased_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    purchased_by_family_id UUID REFERENCES families(id) ON DELETE SET NULL,
    purchased_at TIMESTAMP WITH TIME ZONE,
    added_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    added_by_family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for shared emergency contacts
CREATE TABLE IF NOT EXISTS shared_emergency_contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id UUID NOT NULL REFERENCES emergency_contacts(id) ON DELETE CASCADE,
    shared_with_family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    shared_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    shared_by_family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(contact_id, shared_with_family_id)
);

-- Table for shared notes and documents
CREATE TABLE IF NOT EXISTS shared_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    content TEXT,
    document_type VARCHAR(50) NOT NULL DEFAULT 'note', -- note, recipe, document
    document_url TEXT, -- For uploaded files
    created_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_by_family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for shared document access
CREATE TABLE IF NOT EXISTS shared_document_access (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES shared_documents(id) ON DELETE CASCADE,
    family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    permission_level VARCHAR(20) NOT NULL DEFAULT 'view', -- view, edit, admin
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(document_id, family_id)
);

-- Table for document version history
CREATE TABLE IF NOT EXISTS document_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES shared_documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    modified_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    modified_by_family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for shared resource bookings
CREATE TABLE IF NOT EXISTS shared_resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resource_name VARCHAR(255) NOT NULL,
    description TEXT,
    location TEXT,
    created_by_family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    created_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for shared resource access
CREATE TABLE IF NOT EXISTS shared_resource_access (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resource_id UUID NOT NULL REFERENCES shared_resources(id) ON DELETE CASCADE,
    family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    permission_level VARCHAR(20) NOT NULL DEFAULT 'book', -- view, book, admin
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(resource_id, family_id)
);

-- Table for resource bookings
CREATE TABLE IF NOT EXISTS resource_bookings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resource_id UUID NOT NULL REFERENCES shared_resources(id) ON DELETE CASCADE,
    booked_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    booked_by_family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for family connection sharing templates
CREATE TABLE IF NOT EXISTS sharing_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by_family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    created_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    share_calendar BOOLEAN NOT NULL DEFAULT FALSE,
    share_tasks BOOLEAN NOT NULL DEFAULT FALSE,
    share_photos BOOLEAN NOT NULL DEFAULT FALSE,
    share_shopping BOOLEAN NOT NULL DEFAULT FALSE,
    share_emergency BOOLEAN NOT NULL DEFAULT FALSE,
    share_documents BOOLEAN NOT NULL DEFAULT FALSE,
    share_resources BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_family_connections_requester ON family_connections(requester_family_id);
CREATE INDEX IF NOT EXISTS idx_family_connections_target ON family_connections(target_family_id);
CREATE INDEX IF NOT EXISTS idx_shared_events_event ON shared_events(event_id);
CREATE INDEX IF NOT EXISTS idx_shared_events_family ON shared_events(shared_with_family_id);
CREATE INDEX IF NOT EXISTS idx_family_messages_sender ON family_messages(sender_family_id);
CREATE INDEX IF NOT EXISTS idx_family_messages_recipient ON family_messages(recipient_family_id);
CREATE INDEX IF NOT EXISTS idx_shared_albums_created_by ON shared_albums(created_by_family_id);
CREATE INDEX IF NOT EXISTS idx_shared_album_access_album ON shared_album_access(album_id);
CREATE INDEX IF NOT EXISTS idx_shared_album_access_family ON shared_album_access(family_id);
CREATE INDEX IF NOT EXISTS idx_shared_album_photos_album ON shared_album_photos(album_id);
CREATE INDEX IF NOT EXISTS idx_shared_shopping_lists_created_by ON shared_shopping_lists(created_by_family_id);
CREATE INDEX IF NOT EXISTS idx_shared_shopping_list_access_list ON shared_shopping_list_access(list_id);
CREATE INDEX IF NOT EXISTS idx_shared_shopping_list_access_family ON shared_shopping_list_access(family_id);
CREATE INDEX IF NOT EXISTS idx_shared_shopping_list_items_list ON shared_shopping_list_items(list_id);
CREATE INDEX IF NOT EXISTS idx_shared_emergency_contacts_contact ON shared_emergency_contacts(contact_id);
CREATE INDEX IF NOT EXISTS idx_shared_emergency_contacts_family ON shared_emergency_contacts(shared_with_family_id);
CREATE INDEX IF NOT EXISTS idx_shared_documents_created_by ON shared_documents(created_by_family_id);
CREATE INDEX IF NOT EXISTS idx_shared_document_access_document ON shared_document_access(document_id);
CREATE INDEX IF NOT EXISTS idx_shared_document_access_family ON shared_document_access(family_id);
CREATE INDEX IF NOT EXISTS idx_document_versions_document ON document_versions(document_id);
CREATE INDEX IF NOT EXISTS idx_shared_resources_created_by ON shared_resources(created_by_family_id);
CREATE INDEX IF NOT EXISTS idx_shared_resource_access_resource ON shared_resource_access(resource_id);
CREATE INDEX IF NOT EXISTS idx_shared_resource_access_family ON shared_resource_access(family_id);
CREATE INDEX IF NOT EXISTS idx_resource_bookings_resource ON resource_bookings(resource_id);
CREATE INDEX IF NOT EXISTS idx_resource_bookings_family ON resource_bookings(booked_by_family_id);
