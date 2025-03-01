import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://bzkhmwvzjvhehilqwlmy.supabase.co")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ6a2htd3Z6anZoZWhpbHF3bG15Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDA3ODQ2MzcsImV4cCI6MjA1NjM2MDYzN30.fC04eWawBRQAMOyC83c1sv55AU9qzqCuPIuKwiRktoY")

# Print environment variables for debugging
print(f"SUPABASE_URL: {SUPABASE_URL}")
print(f"SUPABASE_ANON_KEY: {SUPABASE_ANON_KEY[:10]}...")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def get_supabase_client():
    """Returns the Supabase client instance."""
    return supabase
