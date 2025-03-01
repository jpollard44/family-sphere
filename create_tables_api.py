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
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Headers for Supabase REST API
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

def create_chat_threads_table():
    """Create the chat_threads table using the REST API."""
    print("Creating chat_threads table...")
    
    # Define the SQL query
    sql = """
    CREATE TABLE IF NOT EXISTS chat_threads (
        id UUID PRIMARY KEY,
        name TEXT NOT NULL,
        family_id UUID NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        created_by UUID NOT NULL
    );
    """
    
    # Execute the SQL query
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/rpc/exec",
        headers=headers,
        json={"query": sql}
    )
    
    if response.status_code == 200:
        print("chat_threads table created successfully")
        return True
    else:
        print(f"Failed to create chat_threads table: {response.text}")
        return False

def create_default_thread():
    """Create a default chat thread."""
    print("Creating default chat thread...")
    
    thread_id = "00000000-0000-0000-0000-000000000001"
    thread_data = {
        "id": thread_id,
        "name": "General",
        "family_id": "0c0aca45-8a48-4d97-955c-e655b1f904bd",
        "created_at": datetime.now().isoformat(),
        "created_by": "2099db7d-9ec2-4dd5-bcdb-c044868b9e0d"
    }
    
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/chat_threads",
        headers=headers,
        json=thread_data
    )
    
    if response.status_code == 201:
        print(f"Default chat thread created with ID: {thread_id}")
        return True
    else:
        print(f"Failed to create default chat thread: {response.text}")
        return False

def create_poll_votes_table():
    """Create the poll_votes table using the REST API."""
    print("Creating poll_votes table...")
    
    # Define the SQL query
    sql = """
    CREATE TABLE IF NOT EXISTS poll_votes (
        id UUID PRIMARY KEY,
        poll_id UUID NOT NULL,
        user_id UUID NOT NULL,
        option_index INTEGER NOT NULL,
        timestamp TIMESTAMP WITH TIME ZONE NOT NULL
    );
    """
    
    # Execute the SQL query
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/rpc/exec",
        headers=headers,
        json={"query": sql}
    )
    
    if response.status_code == 200:
        print("poll_votes table created successfully")
        return True
    else:
        print(f"Failed to create poll_votes table: {response.text}")
        return False

def check_table_exists(table_name):
    """Check if a table exists in the database."""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/{table_name}?select=count",
        headers=headers
    )
    
    return response.status_code == 200

if __name__ == "__main__":
    print("Checking and creating tables via REST API...")
    
    # Check if tables exist
    if check_table_exists("chat_threads"):
        print("chat_threads table already exists")
    else:
        print("chat_threads table does not exist, creating...")
        if create_chat_threads_table():
            create_default_thread()
    
    if check_table_exists("poll_votes"):
        print("poll_votes table already exists")
    else:
        print("poll_votes table does not exist, creating...")
        create_poll_votes_table()
    
    print("\nDone! Please check the logs for any errors or manual steps required.")
    print("After creating these tables, restart the Flask server to apply the changes.")
