import webbrowser

# Supabase SQL Editor URL
SUPABASE_SQL_EDITOR_URL = "https://app.supabase.com/project/bzkhmwvzjvhehilqwlmy/sql"

def open_sql_editor():
    """Open the Supabase SQL Editor in the default web browser."""
    print("Opening Supabase SQL Editor...")
    webbrowser.open(SUPABASE_SQL_EDITOR_URL)
    
    print("\nPlease run the following SQL statements in the SQL Editor:")
    
    # Chat Threads Table
    print("\n--- Chat Threads Table ---")
    print("""
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
    """)
    
    # Poll Votes Table
    print("\n--- Poll Votes Table ---")
    print("""
CREATE TABLE IF NOT EXISTS poll_votes (
    id UUID PRIMARY KEY,
    poll_id UUID NOT NULL,
    user_id UUID NOT NULL,
    option_index INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
);
    """)
    
    print("\nAfter creating these tables, restart the Flask server to apply the changes.")

if __name__ == "__main__":
    open_sql_editor()
