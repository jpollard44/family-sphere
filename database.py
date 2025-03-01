"""
Database configuration for FamilySphere.
This module provides access to the Supabase client.
"""

from supabase_config import get_supabase_client

# Get Supabase client
db = get_supabase_client()
