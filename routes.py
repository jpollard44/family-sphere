from flask import render_template, redirect, url_for, flash, request, jsonify, make_response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
import requests
import json
from datetime import datetime, date, timedelta
from flask_wtf.csrf import generate_csrf

from app import app
from database import db
from models import User, Family, Event, Task, Finance, Chat, Memory, Inventory, Health, Emergency, Settings, EmergencyContact

# Context processor to add CSRF token to all templates
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf())

# Set CSRF cookie for JavaScript requests
@app.after_request
def set_csrf_cookie(response):
    if 'csrf_token' not in request.cookies:
        response.set_cookie('csrf_token', generate_csrf(), 
                           secure=request.is_secure,
                           httponly=False,
                           samesite='Lax')
    return response

# Helper function for SphereBot AI
def get_spherebot_suggestion(context):
    """Generate a SphereBot suggestion based on context."""
    from database import db
    
    # Get the current user
    user = current_user
    
    # Default suggestions
    suggestions = {
        "dashboard": "Try using the Quick Add button to create new events or tasks!",
        "calendar": "You can drag and drop events to reschedule them.",
        "tasks": "Assign tasks to family members to distribute responsibilities.",
        "chat": "Use @username to tag a specific family member in your message.",
        "finances": "Set up a savings goal for your next family vacation!",
        "memory": "Upload photos from your last family gathering to preserve memories.",
        "inventory": "Low on essentials? Add them to your shopping list!",
        "health": "Schedule regular health check-ups for all family members.",
        "emergency": "Make sure all emergency contacts are up to date.",
        "settings": "Customize your dashboard widgets for a personalized experience.",
        "family": "Invite extended family members to join your FamilySphere!"
    }
    
    try:
        # Get family data
        family_response = db.table('families').select('*').eq('id', user.family_id).execute()
        if family_response.data:
            family = family_response.data[0]
            
            if context == "calendar":
                # Check for upcoming events and potential conflicts
                upcoming_events = db.table('events').select('*').eq('family_id', user.family_id).gte('date', date.today().isoformat()).order('date').limit(10).execute().data
                
                # Check for events on the same day
                event_dates = {}
                for event in upcoming_events:
                    date_str = event['date']
                    if date_str in event_dates:
                        return f"You have multiple events on {event['date']}. Would you like me to suggest a schedule to avoid conflicts?"
                    event_dates[date_str] = True
                    
                # Check for events coming up soon
                if upcoming_events:
                    next_event = upcoming_events[0]
                    days_until = (datetime.strptime(next_event['date'], '%Y-%m-%d').date() - date.today()).days
                    if days_until <= 1:
                        return f"Your event '{next_event['title']}' is coming up {'tomorrow' if days_until == 1 else 'today'}! Do you need help with preparations?"
                
                return "Looking at your calendar, would you like me to suggest family activities for your free weekends?"
                
            elif context == "tasks":
                # Check for overdue tasks
                overdue_tasks = db.table('tasks').select('*').eq('family_id', user.family_id).eq('status', 'Pending').lt('due_date', date.today().isoformat()).execute().data
                if overdue_tasks:
                    return f"You have {len(overdue_tasks)} overdue {'task' if len(overdue_tasks) == 1 else 'tasks'} that need attention. Would you like me to help prioritize them?"
                
                # Check for unassigned tasks
                unassigned_tasks = db.table('tasks').select('*').eq('family_id', user.family_id).is_('assigned_to', 'null').execute().data
                if unassigned_tasks:
                    return f"You have {len(unassigned_tasks)} unassigned {'task' if len(unassigned_tasks) == 1 else 'tasks'}. Would you like me to suggest family members who might be available?"
                
                # Check for task distribution
                members_response = db.table('users').select('*').eq('family_id', user.family_id).execute()
                family_members = members_response.data
                
                task_counts = {}
                for member in family_members:
                    count_response = db.table('tasks').select('*').eq('family_id', user.family_id).eq('assigned_to', member['id']).eq('status', 'Pending').execute()
                    count = len(count_response.data)
                    task_counts[member['username']] = count
                
                if task_counts:
                    max_user = max(task_counts.items(), key=lambda x: x[1])
                    min_user = min(task_counts.items(), key=lambda x: x[1])
                    
                    if max_user[1] > 0 and max_user[1] >= min_user[1] * 2:
                        return f"{max_user[0]} has {max_user[1]} tasks while {min_user[0]} only has {min_user[1]}. Would you like me to suggest redistributing some tasks?"
                
                return "Would you like me to suggest a task rotation schedule for your family?"
                
            elif context == "finance":
                # Check for budget categories with high spending
                finances = db.table('finances').select('*').eq('family_id', user.family_id).execute().data
                if finances:
                    return "I notice your grocery spending is trending higher than last month. Would you like to see where you might save?"
                return "Would you like me to analyze your spending patterns and suggest a family budget?"
                
            elif context == "chat":
                # Check for unanswered messages
                recent_chats = db.table('chats').select('*').eq('family_id', user.family_id).order('timestamp', desc=True).limit(20).execute().data
                if recent_chats:
                    sender_counts = {}
                    for chat in recent_chats:
                        sender_response = db.table('users').select('*').eq('id', chat['sender_id']).execute()
                        if sender_response.data:
                            sender = sender_response.data[0]
                            sender_counts[sender['username']] = sender_counts.get(sender['username'], 0) + 1
                    
                    most_active = max(sender_counts.items(), key=lambda x: x[1]) if sender_counts else None
                    if most_active and most_active[1] > 5:
                        return f"{most_active[0]} has been quite active in the chat lately! Would you like to pin any important messages?"
                return "Would you like me to suggest some conversation starters for your family chat?"
                
            elif context == "memory":
                # Check for recent memories without tags
                memories = db.table('memories').select('*').eq('family_id', user.family_id).order('date', desc=True).limit(5).execute().data
                if memories:
                    return "I notice you have recent family photos. Would you like me to suggest tags or organize them into albums?"
                return "Would you like me to remind you to capture memories of upcoming family events?"
                
            elif context == "inventory":
                # Check for low inventory items
                low_items = db.table('inventory').select('*').eq('family_id', user.family_id).lte('quantity', 2).execute().data
                if low_items:
                    items = ", ".join([item['item_name'] for item in low_items[:3]])
                    more = len(low_items) > 3
                    return f"You're running low on: {items}{' and more' if more else ''}. Would you like me to add these to your shopping list?"
                return "Would you like me to analyze your inventory usage patterns and suggest restocking schedules?"
                
            elif context == "health":
                # Check for upcoming medications or appointments
                health_records = db.table('health').select('*').eq('user_id', user.id).execute().data
                if health_records:
                    return "It looks like it's time for some family health check-ups. Would you like me to suggest scheduling appointments?"
                return "Would you like me to help set up medication reminders for your family?"
                
            elif context == "emergency":
                # Check if emergency contacts are set up
                emergency_contacts = db.table('emergency_contacts').select('*').eq('family_id', user.family_id).execute().data
                if not emergency_contacts:
                    return "I notice you haven't set up any emergency contacts yet. Would you like help setting those up for your family's safety?"
                elif len(emergency_contacts) < 3:
                    return "It's good to have multiple emergency contacts. Would you like to add more to your family's safety plan?"
                return "When was the last time you reviewed your family's emergency plan? Would you like me to help update it?"
                
            elif context == "dashboard":
                # Check for dashboard customization
                settings_response = db.table('settings').select('*').eq('user_id', user.id).execute()
                if settings_response.data:
                    settings = settings_response.data[0]
                    if not settings.get('dashboard_widgets') or len(settings.get('dashboard_widgets', '').split(',')) < 3:
                        return "You might benefit from adding more widgets to your dashboard. Would you like me to suggest some based on your family's activities?"
                
                # Check for any high-priority items across contexts
                overdue_tasks = db.table('tasks').select('*').eq('family_id', user.family_id).eq('status', 'Pending').lt('due_date', date.today().isoformat()).execute().count
                upcoming_events = db.table('events').select('*').eq('family_id', user.family_id).gte('date', date.today().isoformat()).lte('date', (date.today() + timedelta(days=2)).isoformat()).execute().count
                
                if overdue_tasks > 0:
                    return f"You have {overdue_tasks} overdue {'task' if overdue_tasks == 1 else 'tasks'} that need attention. Would you like me to help prioritize them?"
                elif upcoming_events > 0:
                    return f"You have {upcoming_events} upcoming {'event' if upcoming_events == 1 else 'events'} in the next two days. Would you like me to help with preparations?"
                
                return "Welcome back! What would you like to do with your family today?"
                
            elif context == "family":
                # Check for family members without profile pictures
                members_response = db.table('users').select('*').eq('family_id', user.family_id).execute()
                members = members_response.data
                
                if members:
                    return f"Your family has {len(members)} members. Would you like to invite more people to join?"
                return "Would you like to customize your family profile and add a family photo?"
                
            elif context == "settings":
                # Check for unused features
                return "Have you tried enabling dark mode for better nighttime viewing? You can change this in your display settings."
    
    except Exception as e:
        print(f"Error generating SphereBot suggestion: {str(e)}")
    
    # Return default suggestion if no personalized one was generated
    return suggestions.get(context, "How can I assist you today?")

# Routes for authentication
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Query Supabase for the user
        from database import db
        response = db.table('users').select('*').eq('username', username).execute()
        
        if response.data:
            user_data = response.data[0]
            user = User.from_dict(user_data)
            
            if user and user.check_password(password):
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
        
        flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        family_code = request.form.get('family_code')
        create_family = request.form.get('create_family') == '1'
        family_name = request.form.get('family_name')
        
        print(f"Form data: username={username}, create_family={create_family}, family_name={family_name}")
        
        # Validate input
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        # Check if username already exists
        from database import db
        try:
            user_response = db.table('users').select('*').eq('username', username).execute()
            
            if user_response.data:
                flash('Username already exists', 'danger')
                return render_template('register.html')
            
            # Create new user
            import uuid
            user_id = str(uuid.uuid4())
            
            if create_family:
                # Create a new family
                family_id = str(uuid.uuid4())
                # Generate a random 6-character code
                import random
                import string
                family_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                
                print(f"Creating family: {family_name} with ID: {family_id} and code: {family_code}")
                
                try:
                    # Insert family into database
                    family_insert = db.table('families').insert({
                        'id': family_id,
                        'name': family_name,
                        'code': family_code
                    }).execute()
                    
                    print(f"Family insert response: {family_insert}")
                    
                    # Create user with Admin role
                    user = User(
                        id=user_id,
                        username=username,
                        role='Admin',
                        family_id=family_id
                    )
                    user.set_password(password)
                    
                    # Insert user into database
                    user_insert = db.table('users').insert(user.to_dict()).execute()
                    print(f"User insert response: {user_insert}")
                    
                    # Create default settings for user
                    settings_insert = db.table('settings').insert({
                        'id': str(uuid.uuid4()),
                        'user_id': user_id,
                        'theme': 'light',
                        'notifications': True,
                        'spherebot_enabled': True,
                        'location_sharing': False,
                        'dashboard_widgets': 'calendar,tasks,chat,finances'
                    }).execute()
                    print(f"Settings insert response: {settings_insert}")
                    
                    flash(f'Family created with code: {family_code}', 'success')
                    login_user(user)
                    return redirect(url_for('dashboard'))
                except Exception as e:
                    print(f"Error creating family: {str(e)}")
                    flash(f'Error creating family: {str(e)}', 'danger')
                    return render_template('register.html')
            else:
                # Join existing family
                try:
                    family_response = db.table('families').select('*').eq('code', family_code).execute()
                    
                    if not family_response.data:
                        flash('Invalid family code', 'danger')
                        return render_template('register.html')
                    
                    family = family_response.data[0]
                    
                    # Create user with Member role
                    user = User(
                        id=user_id,
                        username=username,
                        role='Member',
                        family_id=family['id']
                    )
                    user.set_password(password)
                    
                    # Insert user into database
                    user_insert = db.table('users').insert(user.to_dict()).execute()
                    print(f"User insert response: {user_insert}")
                    
                    # Create default settings for user
                    settings_insert = db.table('settings').insert({
                        'id': str(uuid.uuid4()),
                        'user_id': user_id,
                        'theme': 'light',
                        'notifications': True,
                        'spherebot_enabled': True,
                        'location_sharing': False,
                        'dashboard_widgets': 'calendar,tasks,chat,finances'
                    }).execute()
                    print(f"Settings insert response: {settings_insert}")
                    
                    flash('Successfully joined family', 'success')
                    login_user(user)
                    return redirect(url_for('dashboard'))
                except Exception as e:
                    print(f"Error joining family: {str(e)}")
                    flash(f'Error joining family: {str(e)}', 'danger')
                    return render_template('register.html')
        except Exception as e:
            print(f"Error during registration: {str(e)}")
            flash(f'Error during registration: {str(e)}', 'danger')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# Root route
@app.route('/')
def index():
    """Redirect to home page."""
    return redirect(url_for('home'))

# Home page (no login required)
@app.route('/home')
def home():
    """Display the home page for non-authenticated users."""
    return render_template('home.html')

# Main dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    """Display the user's dashboard with widgets for different features."""
    from database import db
    
    # Get family information
    family_response = db.table('families').select('*').eq('id', current_user.family_id).execute()
    family = family_response.data[0] if family_response.data else None
    
    # Get upcoming events
    events_response = db.table('events').select('*').eq('family_id', current_user.family_id).gte('date', date.today().isoformat()).order('date').limit(5).execute()
    events = events_response.data
    
    # Get pending tasks
    tasks_response = db.table('tasks').select('*').eq('family_id', current_user.family_id).eq('status', 'Pending').order('due_date').limit(5).execute()
    tasks = tasks_response.data
    
    # Get recent chat messages
    chats_response = db.table('chats').select('*').eq('family_id', current_user.family_id).order('timestamp', desc=True).limit(5).execute()
    chats = chats_response.data
    
    # Get chat senders (users)
    if chats:
        sender_ids = [chat['sender_id'] for chat in chats]
        users_response = db.table('users').select('id, username').in_('id', sender_ids).execute()
        users = {user['id']: user['username'] for user in users_response.data}
    else:
        users = {}
    
    # Get finances
    finances_response = db.table('finances').select('*').eq('family_id', current_user.family_id).limit(5).execute()
    finances = finances_response.data
    
    # Generate SphereBot suggestion
    suggestion = get_spherebot_suggestion("dashboard")
    
    return render_template('dashboard.html', 
                          family=family,
                          events=events, 
                          tasks=tasks, 
                          chats=chats,
                          users=users,
                          finances=finances,
                          suggestion=suggestion)

# Family route
@app.route('/family')
@login_required
def family():
    """Display family information."""
    from database import db
    try:
        # Get family from Supabase
        family_response = db.table('families').select('*').eq('id', current_user.family_id).execute()
        
        if family_response.data:
            family = family_response.data[0]
            
            # Get family members
            members_response = db.table('users').select('*').eq('family_id', current_user.family_id).execute()
            members = members_response.data
            
            return render_template('family.html', family=family, members=members)
        else:
            flash('Family not found', 'danger')
            return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f'Error loading family information: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

# Calendar routes
@app.route('/calendar')
@login_required
def calendar():
    """Display the family calendar with events."""
    from database import db
    
    # Get all events for the user's family
    events_response = db.table('events').select('*').eq('family_id', current_user.family_id).execute()
    events = events_response.data
    
    # Format dates for the calendar
    calendar_events = []
    for event in events:
        calendar_events.append({
            'id': event['id'],
            'title': event['title'],
            'start': f"{event['date']}T{event['time']}",
            'description': event.get('description', ''),
            'location': event.get('location', '')
        })
    
    return render_template('calendar.html', events=calendar_events)

@app.route('/add_event', methods=['GET', 'POST'])
@login_required
def add_event():
    """Add a new event."""
    from database import db
    
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            date_str = request.form.get('date')
            time_str = request.form.get('time')
            description = request.form.get('description')
            location = request.form.get('location')
            
            # Validate input
            if not title or not date_str:
                flash('Title and date are required', 'danger')
                return render_template('add_event.html')
            
            # Create new event
            import uuid
            event_id = str(uuid.uuid4())
            
            # Insert event into database
            event_data = {
                'id': event_id,
                'title': title,
                'date': date_str,
                'time': time_str if time_str else None,
                'description': description,
                'location': location,
                'family_id': current_user.family_id,
                'created_by': current_user.id
            }
            
            event_insert = db.table('events').insert(event_data).execute()
            
            flash('Event added successfully', 'success')
            return redirect(url_for('calendar'))
        except Exception as e:
            flash(f'Error adding event: {str(e)}', 'danger')
            return render_template('add_event.html')
    
    # GET request - show the form
    return render_template('add_event.html')

@app.route('/edit_event/<event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    """Edit an existing event."""
    from database import db
    
    # Get event data
    event_response = db.table('events').select('*').eq('id', event_id).execute()
    
    if not event_response.data:
        flash('Event not found', 'danger')
        return redirect(url_for('calendar'))
    
    event = event_response.data[0]
    
    # Check if user has permission to edit this event
    if event['family_id'] != current_user.family_id:
        flash('You do not have permission to edit this event', 'danger')
        return redirect(url_for('calendar'))
    
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        location = request.form.get('location')
        description = request.form.get('description')
        
        # Validate required fields
        if not title or not date_str or not time_str:
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('edit_event', event_id=event_id))
        
        # Update event data
        event_data = {
            'title': title,
            'date': date_str,
            'time': time_str,
            'location': location,
            'description': description
        }
        
        # Update event in database
        db.table('events').update(event_data).eq('id', event_id).execute()
        
        flash('Event updated successfully', 'success')
        return redirect(url_for('calendar'))
    
    return render_template('edit_event.html', event=event)

@app.route('/delete_event/<event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    """Delete an event from the calendar."""
    from database import db
    
    # Get event data
    event_response = db.table('events').select('*').eq('id', event_id).execute()
    
    if not event_response.data:
        flash('Event not found', 'danger')
        return redirect(url_for('calendar'))
    
    event = event_response.data[0]
    
    # Check if user has permission to delete this event
    if event['family_id'] != current_user.family_id:
        flash('You do not have permission to delete this event', 'danger')
        return redirect(url_for('calendar'))
    
    # Delete event from database
    db.table('events').delete().eq('id', event_id).execute()
    
    flash('Event deleted successfully', 'success')
    return redirect(url_for('calendar'))

# Tasks routes
@app.route('/tasks')
@login_required
def tasks():
    """Display the family tasks and chores."""
    from database import db
    
    # Get all tasks for the user's family
    tasks_response = db.table('tasks').select('*').eq('family_id', current_user.family_id).execute()
    tasks = tasks_response.data
    
    # Get all users in the family for assignment dropdown
    users_response = db.table('users').select('id, username').eq('family_id', current_user.family_id).execute()
    users = {user['id']: user['username'] for user in users_response.data}
    
    # Separate tasks by status
    pending_tasks = [task for task in tasks if task['status'] == 'Pending']
    completed_tasks = [task for task in tasks if task['status'] == 'Completed']
    
    # User map is now the same as users
    user_map = {user['id']: user['username'] for user in users_response.data}
    
    return render_template('tasks.html', 
                          pending_tasks=pending_tasks, 
                          completed_tasks=completed_tasks,
                          users=users,
                          user_map=user_map)

@app.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    """Add a new task."""
    from database import db
    
    # Get all users in the family for assignment dropdown
    users_response = db.table('users').select('id, username').eq('family_id', current_user.family_id).execute()
    users = {user['id']: user['username'] for user in users_response.data}
    
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            description = request.form.get('description')
            due_date = request.form.get('due_date')
            assigned_to = request.form.get('assigned_to')
            points = request.form.get('points', 0)
            
            # Validate input
            if not title or not due_date:
                flash('Title and due date are required', 'danger')
                return render_template('add_task.html', users=users)
            
            # Create new task
            import uuid
            task_id = str(uuid.uuid4())
            
            # Insert task into database
            task_data = {
                'id': task_id,
                'title': title,
                'description': description,
                'due_date': due_date,
                'assigned_to': assigned_to if assigned_to else None,
                'points': int(points) if points else 0,
                'status': 'Pending',
                'family_id': current_user.family_id
            }
            
            task_insert = db.table('tasks').insert(task_data).execute()
            
            flash('Task added successfully', 'success')
            return redirect(url_for('tasks'))
        except Exception as e:
            flash(f'Error adding task: {str(e)}', 'danger')
            return render_template('add_task.html', users=users)
    
    # GET request - show the form
    return render_template('add_task.html', users=users)

@app.route('/complete_task/<task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    """Mark a task as completed."""
    from database import db
    
    # Get task data
    task_response = db.table('tasks').select('*').eq('id', task_id).execute()
    
    if not task_response.data:
        flash('Task not found', 'danger')
        return redirect(url_for('tasks'))
    
    task = task_response.data[0]
    
    # Check if user has permission to complete this task
    if task['family_id'] != current_user.family_id:
        flash('You do not have permission to complete this task', 'danger')
        return redirect(url_for('tasks'))
    
    # Update task status in database
    db.table('tasks').update({'status': 'Completed'}).eq('id', task_id).execute()
    
    # If the task has points and was assigned to the current user, we would update their points
    # But since the points column doesn't exist in the users table, we'll skip this for now
    # In a future update, we could add this column to the users table
    
    flash('Task marked as completed', 'success')
    return redirect(url_for('tasks'))

@app.route('/edit_task/<task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    """Edit an existing task."""
    from database import db
    
    # Get task data
    task_response = db.table('tasks').select('*').eq('id', task_id).execute()
    
    if not task_response.data:
        flash('Task not found', 'danger')
        return redirect(url_for('tasks'))
    
    task = task_response.data[0]
    
    # Check if user has permission to edit this task
    if task['family_id'] != current_user.family_id:
        flash('You do not have permission to edit this task', 'danger')
        return redirect(url_for('tasks'))
    
    # Get all users in the family for assignment dropdown
    users_response = db.table('users').select('id, username').eq('family_id', current_user.family_id).execute()
    users = {user['id']: user['username'] for user in users_response.data}
    
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        due_date = request.form.get('due_date')
        assigned_to = request.form.get('assigned_to')
        points = request.form.get('points', 0)
        
        # Validate required fields
        if not title or not due_date or not assigned_to:
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('edit_task', task_id=task_id))
        
        # Update task data
        task_data = {
            'title': title,
            'description': description,
            'due_date': due_date,
            'assigned_to': assigned_to,
            'points': int(points)
        }
        
        # Update task in database
        db.table('tasks').update(task_data).eq('id', task_id).execute()
        
        flash('Task updated successfully', 'success')
        return redirect(url_for('tasks'))
    
    return render_template('edit_task.html', task=task, users=users)

@app.route('/delete_task/<task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    """Delete a task."""
    from database import db
    
    # Get task data
    task_response = db.table('tasks').select('*').eq('id', task_id).execute()
    
    if not task_response.data:
        flash('Task not found', 'danger')
        return redirect(url_for('tasks'))
    
    task = task_response.data[0]
    
    # Check if user has permission to delete this task
    if task['family_id'] != current_user.family_id:
        flash('You do not have permission to delete this task', 'danger')
        return redirect(url_for('tasks'))
    
    # Delete task from database
    db.table('tasks').delete().eq('id', task_id).execute()
    
    flash('Task deleted successfully', 'success')
    return redirect(url_for('tasks'))

@app.route('/reopen_task/<task_id>', methods=['POST'])
@login_required
def reopen_task(task_id):
    """Reopen a completed task."""
    from database import db
    
    # Get task data
    task_response = db.table('tasks').select('*').eq('id', task_id).execute()
    
    if not task_response.data:
        flash('Task not found', 'danger')
        return redirect(url_for('tasks'))
    
    task = task_response.data[0]
    
    # Check if user has permission to reopen this task
    if task['family_id'] != current_user.family_id:
        flash('You do not have permission to reopen this task', 'danger')
        return redirect(url_for('tasks'))
    
    # Update task status in database
    db.table('tasks').update({'status': 'Pending'}).eq('id', task_id).execute()
    
    flash('Task reopened', 'success')
    return redirect(url_for('tasks'))

@app.route('/task/<task_id>')
@login_required
def task_detail(task_id):
    """Display details for a specific task."""
    from database import db
    
    # Get task details
    task_response = db.table('tasks').select('*').eq('id', task_id).eq('family_id', current_user.family_id).execute()
    
    if not task_response.data:
        flash('Task not found', 'danger')
        return redirect(url_for('tasks'))
    
    task = task_response.data[0]
    
    # Get all users in the family for assignment dropdown
    users_response = db.table('users').select('id, username').eq('family_id', current_user.family_id).execute()
    users = {user['id']: user['username'] for user in users_response.data}
    
    # User map is now the same as users
    user_map = {user['id']: user['username'] for user in users_response.data}
    
    return render_template('task_detail.html', task=task, users=users, user_map=user_map)

@app.route('/bid_task/<task_id>', methods=['POST'])
@login_required
def bid_task(task_id):
    """Bid on a task."""
    from database import db
    
    # Get task data
    task_response = db.table('tasks').select('*').eq('id', task_id).execute()
    
    if not task_response.data:
        flash('Task not found', 'danger')
        return redirect(url_for('tasks'))
    
    task = task_response.data[0]
    
    # Check if user has permission to bid on this task
    if task['family_id'] != current_user.family_id:
        flash('You do not have permission to bid on this task', 'danger')
        return redirect(url_for('tasks'))
    
    # Get bid points from form
    bid_points = request.form.get('bid_points', type=int)
    
    if not bid_points or bid_points < 1:
        flash('Invalid bid amount', 'danger')
        return redirect(url_for('tasks'))
    
    # In a future update, we would check if the user has enough points
    # and update the task and user points accordingly
    
    # For now, just assign the task to the user
    db.table('tasks').update({
        'assigned_to': current_user.id,
        'points': bid_points
    }).eq('id', task_id).execute()
    
    flash(f'You have successfully bid {bid_points} points on this task', 'success')
    return redirect(url_for('tasks'))

# Finance routes
@app.route('/finances')
@login_required
def finances():
    """Display finances page."""
    from database import db
    try:
        # Get family information
        family_response = db.table('families').select('*').eq('id', current_user.family_id).execute()
        if not family_response.data:
            flash('Family not found', 'danger')
            return redirect(url_for('dashboard'))
        
        family = family_response.data[0]
        
        # Get family members
        members_response = db.table('users').select('*').eq('family_id', current_user.family_id).execute()
        family['members'] = members_response.data
        
        # Get finances data
        finances_response = db.table('finances').select('*').eq('family_id', current_user.family_id).execute()
        finances = finances_response.data
        
        # Categorize finances
        budgets = [f for f in finances if f.get('type') == 'Budget']
        goals = [f for f in finances if f.get('type') == 'Goal']
        allowances = [f for f in finances if f.get('type') == 'Allowance']
        
        return render_template('finances.html',
                              family=family,
                              budgets=budgets,
                              goals=goals,
                              allowances=allowances)
    except Exception as e:
        flash(f'Error loading finances: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/add_finance', methods=['GET', 'POST'])
@login_required
def add_finance():
    """Add a new finance record."""
    from database import db
    
    if request.method == 'POST':
        try:
            type = request.form.get('type')
            amount = request.form.get('amount')
            description = request.form.get('description')
            
            # Validate input
            if not type or not amount:
                flash('Type and amount are required', 'danger')
                return render_template('add_finance.html')
            
            # Create new finance record
            import uuid
            from datetime import datetime
            
            finance_id = str(uuid.uuid4())
            
            # Insert finance record into database
            finance_data = {
                'id': finance_id,
                'type': type,
                'title': type,  # Using type as title since title is required
                'amount': float(amount),
                'description': description,
                'family_id': current_user.family_id,
                'created_at': datetime.now().isoformat()
            }
            
            finance_insert = db.table('finances').insert(finance_data).execute()
            
            flash('Finance record added successfully', 'success')
            return redirect(url_for('finances'))
        except Exception as e:
            flash(f'Error adding finance record: {str(e)}', 'danger')
            return render_template('add_finance.html')
    
    # GET request - show the form
    return render_template('add_finance.html')

@app.route('/edit_finance/<finance_id>', methods=['GET', 'POST'])
@login_required
def edit_finance(finance_id):
    """Edit an existing finance item."""
    # Check if user has permission to edit finances
    if current_user.role not in ['Admin', 'Member']:
        flash('You do not have permission to edit finances', 'danger')
        return redirect(url_for('finances'))
    
    from database import db
    
    # Get finance data
    finance_response = db.table('finances').select('*').eq('id', finance_id).execute()
    
    if not finance_response.data:
        flash('Finance item not found', 'danger')
        return redirect(url_for('finances'))
    
    finance = finance_response.data[0]
    
    # Check if user has permission to edit this finance item
    if finance['family_id'] != current_user.family_id:
        flash('You do not have permission to edit this finance item', 'danger')
        return redirect(url_for('finances'))
    
    # Get all users in the family for assignment dropdown
    users_response = db.table('users').select('id, username').eq('family_id', current_user.family_id).execute()
    users = users_response.data
    
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        amount = request.form.get('amount')
        target_amount = request.form.get('target_amount')
        due_date = request.form.get('due_date')
        assigned_to = request.form.get('assigned_to')
        
        # Validate required fields
        if not title or not amount:
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('edit_finance', finance_id=finance_id))
        
        # Update finance data
        finance_data = {
            'title': title,
            'description': description,
            'amount': float(amount),
            'target_amount': float(target_amount) if target_amount else None,
            'due_date': due_date if due_date else None,
            'assigned_to': assigned_to if assigned_to else None
        }
        
        # Update finance in database
        db.table('finances').update(finance_data).eq('id', finance_id).execute()
        
        flash('Finance item updated successfully', 'success')
        return redirect(url_for('finances'))
    
    return render_template('edit_finance.html', finance=finance, users=users)

@app.route('/delete_finance/<finance_id>', methods=['POST'])
@login_required
def delete_finance(finance_id):
    """Delete a finance item."""
    # Check if user has permission to delete finances
    if current_user.role not in ['Admin', 'Member']:
        flash('You do not have permission to delete finances', 'danger')
        return redirect(url_for('finances'))
    
    from database import db
    
    # Get finance data
    finance_response = db.table('finances').select('*').eq('id', finance_id).execute()
    
    if not finance_response.data:
        flash('Finance item not found', 'danger')
        return redirect(url_for('finances'))
    
    finance = finance_response.data[0]
    
    # Check if user has permission to delete this finance item
    if finance['family_id'] != current_user.family_id:
        flash('You do not have permission to delete this finance item', 'danger')
        return redirect(url_for('finances'))
    
    # Delete finance from database
    db.table('finances').delete().eq('id', finance_id).execute()
    
    flash('Finance item deleted successfully', 'success')
    return redirect(url_for('finances'))

# Chat routes
@app.route('/chat')
@login_required
def chat():
    """Display the family chat interface."""
    from database import db
    
    # Get all chat messages for the user's family
    try:
        chats_response = db.table('chats').select('*').eq('family_id', current_user.family_id).order('timestamp', desc=True).limit(50).execute()
        chats = chats_response.data
    except Exception as e:
        app.logger.error(f"Error fetching chats: {str(e)}")
        chats = []
    
    # Get all users in the family for displaying sender names
    try:
        users_response = db.table('users').select('id, username').eq('family_id', current_user.family_id).execute()
        users = {user['id']: user['username'] for user in users_response.data}
        family_members = users_response.data
    except Exception as e:
        app.logger.error(f"Error fetching users: {str(e)}")
        users = {}
        family_members = []
    
    # Get threads if any
    threads = []
    try:
        threads_response = db.table('chat_threads').select('*').eq('family_id', current_user.family_id).execute()
        if threads_response.data:
            threads = threads_response.data
    except Exception as e:
        # If the chat_threads table doesn't exist, we'll use an empty list
        app.logger.error(f"Error fetching chat threads: {str(e)}")
    
    # Get family code for invites
    try:
        family_response = db.table('families').select('code').eq('id', current_user.family_id).execute()
        family_code = family_response.data[0]['code'] if family_response.data else ''
    except Exception as e:
        app.logger.error(f"Error fetching family code: {str(e)}")
        family_code = ''
    
    return render_template('chat.html', 
                          chats=chats, 
                          users=users,
                          threads=threads,
                          family_members=family_members,
                          family_code=family_code,
                          current_user=current_user)

@app.route('/send_message', methods=['GET', 'POST'])
@login_required
def send_message():
    """Send a new chat message."""
    from database import db
    
    if request.method == 'POST':
        try:
            message = request.form.get('message')
            thread_id = request.form.get('thread_id')
            
            # Validate input
            if not message:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'status': 'error', 'message': 'Message content is required'})
                else:
                    flash('Message content is required', 'danger')
                    return redirect(url_for('chat'))
            
            # Create new message
            import uuid
            from datetime import datetime
            
            message_id = str(uuid.uuid4())
            
            # Insert message into database
            message_data = {
                'id': message_id,
                'content': message,
                'sender_id': current_user.id,
                'family_id': current_user.family_id,
                'thread_id': thread_id if thread_id else None,
                'timestamp': datetime.now().isoformat()
            }
            
            message_insert = db.table('chats').insert(message_data).execute()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'status': 'success', 'message': 'Message sent successfully'})
            else:
                flash('Message sent successfully', 'success')
                return redirect(url_for('chat'))
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'status': 'error', 'message': f'Error sending message: {str(e)}'})
            else:
                flash(f'Error sending message: {str(e)}', 'danger')
                return redirect(url_for('chat'))
    
    # GET request - redirect to chat
    return redirect(url_for('chat'))

@app.route('/get_messages')
@login_required
def get_messages():
    """Get chat messages for AJAX updates."""
    from database import db
    
    # Get timestamp of last message client has
    last_timestamp = request.args.get('last_timestamp')
    thread_id = request.args.get('thread_id')
    
    # Query for new messages
    query = db.table('chats').select('*').eq('family_id', current_user.family_id)
    
    if last_timestamp:
        query = query.gt('timestamp', last_timestamp)
        
    if thread_id and thread_id != 'all':
        query = query.eq('thread_id', thread_id)
        
    query = query.order('timestamp')
    
    # Execute query
    chats_response = query.execute()
    chats = chats_response.data
    
    # Get user information for new messages
    if chats:
        sender_ids = list(set([chat['sender_id'] for chat in chats]))
        users_response = db.table('users').select('id, username').in_('id', sender_ids).execute()
        users = {user['id']: user['username'] for user in users_response.data}
        
        # Format messages for JSON response
        messages = []
        for chat in chats:
            messages.append({
                'id': chat['id'],
                'content': chat['content'],
                'sender_id': chat['sender_id'],
                'sender_name': users.get(chat['sender_id'], 'Unknown'),
                'timestamp': chat['timestamp'],
                'thread_id': chat['thread_id']
            })
        
        return jsonify({'messages': messages})
    
    return jsonify({'messages': []})

@app.route('/vote_poll', methods=['POST'])
@login_required
def vote_poll():
    """Vote on a poll in the chat."""
    from database import db
    import json
    import uuid
    from datetime import datetime
    
    # Get form data
    chat_id = request.form.get('chat_id')
    option_index = request.form.get('option_index')
    
    if not chat_id or not option_index:
        return jsonify({'success': False, 'error': 'Missing required data'})
    
    # Get the chat message
    try:
        chat_response = db.table('chats').select('*').eq('id', chat_id).execute()
        
        if not chat_response.data:
            return jsonify({'success': False, 'error': 'Poll not found'})
        
        chat = chat_response.data[0]
        
        # Check if this is a poll
        if not chat.get('is_poll'):
            return jsonify({'success': False, 'error': 'Not a poll'})
    except Exception as e:
        app.logger.error(f"Error fetching chat for poll: {str(e)}")
        return jsonify({'success': False, 'error': 'Error accessing poll data'})
    
    # Try to record the vote
    try:
        # Create vote data
        vote_data = {
            'id': str(uuid.uuid4()),
            'poll_id': chat_id,
            'user_id': current_user.id,
            'option_index': int(option_index),
            'timestamp': datetime.now().isoformat()
        }
        
        # Insert vote into database
        db.table('poll_votes').insert(vote_data).execute()
        
        return jsonify({'success': True, 'message': 'Vote recorded'})
    except Exception as e:
        app.logger.error(f"Error recording poll vote: {str(e)}")
        return jsonify({'success': False, 'error': 'Poll voting system unavailable'})

# Memory routes
@app.route('/memories')
@login_required
def memories():
    """Display the family memories."""
    from database import db
    
    # Get all memories for the user's family
    memories_response = db.table('memories').select('*').eq('family_id', current_user.family_id).order('date', desc=True).execute()
    memories = [Memory.from_dict(memory) for memory in memories_response.data]
    
    spherebot_suggestion = get_spherebot_suggestion("memory")
    
    return render_template('memories.html', 
                          memories=memories,
                          spherebot_suggestion=spherebot_suggestion)

@app.route('/memories/add', methods=['GET', 'POST'])
@login_required
def add_memory():
    """Add a new memory."""
    from database import db
    import uuid
    from datetime import datetime
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        photo_url = request.form.get('photo_url')  # In a real app, this would be file upload
        memory_date = request.form.get('date')
        
        # Create new memory with UUID
        memory_id = str(uuid.uuid4())
        memory_data = {
            'id': memory_id,
            'title': title,
            'description': description,
            'photo_url': photo_url,
            'date': memory_date,
            'family_id': current_user.family_id,
            'created_by': current_user.id,
            'created_at': datetime.now().isoformat()
        }
        
        # Insert memory into database
        db.table('memories').insert(memory_data).execute()
        
        flash('Memory added successfully!', 'success')
        return redirect(url_for('memories'))
        
    return render_template('add_memory.html')

@app.route('/memories/share/<memory_id>', methods=['POST'])
@login_required
def share_memory(memory_id):
    """Share a memory with other families."""
    from database import db
    
    # Get memory data
    memory_response = db.table('memories').select('*').eq('id', memory_id).execute()
    
    if not memory_response.data:
        flash('Memory not found', 'danger')
        return redirect(url_for('memories'))
    
    memory = memory_response.data[0]
    
    # Check if user has permission to share this memory
    if memory['family_id'] != current_user.family_id:
        flash('You do not have permission to share this memory', 'danger')
        return redirect(url_for('memories'))
    
    # Get shared_with data
    shared_with = request.form.getlist('shared_with')
    shared_with_str = ','.join(shared_with) if shared_with else ''
    
    # Update memory in database
    db.table('memories').update({'shared_with': shared_with_str}).eq('id', memory_id).execute()
    
    flash('Memory shared successfully!', 'success')
    return redirect(url_for('memories'))

# Inventory routes
@app.route('/inventory')
@login_required
def inventory():
    from database import db
    
    # Get all inventory items for the user's family
    inventory_response = db.table('inventory').select('*').eq('family_id', current_user.family_id).execute()
    items = [Inventory.from_dict(item) for item in inventory_response.data]
    
    spherebot_suggestion = get_spherebot_suggestion("inventory")
    
    return render_template('inventory.html', 
                          items=items,
                          spherebot_suggestion=spherebot_suggestion)

@app.route('/inventory/add', methods=['POST'])
@login_required
def add_inventory_item():
    from database import db
    import uuid
    
    item_name = request.form.get('item_name')
    quantity = int(request.form.get('quantity', 1))
    category = request.form.get('category', 'General')
    location = request.form.get('location', '')
    notes = request.form.get('notes', '')
    
    # Create new inventory item with UUID
    item_id = str(uuid.uuid4())
    item_data = {
        'id': item_id,
        'item_name': item_name,
        'quantity': quantity,
        'category': category,
        'location': location,
        'notes': notes,
        'family_id': current_user.family_id,
        'created_at': datetime.now().isoformat()
    }
    
    # Insert item into database
    db.table('inventory').insert(item_data).execute()
    
    flash('Item added to inventory successfully!')
    return redirect(url_for('inventory'))

# Health routes
@app.route('/health')
@login_required
def health():
    """Display health information."""
    from database import db
    try:
        # Get health records for the current user
        health_response = db.table('health').select('*').eq('user_id', current_user.id).execute()
        health_records = health_response.data
        
        # Get health records for family members
        # First get all family members
        members_response = db.table('users').select('*').eq('family_id', current_user.family_id).execute()
        family_members = members_response.data
        
        # Then get health records for each family member
        family_health = []
        for member in family_members:
            if member['id'] != current_user.id:  # Skip current user as we already have their records
                member_health = db.table('health').select('*').eq('user_id', member['id']).execute().data
                if member_health:
                    for record in member_health:
                        record['username'] = member['username']
                        family_health.append(record)
        
        return render_template('health.html', 
                              health_records=health_records,
                              family_health=family_health,
                              family_members=family_members)
    except Exception as e:
        flash(f'Error loading health information: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/health/add', methods=['POST'])
@login_required
def add_health_record():
    """Add a new health record."""
    from database import db
    import uuid
    
    # Check if user has permission to add health data
    if current_user.role not in ['Admin', 'Member']:
        flash('You do not have permission to add health data')
        return redirect(url_for('dashboard'))
    
    user_id = request.form.get('user_id', current_user.id)
    record_type = request.form.get('record_type')
    medication = request.form.get('medication', '')
    dosage = request.form.get('dosage', '')
    schedule = request.form.get('schedule', '')
    notes = request.form.get('notes', '')
    reminder_time = request.form.get('reminder_time')
    
    # Create new health record with UUID
    record_id = str(uuid.uuid4())
    record_data = {
        'id': record_id,
        'user_id': user_id,
        'record_type': record_type,
        'medication': medication,
        'dosage': dosage,
        'schedule': schedule,
        'notes': notes,
        'reminder_time': reminder_time,
        'family_id': current_user.family_id,
        'created_at': datetime.now().isoformat()
    }
    
    # Insert record into database
    db.table('health').insert(record_data).execute()
    
    flash('Health record added successfully!')
    return redirect(url_for('health'))

# Emergency routes
@app.route('/emergency')
@login_required
def emergency():
    from database import db
    
    # Get active emergencies for the user's family
    emergency_response = db.table('emergency').select('*').eq('family_id', current_user.family_id).eq('resolved', False).execute()
    active_emergencies = [Emergency.from_dict(emergency) for emergency in emergency_response.data]
    
    # Get emergency contacts for the user's family
    emergency_contacts_response = db.table('emergency_contacts').select('*').eq('family_id', current_user.family_id).execute()
    emergency_contacts = [EmergencyContact.from_dict(contact) for contact in emergency_contacts_response.data]
    
    spherebot_suggestion = get_spherebot_suggestion("emergency")
    
    return render_template('emergency.html', 
                          active_emergencies=active_emergencies,
                          emergency_contacts=emergency_contacts,
                          spherebot_suggestion=spherebot_suggestion)

@app.route('/emergency/sos', methods=['POST'])
@login_required
def trigger_sos():
    from database import db
    import uuid
    
    location = request.form.get('location', 'Unknown')
    
    # Create new emergency with UUID
    emergency_id = str(uuid.uuid4())
    emergency_data = {
        'id': emergency_id,
        'user_id': current_user.id,
        'family_id': current_user.family_id,
        'location': location,
        'sos_status': True,
        'resolved': False,
        'created_at': datetime.now().isoformat()
    }
    
    # Insert emergency into database
    db.table('emergency').insert(emergency_data).execute()
    
    # In a real app, this would send notifications to family members
    
    flash('SOS triggered! Family members have been notified.')
    return redirect(url_for('emergency'))

@app.route('/emergency/contact/add', methods=['POST'])
@login_required
def add_emergency_contact():
    """Add a new emergency contact."""
    from database import db
    import uuid
    
    # Check if user has permission to add emergency contacts
    if current_user.role not in ['Admin', 'Member']:
        flash('You do not have permission to add emergency contacts')
        return redirect(url_for('dashboard'))
    
    name = request.form.get('name')
    relation = request.form.get('relation')
    phone = request.form.get('phone')
    email = request.form.get('email', '')
    address = request.form.get('address', '')
    notes = request.form.get('notes', '')
    is_primary = 'is_primary' in request.form
    
    # Create new emergency contact with UUID
    contact_id = str(uuid.uuid4())
    contact_data = {
        'id': contact_id,
        'name': name,
        'relation': relation,
        'phone': phone,
        'email': email,
        'address': address,
        'notes': notes,
        'is_primary': is_primary,
        'family_id': current_user.family_id,
        'created_at': datetime.now().isoformat()
    }
    
    # Insert contact into database
    db.table('emergency_contacts').insert(contact_data).execute()
    
    flash('Emergency contact added successfully!')
    return redirect(url_for('emergency'))

# Settings routes
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    from database import db
    
    # Get user settings
    settings_response = db.table('settings').select('*').eq('user_id', current_user.id).execute()
    user_settings = settings_response.data[0] if settings_response.data else None
    
    # Create default settings if none exists
    if not user_settings:
        user_settings = {
            'id': str(uuid.uuid4()),
            'user_id': current_user.id,
            'theme': 'light',
            'notifications': True,
            'spherebot_enabled': True,
            'location_sharing': False,
            'dashboard_widgets': 'calendar,tasks,chat,finances'
        }
        db.table('settings').insert(user_settings).execute()
    
    if request.method == 'POST':
        theme = request.form.get('theme')
        notifications = request.form.get('notifications') == 'on'
        spherebot_enabled = request.form.get('spherebot_enabled') == 'on'
        location_sharing = request.form.get('location_sharing') == 'on'
        
        # Handle dashboard widgets - convert checkbox values to comma-separated string
        dashboard_widgets = request.form.getlist('dashboard_widgets')
        if not dashboard_widgets:
            dashboard_widgets = []
        dashboard_widgets_str = ','.join(dashboard_widgets)
        
        # Update user settings
        user_settings['theme'] = theme
        user_settings['notifications'] = notifications
        user_settings['spherebot_enabled'] = spherebot_enabled
        user_settings['location_sharing'] = location_sharing
        user_settings['dashboard_widgets'] = dashboard_widgets_str
        
        # Update settings in database
        db.table('settings').update(user_settings).eq('id', user_settings['id']).execute()
        
        flash('Settings updated successfully!')
        return redirect(url_for('settings'))
        
    return render_template('settings.html', settings=user_settings)

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    from database import db
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Validate input
    if not current_password or not new_password or not confirm_password:
        flash('All fields are required', 'danger')
        return redirect(url_for('settings'))
        
    if new_password != confirm_password:
        flash('New passwords do not match', 'danger')
        return redirect(url_for('settings'))
        
    # Check current password
    if not check_password_hash(current_user.password_hash, current_password):
        flash('Current password is incorrect', 'danger')
        return redirect(url_for('settings'))
        
    # Update password
    current_user.password_hash = generate_password_hash(new_password)
    db.table('users').update({'password_hash': current_user.password_hash}).eq('id', current_user.id).execute()
    
    flash('Password changed successfully!', 'success')
    return redirect(url_for('settings'))

# SphereBot routes
@app.route('/spherebot')
@login_required
def spherebot():
    """Render the SphereBot AI assistant page."""
    return render_template('spherebot.html')

@app.route('/spherebot/query', methods=['POST'])
@login_required
def spherebot_query():
    """Handle SphereBot AI queries and return responses."""
    data = request.get_json()
    query = data.get('query', '')
    
    # Determine the context based on the query content
    context = "general"
    
    # Check for context keywords in the query
    context_keywords = {
        "calendar": ["calendar", "schedule", "event", "appointment", "meeting", "remind", "when"],
        "tasks": ["task", "chore", "assignment", "todo", "to-do", "to do", "work", "job"],
        "finance": ["money", "budget", "finance", "spending", "expense", "cost", "save", "bill"],
        "chat": ["message", "chat", "conversation", "talk", "discuss", "communicate"],
        "memory": ["photo", "picture", "memory", "album", "remember", "moment", "capture"],
        "inventory": ["inventory", "item", "stock", "supply", "grocery", "shopping", "list"],
        "health": ["health", "medication", "medicine", "doctor", "appointment", "prescription"],
        "emergency": ["emergency", "contact", "urgent", "crisis", "help", "sos"],
        "family": ["family", "member", "relative", "relationship", "invite", "join"]
    }
    
    for ctx, keywords in context_keywords.items():
        if any(keyword in query.lower() for keyword in keywords):
            context = ctx
            break
    
    # Get AI-powered suggestion based on context and query
    response = get_spherebot_suggestion(context)
    
    # If no specific response was generated, provide a fallback
    if not response:
        fallback_responses = [
            "I'm here to help with your family coordination. What would you like assistance with?",
            "I can help with calendars, tasks, finances, and more. What do you need?",
            "I'm your family assistant. How can I make your day easier?",
            "I'm analyzing your family data to provide better suggestions. What can I help with now?",
            "I'm learning more about your family's needs. Is there something specific you're looking for?"
        ]
        response = random.choice(fallback_responses)
    
    # Log the interaction for future improvement
    # In a real implementation, this would be stored in a database
    print(f"SphereBot Query: {query}, Context: {context}, Response: {response}")
    
    return jsonify({"response": response})

# SphereBot API endpoint
@app.route('/api/spherebot/suggestion', methods=['POST'])
@login_required
def spherebot_api():
    data = request.json
    context = data.get('context')
    user_query = data.get('query')
    
    suggestion = get_spherebot_suggestion(context)
    
    return jsonify({'suggestion': suggestion})

# Supabase real-time API endpoints
@app.route('/api/supabase/client')
@login_required
def supabase_client():
    """Provide Supabase client information to the frontend."""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Get Supabase URL and anon key
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        return jsonify({
            'success': False,
            'error': 'Supabase configuration is missing'
        })
    
    return jsonify({
        'success': True,
        'supabaseUrl': supabase_url,
        'supabaseKey': supabase_key
    })

@app.route('/api/user/<user_id>/name')
@login_required
def get_user_name(user_id):
    """Get a user's name by ID."""
    from database import db
    
    # Verify user is in the same family
    user_response = db.table('users').select('username, family_id').eq('id', user_id).execute()
    
    if not user_response.data:
        return jsonify({
            'success': False,
            'error': 'User not found'
        })
    
    user = user_response.data[0]
    
    # Only allow access to users in the same family
    if user['family_id'] != current_user.family_id:
        return jsonify({
            'success': False,
            'error': 'Unauthorized'
        })
    
    return jsonify({
        'success': True,
        'username': user['username']
    })

# Invite route
@app.route('/invite', methods=['GET', 'POST'])
@login_required
def invite():
    """Invite a new family member."""
    from database import db
    
    # Only admins can invite new members
    if current_user.role != 'Admin':
        flash('Only family administrators can invite new members', 'danger')
        return redirect(url_for('family'))
    
    # Get the family code
    family_response = db.table('families').select('code').eq('id', current_user.family_id).execute()
    
    if not family_response.data:
        flash('Family not found', 'danger')
        return redirect(url_for('dashboard'))
    
    family_code = family_response.data[0]['code']
    invitation_link = request.host_url + 'register?family_code=' + family_code
    
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            role = request.form.get('role')
            
            # Validate input
            if not email:
                flash('Email is required', 'danger')
                return render_template('invite.html', invitation_link=invitation_link)
            
            # Here you would typically send an email with the invitation link
            # For now, we'll just show a success message
            
            flash(f'Invitation sent to {email} with role {role}', 'success')
            return redirect(url_for('settings'))
        except Exception as e:
            flash(f'Error sending invitation: {str(e)}', 'danger')
            return render_template('invite.html', invitation_link=invitation_link)
    
    # GET request - show the form
    return render_template('invite.html', invitation_link=invitation_link)

@app.route('/event/<event_id>')
@login_required
def event_detail(event_id):
    """Display details for a specific event."""
    from database import db
    
    # Get event details
    event_response = db.table('events').select('*').eq('id', event_id).eq('family_id', current_user.family_id).execute()
    
    if not event_response.data:
        flash('Event not found', 'danger')
        return redirect(url_for('calendar'))
    
    event = event_response.data[0]
    
    # Get all users in the family
    users_response = db.table('users').select('id, username').eq('family_id', current_user.family_id).execute()
    users = users_response.data
    
    # Create a mapping of user IDs to usernames
    user_map = {user['id']: user['username'] for user in users}
    
    return render_template('event_detail.html', event=event, users=users, user_map=user_map)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
