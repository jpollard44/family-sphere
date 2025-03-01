"""
Setup Supabase sample data for FamilySphere application.
This script creates sample data in the Supabase tables.

Note: Before running this script, you need to create the tables in Supabase.
You can use the SQL script in supabase_tables.sql by copying and pasting it
into the Supabase SQL editor in the dashboard.
"""

from supabase_config import get_supabase_client
import uuid
from werkzeug.security import generate_password_hash

def create_sample_data():
    """Create sample data in Supabase tables."""
    supabase = get_supabase_client()
    
    print("Checking if sample data exists...")
    
    # Check if users table has data
    response = supabase.table('users').select('*', count='exact').limit(1).execute()
    
    if hasattr(response, 'count') and response.count > 0:
        print("Sample data already exists. Skipping creation.")
        return
    
    print("Creating sample data...")
    
    try:
        # Create a sample family
        family_id = str(uuid.uuid4())
        supabase.table('families').insert({
            'id': family_id,
            'name': 'Sample Family',
            'code': 'SAMPLE123'
        }).execute()
        print("Created sample family")
        
        # Create a sample user
        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash('password')
        supabase.table('users').insert({
            'id': user_id,
            'username': 'admin',
            'password_hash': password_hash,
            'role': 'Admin',
            'family_id': family_id
        }).execute()
        print("Created sample user")
        
        # Create settings for the user
        supabase.table('settings').insert({
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'theme': 'light',
            'notifications': True,
            'spherebot_enabled': True,
            'location_sharing': False,
            'dashboard_widgets': 'calendar,tasks,chat,finances'
        }).execute()
        print("Created user settings")
        
        # Create a sample event
        supabase.table('events').insert({
            'id': str(uuid.uuid4()),
            'title': 'Family Dinner',
            'date': '2025-03-01',
            'time': '18:00:00',
            'location': 'Home',
            'description': 'Weekly family dinner',
            'family_id': family_id,
            'created_by': user_id
        }).execute()
        print("Created sample event")
        
        # Create a sample task
        supabase.table('tasks').insert({
            'id': str(uuid.uuid4()),
            'title': 'Clean the kitchen',
            'description': 'Wash dishes and clean counters',
            'due_date': '2025-03-02',
            'assigned_to': user_id,
            'points': 10,
            'status': 'Pending',
            'family_id': family_id
        }).execute()
        print("Created sample task")
        
        # Create a sample chat message
        supabase.table('chats').insert({
            'id': str(uuid.uuid4()),
            'message': 'Welcome to FamilySphere!',
            'sender_id': user_id,
            'family_id': family_id
        }).execute()
        print("Created sample chat message")
        
        # Create a sample finance entry
        supabase.table('finances').insert({
            'id': str(uuid.uuid4()),
            'type': 'Budget',
            'title': 'Grocery Budget',
            'description': 'Monthly grocery budget',
            'amount': 500.00,
            'target_amount': 500.00,
            'family_id': family_id
        }).execute()
        print("Created sample finance entry")
        
        print("Sample data created successfully!")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        
        # Check if tables exist
        print("\nChecking if tables exist in Supabase...")
        tables = ['users', 'families', 'events', 'tasks', 'finances', 'chats', 'memories', 
                 'inventory', 'health', 'emergency', 'emergency_contacts', 'settings']
        
        for table in tables:
            try:
                supabase.table(table).select('*', count='exact').limit(1).execute()
                print(f"✓ Table '{table}' exists")
            except Exception:
                print(f"✗ Table '{table}' does not exist")
        
        print("\nPlease create the tables first by running the SQL in supabase_tables.sql")
        print("in the Supabase SQL editor at https://bzkhmwvzjvhehilqwlmy.supabase.co")

if __name__ == "__main__":
    create_sample_data()
