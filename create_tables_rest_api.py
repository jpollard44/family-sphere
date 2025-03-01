import os
import requests
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://bzkhmwvzjvhehilqwlmy.supabase.co")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ6a2htd3Z6anZoZWhpbHF3bG15Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDA3ODQ2MzcsImV4cCI6MjA1NjM2MDYzN30.fC04eWawBRQAMOyC83c1sv55AU9qzqCuPIuKwiRktoY")

# Headers for Supabase REST API
headers = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def create_chat_threads_table():
    """Try to create the chat_threads table using the REST API."""
    print("Attempting to create chat_threads table...")
    
    # First, check if the table exists
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/chat_threads?select=count",
            headers=headers
        )
        
        if response.status_code == 200:
            print("chat_threads table already exists!")
            return True
    except Exception as e:
        print(f"Error checking if chat_threads table exists: {e}")
    
    # Table doesn't exist, try to create it
    print("Table doesn't exist. Please create it manually in the Supabase dashboard.")
    print("SQL to create the table:")
    print("""
CREATE TABLE chat_threads (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    family_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_by UUID NOT NULL
);
    """)
    
    return False

def create_default_thread():
    """Create a default chat thread."""
    print("Attempting to create a default chat thread...")
    
    thread_data = {
        "id": str(uuid.uuid4()),
        "name": "General",
        "family_id": "0c0aca45-8a48-4d97-955c-e655b1f904bd",
        "created_at": datetime.now().isoformat(),
        "created_by": "2099db7d-9ec2-4dd5-bcdb-c044868b9e0d"
    }
    
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/chat_threads",
            headers=headers,
            json=thread_data
        )
        
        if response.status_code == 201:
            print(f"Default chat thread created with ID: {thread_data['id']}")
            return True
        else:
            print(f"Failed to create default chat thread: {response.text}")
            return False
    except Exception as e:
        print(f"Error creating default chat thread: {e}")
        return False

def create_poll_votes_table():
    """Try to create the poll_votes table using the REST API."""
    print("Attempting to create poll_votes table...")
    
    # First, check if the table exists
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/poll_votes?select=count",
            headers=headers
        )
        
        if response.status_code == 200:
            print("poll_votes table already exists!")
            return True
    except Exception as e:
        print(f"Error checking if poll_votes table exists: {e}")
    
    # Table doesn't exist, try to create it
    print("Table doesn't exist. Please create it manually in the Supabase dashboard.")
    print("SQL to create the table:")
    print("""
CREATE TABLE poll_votes (
    id UUID PRIMARY KEY,
    poll_id UUID NOT NULL,
    user_id UUID NOT NULL,
    option_index INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
);
    """)
    
    return False

if __name__ == "__main__":
    print("Checking and creating tables via REST API...")
    
    # Try to create chat_threads table
    chat_threads_exists = create_chat_threads_table()
    
    # If the table exists or was created, create a default thread
    if chat_threads_exists:
        create_default_thread()
    
    # Try to create poll_votes table
    create_poll_votes_table()
    
    print("\nDone! Please check the logs for any errors or manual steps required.")
    print("After creating these tables, restart the Flask server to apply the changes.")
