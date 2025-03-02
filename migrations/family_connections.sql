-- Family Connections Tables

-- Table for storing family connections
CREATE TABLE IF NOT EXISTS family_connections (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    family_id UUID REFERENCES families(id) ON DELETE CASCADE,
    connected_family_id UUID REFERENCES families(id) ON DELETE CASCADE,
    connected_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    shared_features TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(family_id, connected_family_id)
);

-- Enable Row Level Security
ALTER TABLE family_connections ENABLE ROW LEVEL SECURITY;

-- Policies for family_connections
CREATE POLICY "Users can view their family's connections"
    ON family_connections FOR SELECT
    USING (
        auth.uid() IN (
            SELECT user_id FROM users 
            WHERE family_id = family_connections.family_id 
            OR family_id = family_connections.connected_family_id
        )
    );

CREATE POLICY "Users can create connections for their family"
    ON family_connections FOR INSERT
    WITH CHECK (
        auth.uid() IN (
            SELECT user_id FROM users WHERE family_id = family_connections.family_id
        )
    );

CREATE POLICY "Users can update their family's connections"
    ON family_connections FOR UPDATE
    USING (
        auth.uid() IN (
            SELECT user_id FROM users WHERE family_id = family_connections.family_id
        )
    );

CREATE POLICY "Users can delete their family's connections"
    ON family_connections FOR DELETE
    USING (
        auth.uid() IN (
            SELECT user_id FROM users WHERE family_id = family_connections.family_id
        )
    );

-- Table for storing connection requests
CREATE TABLE IF NOT EXISTS family_connection_requests (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    requesting_family_id UUID REFERENCES families(id) ON DELETE CASCADE,
    requested_family_id UUID REFERENCES families(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('pending', 'accepted', 'rejected', 'cancelled')),
    request_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    response_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_pending_request UNIQUE NULLS NOT DISTINCT (requesting_family_id, requested_family_id) 
    WHERE status = 'pending'
);

-- Enable Row Level Security
ALTER TABLE family_connection_requests ENABLE ROW LEVEL SECURITY;

-- Policies for family_connection_requests
CREATE POLICY "Users can view their family's requests"
    ON family_connection_requests FOR SELECT
    USING (
        auth.uid() IN (
            SELECT user_id FROM users 
            WHERE family_id = family_connection_requests.requesting_family_id 
            OR family_id = family_connection_requests.requested_family_id
        )
    );

CREATE POLICY "Users can create requests for their family"
    ON family_connection_requests FOR INSERT
    WITH CHECK (
        auth.uid() IN (
            SELECT user_id FROM users 
            WHERE family_id = family_connection_requests.requesting_family_id
        )
    );

CREATE POLICY "Users can update their family's requests"
    ON family_connection_requests FOR UPDATE
    USING (
        auth.uid() IN (
            SELECT user_id FROM users 
            WHERE family_id = family_connection_requests.requesting_family_id 
            OR family_id = family_connection_requests.requested_family_id
        )
    );

-- Add shared_with column to existing tables if not exists
DO $$ 
BEGIN
    -- Add to events table
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'events' AND column_name = 'shared_with'
    ) THEN
        ALTER TABLE events ADD COLUMN shared_with UUID[] DEFAULT '{}';
    END IF;

    -- Add to tasks table
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tasks' AND column_name = 'shared_with'
    ) THEN
        ALTER TABLE tasks ADD COLUMN shared_with UUID[] DEFAULT '{}';
    END IF;

    -- Add to photos table
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'photos' AND column_name = 'shared_with'
    ) THEN
        ALTER TABLE photos ADD COLUMN shared_with UUID[] DEFAULT '{}';
    END IF;

    -- Add to shopping_lists table
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'shopping_lists' AND column_name = 'shared_with'
    ) THEN
        ALTER TABLE shopping_lists ADD COLUMN shared_with UUID[] DEFAULT '{}';
    END IF;

    -- Add to emergency_contacts table
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'emergency_contacts' AND column_name = 'shared_with'
    ) THEN
        ALTER TABLE emergency_contacts ADD COLUMN shared_with UUID[] DEFAULT '{}';
    END IF;
END $$;

-- Create or update RLS policies for shared items
DO $$ 
DECLARE
    table_names text[] := ARRAY['events', 'tasks', 'photos', 'shopping_lists', 'emergency_contacts'];
    table_name text;
BEGIN
    FOREACH table_name IN ARRAY table_names
    LOOP
        -- Drop existing policies if they exist
        EXECUTE format('DROP POLICY IF EXISTS "Users can view shared items" ON %I', table_name);
        
        -- Create new policy for viewing shared items
        EXECUTE format(
            'CREATE POLICY "Users can view shared items" ON %I
            FOR SELECT USING (
                auth.uid() IN (
                    SELECT user_id FROM users WHERE family_id = ANY(%I.shared_with)
                )
            )', 
            table_name,
            table_name
        );
    END LOOP;
END $$;

-- Create function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updating timestamps
DO $$ 
DECLARE
    table_names text[] := ARRAY['family_connections', 'family_connection_requests'];
    table_name text;
BEGIN
    FOREACH table_name IN ARRAY table_names
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS update_timestamp ON %I;
            CREATE TRIGGER update_timestamp
                BEFORE UPDATE ON %I
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        ', table_name, table_name);
    END LOOP;
END $$;

-- Enable realtime for family connections tables
ALTER PUBLICATION supabase_realtime ADD TABLE family_connections;
ALTER PUBLICATION supabase_realtime ADD TABLE family_connection_requests;
