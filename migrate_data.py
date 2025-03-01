#!/usr/bin/env python3
"""
Data Migration Script for FamilySphere
Transfers data from SQLite to Supabase
"""

import os
import uuid
import sqlite3
from dotenv import load_dotenv
from database import db
from werkzeug.security import generate_password_hash

# Load environment variables
load_dotenv()

def migrate_data():
    """Migrate data from SQLite to Supabase."""
    print("Starting data migration from SQLite to Supabase...")
    
    # Connect to SQLite database
    try:
        sqlite_conn = sqlite3.connect('familysphere.db')
        sqlite_conn.row_factory = sqlite3.Row
        cursor = sqlite_conn.cursor()
        print("Connected to SQLite database.")
    except sqlite3.Error as e:
        print(f"Error connecting to SQLite database: {e}")
        return
    
    # Migrate families
    try:
        print("Migrating families...")
        cursor.execute("SELECT * FROM family")
        families = cursor.fetchall()
        
        for family in families:
            family_id = str(uuid.uuid4())
            family_data = {
                'id': family_id,
                'name': family['name'],
                'code': family['code']
            }
            
            # Map old family ID to new UUID
            family_id_map[family['id']] = family_id
            
            # Insert into Supabase
            db.table('families').insert(family_data).execute()
        
        print(f"Migrated {len(families)} families.")
    except Exception as e:
        print(f"Error migrating families: {e}")
    
    # Migrate users
    try:
        print("Migrating users...")
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()
        
        for user in users:
            user_id = str(uuid.uuid4())
            
            # Map old family ID to new UUID
            family_id = family_id_map.get(user['family_id'])
            if not family_id:
                print(f"Warning: Family ID {user['family_id']} not found for user {user['username']}")
                continue
            
            user_data = {
                'id': user_id,
                'username': user['username'],
                'password_hash': user['password_hash'],
                'role': user['role'],
                'family_id': family_id
            }
            
            # Map old user ID to new UUID
            user_id_map[user['id']] = user_id
            
            # Insert into Supabase
            db.table('users').insert(user_data).execute()
        
        print(f"Migrated {len(users)} users.")
    except Exception as e:
        print(f"Error migrating users: {e}")
    
    # Migrate events
    try:
        print("Migrating events...")
        cursor.execute("SELECT * FROM event")
        events = cursor.fetchall()
        
        for event in events:
            event_id = str(uuid.uuid4())
            
            # Map old family ID to new UUID
            family_id = family_id_map.get(event['family_id'])
            if not family_id:
                print(f"Warning: Family ID {event['family_id']} not found for event {event['title']}")
                continue
            
            # Map old created_by ID to new UUID
            created_by = user_id_map.get(event['created_by'])
            
            event_data = {
                'id': event_id,
                'title': event['title'],
                'date': event['date'],
                'time': event['time'],
                'location': event.get('location', ''),
                'description': event.get('description', ''),
                'family_id': family_id,
                'created_by': created_by
            }
            
            # Insert into Supabase
            db.table('events').insert(event_data).execute()
        
        print(f"Migrated {len(events)} events.")
    except Exception as e:
        print(f"Error migrating events: {e}")
    
    # Migrate tasks
    try:
        print("Migrating tasks...")
        cursor.execute("SELECT * FROM task")
        tasks = cursor.fetchall()
        
        for task in tasks:
            task_id = str(uuid.uuid4())
            
            # Map old family ID to new UUID
            family_id = family_id_map.get(task['family_id'])
            if not family_id:
                print(f"Warning: Family ID {task['family_id']} not found for task {task['title']}")
                continue
            
            # Map old assigned_to ID to new UUID
            assigned_to = user_id_map.get(task['assigned_to'])
            
            task_data = {
                'id': task_id,
                'title': task['title'],
                'description': task.get('description', ''),
                'due_date': task['due_date'],
                'assigned_to': assigned_to,
                'points': task.get('points', 0),
                'status': task.get('status', 'Pending'),
                'family_id': family_id
            }
            
            # Insert into Supabase
            db.table('tasks').insert(task_data).execute()
        
        print(f"Migrated {len(tasks)} tasks.")
    except Exception as e:
        print(f"Error migrating tasks: {e}")
    
    # Migrate finances
    try:
        print("Migrating finances...")
        cursor.execute("SELECT * FROM finance")
        finances = cursor.fetchall()
        
        for finance in finances:
            finance_id = str(uuid.uuid4())
            
            # Map old family ID to new UUID
            family_id = family_id_map.get(finance['family_id'])
            if not family_id:
                print(f"Warning: Family ID {finance['family_id']} not found for finance {finance['title']}")
                continue
            
            finance_data = {
                'id': finance_id,
                'type': finance['type'],
                'title': finance['title'],
                'description': finance.get('description', ''),
                'amount': finance['amount'],
                'target_amount': finance.get('target_amount', 0),
                'due_date': finance.get('due_date'),
                'family_id': family_id
            }
            
            # Insert into Supabase
            db.table('finances').insert(finance_data).execute()
        
        print(f"Migrated {len(finances)} finances.")
    except Exception as e:
        print(f"Error migrating finances: {e}")
    
    # Migrate chats
    try:
        print("Migrating chats...")
        cursor.execute("SELECT * FROM chat")
        chats = cursor.fetchall()
        
        for chat in chats:
            chat_id = str(uuid.uuid4())
            
            # Map old family ID to new UUID
            family_id = family_id_map.get(chat['family_id'])
            if not family_id:
                print(f"Warning: Family ID {chat['family_id']} not found for chat message")
                continue
            
            # Map old sender_id ID to new UUID
            sender_id = user_id_map.get(chat['sender_id'])
            
            chat_data = {
                'id': chat_id,
                'message': chat['message'],
                'sender_id': sender_id,
                'family_id': family_id,
                'timestamp': chat['timestamp']
            }
            
            # Insert into Supabase
            db.table('chats').insert(chat_data).execute()
        
        print(f"Migrated {len(chats)} chat messages.")
    except Exception as e:
        print(f"Error migrating chats: {e}")
    
    # Migrate settings
    try:
        print("Migrating settings...")
        cursor.execute("SELECT * FROM settings")
        settings_list = cursor.fetchall()
        
        for settings in settings_list:
            settings_id = str(uuid.uuid4())
            
            # Map old user ID to new UUID
            user_id = user_id_map.get(settings['user_id'])
            if not user_id:
                print(f"Warning: User ID {settings['user_id']} not found for settings")
                continue
            
            settings_data = {
                'id': settings_id,
                'user_id': user_id,
                'theme': settings.get('theme', 'light'),
                'notifications': settings.get('notifications', True),
                'spherebot_enabled': settings.get('spherebot_enabled', True),
                'location_sharing': settings.get('location_sharing', False),
                'dashboard_widgets': settings.get('dashboard_widgets', 'calendar,tasks,chat,finances')
            }
            
            # Insert into Supabase
            db.table('settings').insert(settings_data).execute()
        
        print(f"Migrated {len(settings_list)} settings.")
    except Exception as e:
        print(f"Error migrating settings: {e}")
    
    # Close SQLite connection
    sqlite_conn.close()
    print("Data migration completed.")

if __name__ == "__main__":
    # Initialize ID mapping dictionaries
    family_id_map = {}  # Maps old SQLite IDs to new UUIDs
    user_id_map = {}    # Maps old SQLite IDs to new UUIDs
    
    # Run migration
    migrate_data()
