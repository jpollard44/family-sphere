-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    family_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create families table
CREATE TABLE IF NOT EXISTS families (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    code TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create events table
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    date DATE NOT NULL,
    time TIME,
    location TEXT,
    description TEXT,
    family_id UUID NOT NULL,
    created_by UUID,
    shared_with TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT,
    due_date DATE NOT NULL,
    assigned_to UUID,
    points INTEGER DEFAULT 0,
    status TEXT DEFAULT 'Pending',
    family_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create finances table
CREATE TABLE IF NOT EXISTS finances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    amount NUMERIC,
    target_amount NUMERIC,
    due_date DATE,
    assigned_to UUID,
    family_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create chats table
CREATE TABLE IF NOT EXISTS chats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message TEXT NOT NULL,
    sender_id UUID NOT NULL,
    family_id UUID NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    thread_id UUID,
    is_poll BOOLEAN DEFAULT FALSE,
    poll_options TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create memories table
CREATE TABLE IF NOT EXISTS memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT,
    photo_url TEXT NOT NULL,
    description TEXT,
    date DATE,
    family_id UUID NOT NULL,
    created_by UUID,
    shared_with TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create inventory table
CREATE TABLE IF NOT EXISTS inventory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_name TEXT NOT NULL,
    description TEXT,
    quantity INTEGER NOT NULL,
    category TEXT,
    location TEXT,
    notes TEXT,
    restock_threshold INTEGER,
    family_id UUID NOT NULL,
    is_borrowed BOOLEAN DEFAULT FALSE,
    borrowed_by TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create health table
CREATE TABLE IF NOT EXISTS health (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    medication TEXT NOT NULL,
    dosage TEXT,
    frequency TEXT,
    reminder_time TIME,
    start_date DATE,
    end_date DATE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create emergency table
CREATE TABLE IF NOT EXISTS emergency (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    family_id UUID NOT NULL,
    location TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sos_status BOOLEAN DEFAULT FALSE,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_by UUID,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create emergency_contacts table
CREATE TABLE IF NOT EXISTS emergency_contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    relation TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    notes TEXT,
    is_primary BOOLEAN DEFAULT FALSE,
    family_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create settings table
CREATE TABLE IF NOT EXISTS settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    theme TEXT,
    notifications BOOLEAN DEFAULT TRUE,
    spherebot_enabled BOOLEAN DEFAULT TRUE,
    location_sharing BOOLEAN DEFAULT FALSE,
    dashboard_widgets TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add foreign key constraints
ALTER TABLE users ADD CONSTRAINT fk_family FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE SET NULL;
ALTER TABLE events ADD CONSTRAINT fk_event_family FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE;
ALTER TABLE events ADD CONSTRAINT fk_event_creator FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE tasks ADD CONSTRAINT fk_task_family FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE;
ALTER TABLE tasks ADD CONSTRAINT fk_task_assignee FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE finances ADD CONSTRAINT fk_finance_family FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE;
ALTER TABLE finances ADD CONSTRAINT fk_finance_assignee FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE chats ADD CONSTRAINT fk_chat_family FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE;
ALTER TABLE chats ADD CONSTRAINT fk_chat_sender FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE memories ADD CONSTRAINT fk_memory_family FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE;
ALTER TABLE memories ADD CONSTRAINT fk_memory_creator FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE inventory ADD CONSTRAINT fk_inventory_family FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE;
ALTER TABLE health ADD CONSTRAINT fk_health_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE emergency ADD CONSTRAINT fk_emergency_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE emergency ADD CONSTRAINT fk_emergency_family FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE;
ALTER TABLE emergency ADD CONSTRAINT fk_emergency_resolver FOREIGN KEY (resolved_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE emergency_contacts ADD CONSTRAINT fk_emergency_contact_family FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE;
ALTER TABLE settings ADD CONSTRAINT fk_settings_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Create indexes for better performance
CREATE INDEX idx_users_family ON users(family_id);
CREATE INDEX idx_events_family ON events(family_id);
CREATE INDEX idx_events_date ON events(date);
CREATE INDEX idx_tasks_family ON tasks(family_id);
CREATE INDEX idx_tasks_assigned ON tasks(assigned_to);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_finances_family ON finances(family_id);
CREATE INDEX idx_chats_family ON chats(family_id);
CREATE INDEX idx_chats_sender ON chats(sender_id);
CREATE INDEX idx_memories_family ON memories(family_id);
CREATE INDEX idx_inventory_family ON inventory(family_id);
CREATE INDEX idx_health_user ON health(user_id);
CREATE INDEX idx_emergency_user ON emergency(user_id);
CREATE INDEX idx_emergency_family ON emergency(family_id);
CREATE INDEX idx_emergency_contacts_family ON emergency_contacts(family_id);
CREATE INDEX idx_settings_user ON settings(user_id);
