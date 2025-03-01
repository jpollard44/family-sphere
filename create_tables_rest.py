import os
import uuid
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://bzkhmwvzjvhehilqwlmy.supabase.co")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

if not SUPABASE_SERVICE_KEY:
    print("Error: SUPABASE_SERVICE_KEY is not set in the .env file")
    exit(1)

# Headers for Supabase REST API
headers = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def create_chat_threads_table():
    """Create the chat_threads table using REST API."""
    url = f"{SUPABASE_URL}/rest/v1/rpc/create_chat_threads_table"
    
    # SQL statement to create the table
    sql = """
    CREATE TABLE IF NOT EXISTS chat_threads (
        id UUID PRIMARY KEY,
        name TEXT NOT NULL,
        family_id UUID NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        created_by UUID NOT NULL
    );
    """
    
    # Call the RPC function
    response = requests.post(
        url,
        headers=headers,
        json={"sql": sql}
    )
    
    if response.status_code == 200:
        print("Chat threads table created successfully")
    else:
        print(f"Failed to create chat threads table: {response.text}")

def create_default_thread():
    """Create a default chat thread."""
    url = f"{SUPABASE_URL}/rest/v1/chat_threads"
    
    thread_data = {
        "id": str(uuid.uuid4()),
        "name": "General",
        "family_id": "0c0aca45-8a48-4d97-955c-e655b1f904bd",
        "created_at": datetime.now().isoformat(),
        "created_by": "2099db7d-9ec2-4dd5-bcdb-c044868b9e0d"
    }
    
    response = requests.post(
        url,
        headers=headers,
        json=thread_data
    )
    
    if response.status_code == 201:
        print(f"Default chat thread created with ID: {thread_data['id']}")
    else:
        print(f"Failed to create default chat thread: {response.text}")

def create_poll_votes_table():
    """Create the poll_votes table using REST API."""
    url = f"{SUPABASE_URL}/rest/v1/rpc/create_poll_votes_table"
    
    # SQL statement to create the table
    sql = """
    CREATE TABLE IF NOT EXISTS poll_votes (
        id UUID PRIMARY KEY,
        poll_id UUID NOT NULL,
        user_id UUID NOT NULL,
        option_index INTEGER NOT NULL,
        timestamp TIMESTAMP WITH TIME ZONE NOT NULL
    );
    """
    
    # Call the RPC function
    response = requests.post(
        url,
        headers=headers,
        json={"sql": sql}
    )
    
    if response.status_code == 200:
        print("Poll votes table created successfully")
    else:
        print(f"Failed to create poll votes table: {response.text}")

def check_table_exists(table_name):
    """Check if a table exists in the database."""
    url = f"{SUPABASE_URL}/rest/v1/{table_name}?select=count"
    
    response = requests.get(
        url,
        headers=headers
    )
    
    return response.status_code == 200

if __name__ == "__main__":
    # Check if tables exist
    if check_table_exists("chat_threads"):
        print("Chat threads table already exists")
    else:
        print("Chat threads table does not exist, creating...")
        create_chat_threads_table()
        create_default_thread()
    
    if check_table_exists("poll_votes"):
        print("Poll votes table already exists")
    else:
        print("Poll votes table does not exist, creating...")
        create_poll_votes_table()
