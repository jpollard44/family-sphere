# FamilySphere Supabase Migration Guide

This document provides instructions for migrating the FamilySphere application from SQLAlchemy (SQLite) to Supabase (PostgreSQL).

## Migration Overview

The migration involves:
1. Setting up a Supabase project
2. Creating database tables in Supabase
3. Updating the application code to use Supabase
4. Migrating existing data (if any)

## Prerequisites

- Supabase account
- Supabase project URL and API key
- Python 3.8+
- Required packages: `supabase`, `python-dotenv`, `flask-login`, `werkzeug`

## Step 1: Set Up Environment Variables

Create a `.env` file in the project root with the following variables:

```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-api-key
FLASK_SECRET_KEY=your-flask-secret-key
```

## Step 2: Create Database Tables

Run the SQL script to create the necessary tables in Supabase:

1. Log in to your Supabase dashboard
2. Navigate to the SQL Editor
3. Copy and paste the contents of `supabase_tables.sql`
4. Run the script

## Step 3: Generate Sample Data (Optional)

If you want to create sample data in your Supabase database:

```bash
python setup_supabase.py
```

## Step 4: Migrate Existing Data (Optional)

If you have existing data in SQLite that you want to migrate to Supabase:

```bash
python migrate_data.py
```

## Step 5: Run the Application

Start the Flask application:

```bash
python app.py
```

The application should now be running with Supabase as the database backend.

## Code Changes Overview

The following files have been updated to use Supabase:

- `supabase_config.py`: Configuration for Supabase client
- `database.py`: Database connection setup
- `app.py`: User loader function for Flask-Login
- `routes.py`: All routes updated to use Supabase queries
- `models.py`: Model classes updated to work with Supabase

### Key Route Migrations

1. **Authentication Routes**
   - Login, registration, and logout now use Supabase queries
   - Password hashing is still handled by Werkzeug

2. **Dashboard Routes**
   - Data fetching for dashboard widgets uses Supabase queries
   - SphereBot suggestions are generated based on Supabase data

3. **Calendar/Events Routes**
   - View, add, edit, and delete events use Supabase queries
   - Event sharing functionality preserved

4. **Tasks Routes**
   - View, add, complete, edit, and delete tasks use Supabase queries
   - Task assignment and points system preserved

5. **Finances Routes**
   - View, add, edit, and delete finances use Supabase queries
   - Budget, goals, and allowances functionality preserved

6. **Chat Routes**
   - View, send, and receive messages use Supabase queries
   - Poll functionality and thread management preserved

7. **Memories Routes**
   - View, add, and share memories use Supabase queries
   - Photo storage references preserved

8. **Inventory Routes**
   - View and add inventory items use Supabase queries
   - Categorization and location tracking preserved

9. **Health Routes**
   - View and add health records use Supabase queries
   - Medication tracking and reminders preserved

10. **Emergency Routes**
    - View emergency contacts and trigger SOS use Supabase queries
    - Emergency contact management preserved

11. **Settings Routes**
    - View and update user settings use Supabase queries
    - Theme preferences and dashboard widget configuration preserved

## Supabase Data Structure

The database schema includes the following tables:

- `users`: User accounts and authentication
- `families`: Family groups
- `events`: Calendar events
- `tasks`: Tasks and chores
- `finances`: Budget, goals, and allowances
- `chats`: Family communication
- `memories`: Photos and videos
- `inventory`: Household items
- `health`: Medication tracking
- `emergency`: SOS features
- `emergency_contacts`: Emergency contact information
- `settings`: User preferences

## Troubleshooting

If you encounter issues during migration:

1. Check that your Supabase URL and API key are correct in the `.env` file
2. Verify that all tables were created successfully in Supabase
3. Check for any error messages in the console when running the application
4. Ensure all required packages are installed

For additional help, refer to the [Supabase documentation](https://supabase.io/docs) or the [Flask documentation](https://flask.palletsprojects.com/).
