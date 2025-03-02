"""
Create the exec_sql function in Supabase for running raw SQL.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from supabase_config import supabase

def apply_migration():
    """Create the exec_sql function."""
    try:
        # Read the migration SQL
        migration_path = Path(__file__).parent / 'create_exec_sql_function.sql'
        with open(migration_path, 'r') as f:
            sql = f.read()

        # Execute the SQL directly using the REST API
        response = supabase.rest.rpc('exec_sql', {'sql': sql}).execute()
        print("Successfully created exec_sql function!")
        return True

    except Exception as e:
        print(f"Error creating exec_sql function: {e}")
        return False

if __name__ == '__main__':
    success = apply_migration()
    sys.exit(0 if success else 1)
