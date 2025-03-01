-- Create chat_threads table
CREATE TABLE IF NOT EXISTS chat_threads (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    family_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_by UUID NOT NULL
);

-- Create a default thread
INSERT INTO chat_threads (id, name, family_id, created_at, created_by)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'General',
    '0c0aca45-8a48-4d97-955c-e655b1f904bd',
    NOW(),
    '2099db7d-9ec2-4dd5-bcdb-c044868b9e0d'
);

-- Create poll_votes table
CREATE TABLE IF NOT EXISTS poll_votes (
    id UUID PRIMARY KEY,
    poll_id UUID NOT NULL,
    user_id UUID NOT NULL,
    option_index INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
);
