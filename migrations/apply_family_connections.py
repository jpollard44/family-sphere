"""
Apply family connections migration to Supabase database.
This script reads the SQL migration file and executes it using the Supabase client.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from supabase_config import supabase

def apply_migration():
    """Apply the family connections migration."""
    try:
        # Read the migration SQL
        migration_path = Path(__file__).parent / 'family_connections.sql'
        with open(migration_path, 'r') as f:
            migration_sql = f.read()

        # Split the migration into individual statements
        statements = [s.strip() for s in migration_sql.split(';') if s.strip()]

        # Execute each statement
        for statement in statements:
            try:
                # Use the rpc function to execute raw SQL
                supabase.rpc('exec_sql', {'sql': statement}).execute()
                print(f"Successfully executed statement")
            except Exception as e:
                print(f"Error executing statement: {e}")
                print("Statement:", statement)
                raise

        print("Family connections migration completed successfully!")
        return True

    except Exception as e:
        print(f"Error applying migration: {e}")
        return False

if __name__ == '__main__':
    success = apply_migration()
    sys.exit(0 if success else 1)
