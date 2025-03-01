import os
import uuid
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
from supabase_config import get_supabase_client

# Load environment variables
load_dotenv()

# Get Supabase client
supabase = get_supabase_client()

def create_tables_manually():
    """Create tables manually by providing SQL statements."""
    print("To create the necessary tables, please run the following SQL statements in the Supabase SQL Editor:")
    
    # Chats Table
    print("\n--- Chats Table ---")
    print("""
CREATE TABLE IF NOT EXISTS chats (
    id UUID PRIMARY KEY,
    message TEXT NOT NULL,
    sender_id UUID NOT NULL,
    family_id UUID NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    thread_id UUID,
    is_poll BOOLEAN DEFAULT FALSE,
    poll_options TEXT
);
    """)
    
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

def check_tables():
    """Check if the required tables exist."""
    tables_to_check = [
        'users', 
        'families', 
        'events', 
        'tasks', 
        'finances', 
        'chats', 
        'chat_threads', 
        'memories', 
        'inventory', 
        'health', 
        'emergency', 
        'emergency_contacts', 
        'settings', 
        'poll_votes'
    ]
    existing_tables = []
    missing_tables = []
    
    for table in tables_to_check:
        try:
            response = supabase.table(table).select('count').limit(1).execute()
            existing_tables.append(table)
        except Exception as e:
            print(f"Error checking table {table}: {str(e)}")
            missing_tables.append(table)
    
    print(f"Existing tables: {', '.join(existing_tables) if existing_tables else 'None'}")
    print(f"Missing tables: {', '.join(missing_tables) if missing_tables else 'None'}")
    
    return existing_tables, missing_tables

if __name__ == "__main__":
    print("Checking tables...")
    existing_tables, missing_tables = check_tables()
    
    if missing_tables:
        print("\nSome tables are missing. You need to create them manually.")
        create_tables_manually()
    else:
        print("\nAll required tables exist. No action needed.")
