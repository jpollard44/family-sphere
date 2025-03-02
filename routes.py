from flask import render_template, redirect, url_for, flash, request, jsonify, make_response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
import json
import traceback
import requests
from datetime import date, datetime, timedelta
from database import db
from models import User, Family, Event, Task, Finance, Chat, Memory, Inventory, Health, Emergency, Settings, EmergencyContact
from flask_wtf.csrf import generate_csrf
from app import app, csrf
from icalendar import Calendar, Event as ICalEvent, vText
import pytz
import uuid
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

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
    import requests
    from datetime import date, datetime
    from app import app
    
    # Get the current user
    user = current_user
    
    try:
        # Get family data
        family_response = db.table('families').select('*').eq('id', user.family_id).execute()
        
        if family_response.data:
            family = family_response.data[0]
            
            # Prepare system message based on context
            system_message = {
                "role": "system",
                "content": f"You are SphereBot, an AI assistant for the FamilySphere family management app. "
                      f"You help families coordinate activities, manage tasks, and stay connected. "
                      f"You are currently helping with the {context} feature. "
                      f"Keep responses friendly, helpful, and focused on family coordination."
            }
            
            # Prepare context-specific messages
            messages = [system_message]
            
            if context == "calendar":
                # Get upcoming events
                upcoming_events = db.table('events').select('*').eq('family_id', user.family_id).gte('date', date.today().isoformat()).order('date').limit(5).execute().data
                events_str = "Upcoming events:\n" + "\n".join([f"- {event['title']} on {event['date']}" for event in upcoming_events]) if upcoming_events else "No upcoming events."
                messages.append({
                    "role": "user",
                    "content": f"Help me manage my family calendar. {events_str}"
                })
                
            elif context == "tasks":
                # Get pending tasks
                pending_tasks = db.table('tasks').select('*').eq('family_id', user.family_id).eq('status', 'Pending').execute().data
                tasks_str = "Pending tasks:\n" + "\n".join([f"- {task['title']} (due: {task['due_date']})" for task in pending_tasks]) if pending_tasks else "No pending tasks."
                messages.append({
                    "role": "user",
                    "content": f"Help me manage family tasks. {tasks_str}"
                })
                
            else:
                messages.append({
                    "role": "user",
                    "content": f"Help me with {context} management in my family app."
                })
        
        # Call Grok API
        response = requests.post(
            app.config['GROK_API_URL'],
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {app.config['GROK_API_KEY']}"
            },
            json={
                "messages": messages,
                "model": app.config['GROK_MODEL'],
                "stream": False,
                "temperature": 0.7
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and result['choices']:
                return result['choices'][0]['message']['content']
        
        # Fallback to default suggestions if API call fails
        return get_default_suggestion(context)
        
    except Exception as e:
        print(f"Error in get_spherebot_suggestion: {str(e)}")
        return get_default_suggestion(context)

def get_default_suggestion(context):
    """Return a default suggestion based on the context when the Grok API is unavailable."""
    suggestions = {
        "general": "I'm here to help you manage your family activities. You can ask me about your calendar, tasks, finances, and more.",
        "calendar": "Would you like to see your upcoming events or add a new event to your calendar?",
        "tasks": "Here are some task management options:\n- View your pending tasks\n- Create a new task\n- Assign tasks to family members to distribute responsibilities\n- Mark tasks as completed",
        "finance": "I can help you manage your family finances. Would you like to review your budget, add an expense, or set a savings goal?",
        "chat": "Would you like to send a message to your family members or check recent conversations?",
        "memory": "Would you like to view your family photo albums or add new memories?",
        "inventory": "I can help you manage your household inventory. Would you like to check what items you need to restock?",
        "health": "Would you like to view medication schedules or set up health reminders for your family?",
        "emergency": "Would you like to update emergency contact information or check your family's safety status?",
        "family": "Would you like to manage your family members or connect with other families?"
    }
    
    return suggestions.get(context, suggestions["general"])

# Helper function to get RSVP count for an event
def get_rsvp_count(event_id):
    """Get the count of 'yes' RSVPs for an event."""
    from database import db
    
    rsvp_response = db.table('event_rsvps').select('*').eq('event_id', event_id).eq('response', 'yes').execute()
    return len(rsvp_response.data)

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
    import datetime
    
    # Get all events for the user's family
    events_response = db.table('events').select('*').eq('family_id', current_user.family_id).execute()
    events = events_response.data
    
    # Get shared events
    shared_events = []
    shared_response = db.table('events').select('*').neq('family_id', current_user.family_id).execute()
    for event in shared_response.data:
        shared_with = event.get('shared_with', '')
        if shared_with and current_user.family_id in shared_with.split(','):
            shared_events.append(event)
    
    # Get family members for filter dropdown
    family_members_response = db.table('users').select('id, username').eq('family_id', current_user.family_id).execute()
    family_members = family_members_response.data
    
    # Format events for FullCalendar
    formatted_events = []
    
    for event in events:
        formatted_event = format_event_for_calendar(event, is_family_event=True)
        formatted_events.append(formatted_event)
    
    for event in shared_events:
        formatted_event = format_event_for_calendar(event, is_family_event=False)
        formatted_events.append(formatted_event)
    
    return render_template('calendar.html', 
                           events=formatted_events, 
                           family_members=family_members,
                           page_title="Family Calendar")

# Helper function to format events for FullCalendar
def format_event_for_calendar(event, is_family_event=True):
    """Format an event for FullCalendar."""
    formatted_event = {
        'id': event['id'],
        'title': event['title'],
        'start': event['date']
    }
    
    # Add time if available
    if event.get('time'):
        try:
            # Try parsing with seconds
            event_time = datetime.datetime.strptime(event['time'], '%H:%M:%S').time()
        except ValueError:
            # If that fails, try without seconds
            event_time = datetime.datetime.strptime(event['time'], '%H:%M').time()
        
        formatted_event['start'] += 'T' + event_time.strftime('%H:%M:%S')
    
    # Add end time if available, otherwise default to 1 hour
    if event.get('end_time'):
        try:
            # Try parsing with seconds
            end_time = datetime.datetime.strptime(event['end_time'], '%H:%M:%S').time()
        except ValueError:
            # If that fails, try without seconds
            end_time = datetime.datetime.strptime(event['end_time'], '%H:%M').time()
        
        formatted_event['end'] = event['date'] + 'T' + end_time.strftime('%H:%M:%S')
    else:
        # Fallback for events with date but no time
        formatted_event['end'] = event['date'] + 'T' + datetime.time(23, 59, 59).strftime('%H:%M:%S')
    
    # Add all-day flag
    if event.get('all_day'):
        formatted_event['allDay'] = True
    
    # Add color based on category
    category_colors = {
        'Family': '#4285F4',  # Blue
        'Work': '#EA4335',    # Red
        'School': '#FBBC05',  # Yellow
        'Sports': '#34A853',  # Green
        'Health': '#8E24AA',  # Purple
        'Social': '#FB8C00',  # Orange
        'Other': '#9E9E9E'    # Gray
    }
    
    if event.get('category') and event['category'] in category_colors:
        formatted_event['backgroundColor'] = category_colors[event['category']]
    else:
        # Default color
        formatted_event['backgroundColor'] = '#4285F4'
    
    # Add border color for shared events
    if not is_family_event:
        formatted_event['borderColor'] = '#FF5722'  # Deep Orange
        formatted_event['textColor'] = '#FFFFFF'
    
    # Add extended properties
    formatted_event['extendedProps'] = {
        'description': event.get('description', ''),
        'location': event.get('location', ''),
        'category': event.get('category', ''),
        'created_by': event.get('created_by', ''),
        'family_id': event.get('family_id', ''),
        'shared_with': event.get('shared_with', ''),
        'is_recurring': event.get('is_recurring', False),
        'recurrence_pattern': event.get('recurrence_pattern', '')
    }
    
    return formatted_event

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
            category = request.form.get('category', 'family')
            
            # Get recurring event options
            is_recurring = 'is_recurring' in request.form
            recurrence_pattern = request.form.get('recurrence_pattern')
            recurrence_end_date = request.form.get('recurrence_end_date')
            
            # Get RSVP options
            rsvp_enabled = 'rsvp_enabled' in request.form
            rsvp_deadline = request.form.get('rsvp_deadline')
            rsvp_notify = 'rsvp_notify' in request.form
            
            # Get reminder options
            reminder_enabled = 'reminder_enabled' in request.form
            reminder_time = request.form.get('reminder_time')
            notification_method = request.form.get('notification_method')
            
            # Get shared with families
            shared_with = request.form.getlist('shared_with')
            
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
                'category': category,
                'family_id': current_user.family_id,
                'created_by': current_user.id,
                'is_recurring': is_recurring,
                'recurrence_pattern': recurrence_pattern if is_recurring else None,
                'recurrence_end_date': recurrence_end_date if is_recurring and recurrence_end_date else None,
                'rsvp_enabled': rsvp_enabled,
                'rsvp_deadline': rsvp_deadline if rsvp_enabled and rsvp_deadline else None,
                'rsvp_notify': rsvp_notify if rsvp_enabled else False,
                'reminder_enabled': reminder_enabled,
                'reminder_time': reminder_time if reminder_enabled else None,
                'notification_method': notification_method if reminder_enabled else None,
                'shared_with': shared_with if shared_with else None
            }
            
            event_insert = db.table('events').insert(event_data).execute()
            
            # If this was created from a template and user wants to save updates back to template
            template_id = request.form.get('template_id')
            update_template = 'update_template' in request.form
            
            if template_id and update_template:
                template_data = {
                    'event_title': title,
                    'event_category': category,
                    'event_location': location,
                    'event_description': description,
                    'all_day': time_str == '',
                    'event_time': time_str,
                    'recurrence_pattern': recurrence_pattern,
                    'updated_at': datetime.now().isoformat()
                }
                
                # Update the template with the new values
                template_update = db.table('calendar_templates').update(template_data).eq('id', template_id).eq('family_id', current_user.family_id).execute()
                flash('Event added and template updated successfully', 'success')
            else:
                flash('Event added successfully', 'success')
                
            return redirect(url_for('calendar'))
        except Exception as e:
            flash(f'Error adding event: {str(e)}', 'danger')
            return render_template('add_event.html')
    
    # GET request - show the form
    # Get other families the user can share events with
    from database import db
    families_response = db.table('families').select('id, name').neq('id', current_user.family_id).execute()
    families = families_response.data
    
    # Check if we're using a template
    template_id = request.args.get('template_id')
    template = None
    
    if template_id:
        # Get the template data
        template_result = db.table('calendar_templates').select('*').eq('id', template_id).eq('family_id', current_user.family_id).execute()
        if template_result.data:
            template = template_result.data[0]
    
    # Pre-populate form fields from query parameters (used by template system)
    form_data = {
        'title': request.args.get('title', ''),
        'category': request.args.get('category', 'Family'),
        'location': request.args.get('location', ''),
        'description': request.args.get('description', ''),
        'all_day': request.args.get('all_day') == 'true',
        'start_time': request.args.get('start_time', ''),
        'end_time': request.args.get('end_time', ''),
        'recurrence': request.args.get('recurrence', ''),
        'template_id': template_id
    }
    
    return render_template('add_event.html', families=families, template=template, form_data=form_data)

@app.route('/event/<event_id>')
@login_required
def get_event(event_id):
    """Get event details for display in modal."""
    from database import db
    
    # Check if this is a recurring event instance
    if '_' in event_id:
        # This is a recurring event instance
        base_id, instance_date = event_id.split('_', 1)
        
        # Get the base event
        event_response = db.table('events').select('*').eq('id', base_id).execute()
        
        if not event_response.data:
            return jsonify({'error': 'Event not found'}), 404
            
        event = event_response.data[0]
        
        # Override the date with the instance date
        event['date'] = instance_date
        event['is_instance'] = True
        event['instance_id'] = event_id
    else:
        # Regular event
        event_response = db.table('events').select('*').eq('id', event_id).execute()
        
        if not event_response.data:
            return jsonify({'error': 'Event not found'}), 404
            
        event = event_response.data[0]
    
    # Get RSVP responses if enabled
    rsvp_responses = []
    if event.get('rsvp_enabled'):
        rsvp_response = db.table('event_rsvps').select('*').eq('event_id', event_id).execute()
        if rsvp_response.data:
            # Get usernames for each RSVP
            for rsvp in rsvp_response.data:
                user_response = db.table('users').select('username').eq('id', rsvp['user_id']).execute()
                username = user_response.data[0]['username'] if user_response.data else 'Unknown'
                
                rsvp_responses.append({
                    'user_id': rsvp['user_id'],
                    'username': username,
                    'response': rsvp['response']
                })
    
    # Check if user can edit this event
    can_edit = event['created_by'] == current_user.id or current_user.role == 'Admin'
    
    # Format response
    response = {
        'id': event_id,
        'title': event['title'],
        'date': event['date'],
        'time': event['time'],
        'description': event.get('description', ''),
        'location': event.get('location', ''),
        'category': event.get('category', 'family'),
        'is_recurring': event.get('is_recurring', False),
        'recurrence_pattern': event.get('recurrence_pattern', ''),
        'rsvp_enabled': event.get('rsvp_enabled', False),
        'rsvp_responses': rsvp_responses,
        'reminder_enabled': event.get('reminder_enabled', False),
        'reminder_time': event.get('reminder_time', '60'),
        'notification_method': event.get('notification_method', 'app'),
        'can_edit': can_edit
    }
    
    return jsonify(response)

@app.route('/event_rsvp', methods=['POST'])
@login_required
def event_rsvp():
    """Handle RSVP responses for events."""
    from database import db
    
    try:
        data = request.json
        event_id = data.get('event_id')
        response_type = data.get('response')
        
        if not event_id or not response_type:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
            
        # Check if event exists
        if '_' in event_id:
            # This is a recurring event instance
            base_id = event_id.split('_', 1)[0]
            event_response = db.table('events').select('*').eq('id', base_id).execute()
        else:
            event_response = db.table('events').select('*').eq('id', event_id).execute()
            
        if not event_response.data:
            return jsonify({'success': False, 'message': 'Event not found'}), 404
            
        # Check if user already responded
        rsvp_response = db.table('event_rsvps').select('*').eq('event_id', event_id).eq('user_id', current_user.id).execute()
        
        if rsvp_response.data:
            # Update existing RSVP
            db.table('event_rsvps').update({'response': response_type}).eq('event_id', event_id).eq('user_id', current_user.id).execute()
        else:
            # Create new RSVP
            import uuid
            rsvp_id = str(uuid.uuid4())
            
            rsvp_data = {
                'id': rsvp_id,
                'event_id': event_id,
                'user_id': current_user.id,
                'response': response_type,
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            db.table('event_rsvps').insert(rsvp_data).execute()
        
        # Get updated RSVP responses
        updated_rsvp_response = db.table('event_rsvps').select('*').eq('event_id', event_id).execute()
        rsvp_responses = []
        
        for rsvp in updated_rsvp_response.data:
            user_response = db.table('users').select('username').eq('id', rsvp['user_id']).execute()
            username = user_response.data[0]['username'] if user_response.data else 'Unknown'
            
            rsvp_responses.append({
                'user_id': rsvp['user_id'],
                'username': username,
                'response': rsvp['response']
            })
        
        return jsonify({'success': True, 'responses': rsvp_responses})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/update_event_dates', methods=['POST'])
@login_required
def update_event_dates():
    """Update event dates after drag and drop or resize."""
    from database import db
    
    try:
        data = request.json
        event_id = data.get('event_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if not event_id or not start_date:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        # Check if this is a recurring event instance
        if '_' in event_id:
            # For recurring instances, we create an exception
            base_id, instance_date = event_id.split('_', 1)
            
            # Get the base event
            event_response = db.table('events').select('*').eq('id', base_id).execute()
            
            if not event_response.data:
                return jsonify({'success': False, 'message': 'Event not found'}), 404
                
            base_event = event_response.data[0]
            
            # Create an exception for this instance
            import uuid
            exception_id = str(uuid.uuid4())
            
            exception_data = {
                'id': exception_id,
                'event_id': base_id,
                'original_date': instance_date,
                'new_date': start_date,
                'end_date': end_date
            }
            
            db.table('event_exceptions').insert(exception_data).execute()
        else:
            # Regular event update
            update_data = {'date': start_date}
            if end_date:
                update_data['end_date'] = end_date
                
            db.table('events').update(update_data).eq('id', event_id).execute()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/import_calendar', methods=['POST'])
@login_required
def import_calendar():
    """Import events from external calendar."""
    from database import db
    import uuid
    
    try:
        source = request.form.get('source')
        sync = 'sync' in request.form
        
        # In a real implementation, this would handle different calendar sources
        # For now, we'll just handle iCal file uploads
        if 'calendar_file' in request.files:
            file = request.files['calendar_file']
            
            if file.filename == '':
                return jsonify({'success': False, 'message': 'No file selected'}), 400
                
            if file:
                # Process the iCal file
                # This is a simplified version - a real implementation would use a library like icalendar
                # to properly parse the file
                
                # Mock implementation - just create a sample event
                event_id = str(uuid.uuid4())
                
                event_data = {
                    'id': event_id,
                    'title': 'Imported Event',
                    'date': '2025-03-15',
                    'time': '14:00:00',
                    'description': 'This event was imported from an external calendar',
                    'location': 'External Location',
                    'category': 'family',
                    'family_id': current_user.family_id,
                    'created_by': current_user.id,
                    'is_recurring': False
                }
                
                db.table('events').insert(event_data).execute()
                
                return jsonify({'success': True, 'message': 'Calendar imported successfully'})
        
        return jsonify({'success': False, 'message': 'No file uploaded or unsupported source'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/export_calendar')
@login_required
def export_calendar():
    """Export calendar events to iCal format."""
    try:
        from database import db
        import datetime
        from icalendar import Calendar, ICalEvent, vText
        from flask import Response
        import pytz
        
        # Get filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category = request.args.get('category')
        member_id = request.args.get('member_id')
        include_shared = request.args.get('include_shared', 'true') == 'true'
        
        # Get all events for the user's family
        query = db.table('events').select('*').eq('family_id', current_user.family_id)
        
        # Apply date filters if provided
        if start_date:
            query = query.gte('date', start_date)
        if end_date:
            query = query.lte('date', end_date)
            
        # Apply category filter if provided
        if category and category != 'all':
            query = query.eq('category', category)
            
        # Apply member filter if provided
        if member_id and member_id != 'all':
            query = query.eq('created_by', member_id)
            
        events_response = query.execute()
        events = events_response.data
        
        # Also get shared events that this family can see
        shared_events = []
        if include_shared:
            shared_query = db.table('events').select('*').neq('family_id', current_user.family_id)
            
            # Apply date filters if provided
            if start_date:
                shared_query = shared_query.gte('date', start_date)
            if end_date:
                shared_query = shared_query.lte('date', end_date)
                
            # Apply category filter if provided
            if category and category != 'all':
                shared_query = shared_query.eq('category', category)
                
            shared_response = shared_query.execute()
            
            # Filter shared events to only include those shared with this family
            for event_data in shared_response.data:
                shared_with = event_data.get('shared_with', '')
                if shared_with and current_user.family_id in shared_with.split(','):
                    events.append(event_data)
        
        # Create a new calendar
        cal = Calendar()
        cal.add('prodid', '-//FamilySphere//familysphere.app//')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        cal.add('x-wr-calname', f'FamilySphere - {current_user.username}\'s Family Calendar')
        
        # Add events to the calendar
        for event in events:
            event = ICalEvent()
            
            # Required fields
            event.add('summary', event['title'])
            
            # Convert date string to datetime
            event_date = datetime.datetime.strptime(event['date'], '%Y-%m-%d').date()
            
            # Handle all-day events vs. timed events
            if event.get('all_day'):
                # All-day events need a DATE value
                event.add('dtstart', event_date, parameters={'VALUE': 'DATE'})
                
                # For all-day events, the end date should be the day after (per iCalendar spec)
                end_date = event_date + datetime.timedelta(days=1)
                event.add('dtend', end_date, parameters={'VALUE': 'DATE'})
            else:
                # Add time if available
                if event.get('time'):
                    try:
                        # Try parsing with seconds
                        event_time = datetime.datetime.strptime(event['time'], '%H:%M:%S').time()
                    except ValueError:
                        # If that fails, try without seconds
                        event_time = datetime.datetime.strptime(event['time'], '%H:%M').time()
                    
                    event_start = datetime.datetime.combine(event_date, event_time)
                    
                    # Add timezone information (assuming Eastern Time - can be customized later)
                    local_tz = pytz.timezone('America/New_York')
                    event_start = local_tz.localize(event_start)
                    
                    event.add('dtstart', event_start)
                    
                    # Add end time if available, otherwise default to 1 hour
                    if event.get('end_time'):
                        try:
                            # Try parsing with seconds
                            end_time = datetime.datetime.strptime(event['end_time'], '%H:%M:%S').time()
                        except ValueError:
                            # If that fails, try without seconds
                            end_time = datetime.datetime.strptime(event['end_time'], '%H:%M').time()
                            
                        end_datetime = datetime.datetime.combine(event_date, end_time)
                        end_datetime = local_tz.localize(end_datetime)
                    else:
                        end_datetime = event_start + datetime.timedelta(hours=1)
                    
                    event.add('dtend', end_datetime)
                else:
                    # Fallback for events with date but no time
                    event.add('dtstart', event_date, parameters={'VALUE': 'DATE'})
                    event.add('dtend', event_date + datetime.timedelta(days=1), parameters={'VALUE': 'DATE'})
            
            # Optional fields
            if event.get('description'):
                event.add('description', event['description'])
            
            if event.get('location'):
                event.add('location', vText(event['location']))
            
            # Add category
            if event.get('category'):
                event.add('categories', event['category'])
            
            # Add unique ID
            event.add('uid', f"{event['id']}@familysphere.app")
            
            # Add creation timestamp
            event.add('dtstamp', datetime.datetime.now(pytz.utc))
            
            # Handle recurring events
            if event.get('is_recurring') or event.get('recurrence_pattern'):
                recurrence_pattern = event.get('recurrence_pattern')
                
                if recurrence_pattern == 'daily':
                    event.add('rrule', {'FREQ': 'DAILY'})
                elif recurrence_pattern == 'weekly':
                    event.add('rrule', {'FREQ': 'WEEKLY'})
                elif recurrence_pattern == 'biweekly':
                    event.add('rrule', {'FREQ': 'WEEKLY', 'INTERVAL': 2})
                elif recurrence_pattern == 'monthly':
                    event.add('rrule', {'FREQ': 'MONTHLY'})
                elif recurrence_pattern == 'yearly':
                    event.add('rrule', {'FREQ': 'YEARLY'})
                
                # Add end date if specified
                if event.get('recurrence_end_date'):
                    end_date = datetime.datetime.strptime(event['recurrence_end_date'], '%Y-%m-%d').date()
                    event.add('rrule', {'UNTIL': end_date})
            
            # Add organizer if available
            if event.get('created_by'):
                # Get user info
                user_response = db.table('users').select('username, email').eq('id', event['created_by']).execute()
                if user_response.data:
                    user = user_response.data[0]
                    if user.get('email'):
                        event.add('organizer', f"mailto:{user['email']}")
            
            # Add the event to the calendar
            cal.add_component(event)
        
        # Generate iCal file
        ical_data = cal.to_ical()
        
        # Create response with iCal data
        response = Response(ical_data, mimetype='text/calendar')
        filename = f"familysphere_calendar_{datetime.datetime.now().strftime('%Y%m%d')}.ics"
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        # Add success flash message
        flash("Calendar exported successfully!", "success")
        
        return response
    
    except Exception as e:
        app.logger.error(f"Error exporting calendar: {str(e)}")
        flash(f"Error exporting calendar: {str(e)}", "danger")
        return redirect(url_for('calendar'))

@app.route('/event_reminders')
@login_required
def event_reminders():
    """Display and manage event reminders for the user."""
    from database import db
    import datetime
    
    # Get all events with reminders for the user
    events_response = db.table('events').select('*').eq('family_id', current_user.family_id).eq('reminder_enabled', True).execute()
    events_with_reminders = events_response.data
    
    # Current date and time for calculating upcoming reminders
    now = datetime.datetime.now()
    
    # Process events to determine upcoming reminders
    upcoming_reminders = []
    for event in events_with_reminders:
        event_date = datetime.datetime.strptime(f"{event['date']}T{event['time'] if event['time'] else '00:00:00'}", "%Y-%m-%dT%H:%M:%S")
        
        # Calculate reminder time based on minutes before event
        reminder_minutes = int(event.get('reminder_time', 60))  # Default to 1 hour if not specified
        reminder_time = event_date - datetime.timedelta(minutes=reminder_minutes)
        
        # Only include future reminders
        if reminder_time > now:
            upcoming_reminders.append({
                'event_id': event['id'],
                'title': event['title'],
                'event_date': event_date,
                'reminder_time': reminder_time,
                'minutes_before': reminder_minutes,
                'notification_method': event.get('notification_method', 'app')
            })
    
    # Sort reminders by reminder time
    upcoming_reminders.sort(key=lambda x: x['reminder_time'])
    
    return render_template('event_reminders.html', reminders=upcoming_reminders)

@app.route('/check_reminders')
@login_required
def check_reminders():
    """API endpoint to check for due reminders."""
    from database import db
    import datetime
    
    # Get all events with reminders for the user
    events_response = db.table('events').select('*').eq('family_id', current_user.family_id).eq('reminder_enabled', True).execute()
    events_with_reminders = events_response.data
    
    # Current date and time
    now = datetime.datetime.now()
    
    # Process events to determine due reminders
    due_reminders = []
    for event in events_with_reminders:
        event_date = datetime.datetime.strptime(f"{event['date']}T{event['time'] if event['time'] else '00:00:00'}", "%Y-%m-%dT%H:%M:%S")
        
        # Calculate reminder time based on minutes before event
        reminder_minutes = int(event.get('reminder_time', 60))  # Default to 1 hour if not specified
        reminder_time = event_date - datetime.timedelta(minutes=reminder_minutes)
        
        # Check if reminder is due (within the last 5 minutes)
        time_diff = (now - reminder_time).total_seconds() / 60
        if 0 <= time_diff <= 5:  # Reminder is due within the last 5 minutes
            due_reminders.append({
                'event_id': event['id'],
                'title': event['title'],
                'event_date': event_date.strftime("%Y-%m-%d %H:%M"),
                'notification_method': event.get('notification_method', 'app')
            })
    
    return jsonify({'reminders': due_reminders})

@app.route('/update_reminder_preferences', methods=['POST'])
@login_required
def update_reminder_preferences():
    """Update user's reminder preferences."""
    from database import db
    
    try:
        data = request.json
        event_id = data.get('event_id')
        reminder_enabled = data.get('reminder_enabled', False)
        reminder_time = data.get('reminder_time')
        notification_method = data.get('notification_method')
        
        if not event_id:
            return jsonify({'success': False, 'message': 'Missing event ID'}), 400
            
        # Check if user can edit this event
        event_response = db.table('events').select('created_by').eq('id', event_id).execute()
        if not event_response.data:
            return jsonify({'success': False, 'message': 'Event not found'}), 404
            
        event = event_response.data[0]
        if event['created_by'] != current_user.id and current_user.role != 'Admin':
            return jsonify({'success': False, 'message': 'Not authorized to update this event'}), 403
            
        # Update reminder settings
        update_data = {
            'reminder_enabled': reminder_enabled
        }
        
        if reminder_enabled:
            update_data['reminder_time'] = reminder_time
            update_data['notification_method'] = notification_method
        
        db.table('events').update(update_data).eq('id', event_id).execute()
        
        return jsonify({'success': True, 'message': 'Reminder preferences updated'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

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
            finance_type = request.form.get('type')
            amount = request.form.get('amount')
            title = request.form.get('title', '')
            description = request.form.get('description', '')
            category = request.form.get('category', 'General')
            due_date = request.form.get('due_date', '')
            recurring = 'recurring' in request.form
            assigned_to = request.form.get('assigned_to', '')
            target_date = request.form.get('target_date', '')
            priority = request.form.get('priority', 'Medium')
            
            # Validate input
            if not finance_type or not amount:
                flash('Type and amount are required', 'danger')
                return render_template('add_finance.html')
            
            # Create new finance record
            import uuid
            from datetime import datetime
            
            finance_id = str(uuid.uuid4())
            
            # Prepare finance data based on type
            finance_data = {
                'id': finance_id,
                'type': finance_type,
                'amount': float(amount),
                'description': description,
                'family_id': current_user.family_id,
                'created_by': current_user.id,
                'created_at': datetime.now().isoformat()
            }
            
            # Add type-specific fields
            if finance_type == 'Budget':
                finance_data['title'] = title or 'Monthly Budget'
                finance_data['category'] = category
                finance_data['recurring'] = recurring
                
            elif finance_type == 'Expense':
                finance_data['title'] = title or 'Expense'
                finance_data['category'] = category
                finance_data['date'] = due_date or datetime.now().isoformat()
                finance_data['paid_by'] = assigned_to or current_user.id
                
            elif finance_type == 'Goal':
                finance_data['title'] = title or 'Savings Goal'
                finance_data['target_date'] = target_date
                finance_data['current_amount'] = 0.0
                finance_data['target_amount'] = float(amount)
                finance_data['priority'] = priority
                
            elif finance_type == 'Allowance':
                finance_data['title'] = title or 'Allowance'
                finance_data['assigned_to'] = assigned_to
                finance_data['recurring'] = recurring
                finance_data['frequency'] = request.form.get('frequency', 'Weekly')
            
            # Insert finance record into database
            finance_insert = db.table('finances').insert(finance_data).execute()
            
            flash(f'{finance_type} added successfully', 'success')
            return redirect(url_for('finances'))
        except Exception as e:
            flash(f'Error adding finance record: {str(e)}', 'danger')
            return render_template('add_finance.html')
    
    # GET request - show the form
    family_members = []
    try:
        from database import db
        # Get family members for assignment
        family_data = db.table('users').select('id', 'username').eq('family_id', current_user.family_id).execute()
        if family_data and hasattr(family_data, 'data'):
            family_members = family_data.data
    except Exception as e:
        print(f"Error getting family members: {e}")
    
    return render_template('add_finance.html', family_members=family_members)

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
        try:
            title = request.form.get('title')
            description = request.form.get('description', '')
            photo_url = request.form.get('photo_url', '')  # In a real app, this would be file upload
            memory_date = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))
            location = request.form.get('location', '')
            tags = request.form.get('tags', '')
            album_id = request.form.get('album_id', '')
            privacy = request.form.get('privacy', 'family') # family, private, shared
            
            # Create new memory with UUID
            memory_id = str(uuid.uuid4())
            memory_data = {
                'id': memory_id,
                'title': title,
                'description': description,
                'photo_url': photo_url,
                'date': memory_date,
                'location': location,
                'tags': tags,
                'privacy': privacy,
                'family_id': current_user.family_id,
                'created_by': current_user.id,
                'created_at': datetime.now().isoformat()
            }
            
            # Add to album if specified
            if album_id:
                memory_data['album_id'] = album_id
                
                # Check if album exists, create if not
                album_check = db.table('albums').select('id').eq('id', album_id).execute()
                if not album_check.data:
                    # Get album name or use default
                    album_name = request.form.get('album_name', 'Unnamed Album')
                    album_data = {
                        'id': album_id,
                        'name': album_name,
                        'description': f"Album created on {datetime.now().strftime('%Y-%m-%d')}",
                        'cover_photo_id': memory_id,
                        'family_id': current_user.family_id,
                        'created_by': current_user.id,
                        'created_at': datetime.now().isoformat()
                    }
                    db.table('albums').insert(album_data).execute()
            
            # Insert memory into database
            db.table('memories').insert(memory_data).execute()
            
            # Process people tags (family members in the photo)
            people_tags = request.form.getlist('people')
            if people_tags:
                for person_id in people_tags:
                    tag_id = str(uuid.uuid4())
                    tag_data = {
                        'id': tag_id,
                        'memory_id': memory_id,
                        'user_id': person_id,
                        'created_at': datetime.now().isoformat()
                    }
                    db.table('memory_people').insert(tag_data).execute()
            
            flash('Memory added successfully!', 'success')
            return redirect(url_for('memories'))
        except Exception as e:
            flash(f'Error adding memory: {str(e)}', 'danger')
            return render_template('add_memory.html')
            
    # For GET request, get family members and albums for dropdown
    family_members = []
    albums = []
    try:
        # Get family members for tagging
        family_data = db.table('users').select('id', 'username').eq('family_id', current_user.family_id).execute()
        if family_data and hasattr(family_data, 'data'):
            family_members = family_data.data
            
        # Get existing albums
        albums_data = db.table('albums').select('id', 'name').eq('family_id', current_user.family_id).execute()
        if albums_data and hasattr(albums_data, 'data'):
            albums = albums_data.data
    except Exception as e:
        print(f"Error retrieving data for memory form: {e}")
        
    return render_template('add_memory.html', family_members=family_members, albums=albums)

@app.route('/memories/album/add', methods=['POST'])
@login_required
def add_album():
    """Add a new photo album."""
    from database import db
    import uuid
    from datetime import datetime
    
    name = request.form.get('name')
    description = request.form.get('description', '')
    
    # Create new album with UUID
    album_id = str(uuid.uuid4())
    album_data = {
        'id': album_id,
        'name': name,
        'description': description,
        'family_id': current_user.family_id,
        'created_by': current_user.id,
        'created_at': datetime.now().isoformat()
    }
    
    # Insert album into database
    db.table('albums').insert(album_data).execute()
    
    flash('Album created successfully!', 'success')
    return redirect(url_for('memories'))

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
    """Add a new inventory item."""
    from database import db
    import uuid
    
    item_name = request.form.get('item_name')
    quantity = int(request.form.get('quantity', 1))
    category = request.form.get('category', 'General')
    location = request.form.get('location', '')
    notes = request.form.get('notes', '')
    purchase_date = request.form.get('purchase_date', '')
    expiration_date = request.form.get('expiration_date', '')
    low_stock_threshold = request.form.get('low_stock_threshold', '')
    unit = request.form.get('unit', '')
    price = request.form.get('price', '')
    barcode = request.form.get('barcode', '')
    auto_replenish = 'auto_replenish' in request.form
    
    # Convert low_stock_threshold to int if provided
    if low_stock_threshold:
        try:
            low_stock_threshold = int(low_stock_threshold)
        except ValueError:
            low_stock_threshold = None
    
    # Convert price to float if provided
    if price:
        try:
            price = float(price)
        except ValueError:
            price = None
    
    # Create new inventory item with UUID
    item_id = str(uuid.uuid4())
    item_data = {
        'id': item_id,
        'item_name': item_name,
        'quantity': quantity,
        'category': category,
        'location': location,
        'notes': notes,
        'purchase_date': purchase_date,
        'family_id': current_user.family_id,
        'created_by': current_user.id,
        'created_at': datetime.now().isoformat(),
        'last_updated': datetime.now().isoformat()
    }
    
    # Add optional fields if they exist
    if expiration_date:
        item_data['expiration_date'] = expiration_date
    
    if low_stock_threshold is not None:
        item_data['low_stock_threshold'] = low_stock_threshold
    
    if unit:
        item_data['unit'] = unit
    
    if price is not None:
        item_data['price'] = price
    
    if barcode:
        item_data['barcode'] = barcode
    
    item_data['auto_replenish'] = auto_replenish
    
    # Insert item into database
    db.table('inventory').insert(item_data).execute()
    
    # Check if below threshold and add to shopping list if auto_replenish is enabled
    if auto_replenish and low_stock_threshold is not None and quantity <= low_stock_threshold:
        try:
            # Add to shopping list
            shopping_item_id = str(uuid.uuid4())
            shopping_item = {
                'id': shopping_item_id,
                'item_name': item_name,
                'quantity': max(low_stock_threshold - quantity + 1, 1),  # At least 1
                'inventory_item_id': item_id,
                'family_id': current_user.family_id,
                'created_by': current_user.id,
                'created_at': datetime.now().isoformat(),
                'status': 'Active'
            }
            db.table('shopping_list').insert(shopping_item).execute()
            flash(f'Item added to inventory successfully! Also added to shopping list due to low stock.')
        except Exception as e:
            flash(f'Item added to inventory successfully! (Shopping list error: {str(e)})')
    else:
        flash('Item added to inventory successfully!')
    
    return redirect(url_for('inventory'))

@app.route('/inventory/update/<item_id>', methods=['POST'])
@login_required
def update_inventory_item(item_id):
    """Update an inventory item's quantity"""
    from database import db
    from datetime import datetime
    
    action = request.form.get('action')
    quantity = int(request.form.get('quantity', 1))
    
    try:
        # Get current item data
        item_response = db.table('inventory').select('*').eq('id', item_id).single().execute()
        if not item_response.data:
            flash('Item not found!', 'danger')
            return redirect(url_for('inventory'))
        
        item = item_response.data
        current_quantity = item.get('quantity', 0)
        low_stock_threshold = item.get('low_stock_threshold')
        
        # Update quantity based on action
        if action == 'increment':
            new_quantity = current_quantity + quantity
        elif action == 'decrement':
            new_quantity = max(0, current_quantity - quantity)
        else:  # Set to specific value
            new_quantity = quantity
        
        # Update item in database
        db.table('inventory').update({
            'quantity': new_quantity,
            'last_updated': datetime.now().isoformat()
        }).eq('id', item_id).execute()
        
        # Check if below threshold for auto-replenish
        if item.get('auto_replenish', False) and low_stock_threshold is not None and new_quantity <= low_stock_threshold:
            # Check if already in shopping list
            shopping_check = db.table('shopping_list').select('id').eq('inventory_item_id', item_id).eq('status', 'Active').execute()
            
            if not shopping_check.data:
                # Add to shopping list
                import uuid
                shopping_item_id = str(uuid.uuid4())
                shopping_item = {
                    'id': shopping_item_id,
                    'item_name': item.get('item_name'),
                    'quantity': max(low_stock_threshold - new_quantity + 1, 1),  # At least 1
                    'inventory_item_id': item_id,
                    'family_id': current_user.family_id,
                    'created_by': current_user.id,
                    'created_at': datetime.now().isoformat(),
                    'status': 'Active'
                }
                db.table('shopping_list').insert(shopping_item).execute()
                flash(f'Item updated! Also added to shopping list due to low stock.')
            else:
                flash('Item updated successfully!')
        else:
            flash('Item updated successfully!')
            
    except Exception as e:
        flash(f'Error updating item: {str(e)}', 'danger')
    
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
    
    # Add type-specific fields
    if record_type == 'medication':
        medication = request.form.get('medication', '')
        dosage = request.form.get('dosage', '')
        schedule = request.form.get('schedule', '')
        notes = request.form.get('notes', '')
        reminder_time = request.form.get('reminder_time')
        start_date = request.form.get('start_date', datetime.now().strftime('%Y-%m-%d'))
        end_date = request.form.get('end_date', '')
        
        record_data.update({
            'medication': medication,
            'dosage': dosage,
            'schedule': schedule,
            'notes': notes,
            'reminder_time': reminder_time,
            'start_date': start_date
        })
        
        if end_date:
            record_data['end_date'] = end_date
            
    elif record_type == 'appointment':
        doctor = request.form.get('doctor', '')
        specialty = request.form.get('specialty', '')
        location = request.form.get('location', '')
        date = request.form.get('date', '')
        time = request.form.get('time', '')
        notes = request.form.get('notes', '')
        reminder = 'reminder' in request.form
        
        record_data.update({
            'doctor': doctor,
            'specialty': specialty,
            'location': location,
            'date': date,
            'time': time,
            'notes': notes,
            'reminder': reminder
        })
        
    elif record_type == 'measurement':
        measurement_type = request.form.get('measurement_type', '') # weight, height, blood pressure, etc.
        value = request.form.get('value', '')
        unit = request.form.get('unit', '')
        date = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))
        notes = request.form.get('notes', '')
        
        record_data.update({
            'measurement_type': measurement_type,
            'value': value,
            'unit': unit,
            'date': date,
            'notes': notes
        })
        
    elif record_type == 'allergy':
        allergen = request.form.get('allergen', '')
        severity = request.form.get('severity', 'Medium') # Mild, Medium, Severe
        symptoms = request.form.get('symptoms', '')
        treatment = request.form.get('treatment', '')
        notes = request.form.get('notes', '')
        
        record_data.update({
            'allergen': allergen,
            'severity': severity,
            'symptoms': symptoms,
            'treatment': treatment,
            'notes': notes
        })
        
    elif record_type == 'immunization':
        vaccine = request.form.get('vaccine', '')
        date = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))
        location = request.form.get('location', '')
        next_due = request.form.get('next_due', '')
        notes = request.form.get('notes', '')
        
        record_data.update({
            'vaccine': vaccine,
            'date': date,
            'location': location,
            'notes': notes
        })
        
        if next_due:
            record_data['next_due'] = next_due
    
    # Insert record into database
    db.table('health').insert(record_data).execute()
    
    # Set reminder if needed for medication or appointment
    if record_type in ['medication', 'appointment'] and record_data.get('reminder_time') or record_data.get('reminder'):
        try:
            reminder_id = str(uuid.uuid4())
            reminder_data = {
                'id': reminder_id,
                'user_id': user_id,
                'type': f'health_{record_type}',
                'record_id': record_id,
                'time': record_data.get('reminder_time') or f"{record_data.get('date')} {record_data.get('time')}",
                'message': f"Reminder: {record_data.get('medication') if record_data.get('medication') else 'Appointment with ' + str(record_data.get('doctor', ''))}",
                'status': 'Active',
                'created_at': datetime.now().isoformat()
            }
            db.table('reminders').insert(reminder_data).execute()
            flash(f'Health record added successfully with reminder!')
        except Exception as e:
            flash(f'Health record added successfully! (Reminder error: {str(e)})')
    else:
        flash('Health record added successfully!')
    
    return redirect(url_for('health'))

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
    
    # Get family members for medical information
    family_members_response = db.table('users').select('*').eq('family_id', current_user.family_id).execute()
    family_members = family_members_response.data
    
    # Get medications for each family member
    for member in family_members:
        medications_response = db.table('health').select('*').eq('user_id', member['id']).execute()
        member['medications'] = medications_response.data
    
    # In a real app, this would come from a location tracking table
    # For now, we'll return an empty list - the UI will handle this gracefully
    family_locations = []
    
    spherebot_suggestion = get_spherebot_suggestion("emergency")
    
    return render_template('emergency.html', 
                          active_emergencies=active_emergencies,
                          emergency_contacts=emergency_contacts,
                          family_members=family_members,
                          family_locations=family_locations,
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
    is_medical = 'is_medical' in request.form
    
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
        'is_medical': is_medical,
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
    
    # Get family information
    family_response = db.table('families').select('*').eq('id', current_user.family_id).execute()
    family_name = family_response.data[0]['name'] if family_response.data else 'No Family'
    
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
    
    # Add family name to settings
    user_settings['family_name'] = family_name
    
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
@csrf.exempt  # Exempt this route from CSRF protection for testing
@login_required
def spherebot_query():
    """Handle SphereBot AI queries and return responses."""
    try:
        # Validate request
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
            
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({"error": "Missing query parameter"}), 400
            
        query = data['query']
        if not query or not isinstance(query, str):
            return jsonify({"error": "Invalid query parameter"}), 400
        
        # Get the Grok API settings
        grok_api_key = current_app.config.get('GROK_API_KEY')
        grok_api_url = current_app.config.get('GROK_API_URL')
        grok_model = current_app.config.get('GROK_MODEL')
        
        # Determine the context based on the query content
        context_keywords = {
            "calendar": ["calendar", "schedule", "event", "appointment", "meeting", "remind", "when"],
            "tasks": ["task", "chore", "assignment", "todo", "to-do", "to do", "work", "job"],
            "finance": ["money", "budget", "finance", "spending", "expense", "cost", "save", "bill", "payment"],
            "chat": ["message", "chat", "conversation", "talk", "discuss", "communicate"],
            "memory": ["photo", "picture", "memory", "album", "remember", "moment", "capture"],
            "inventory": ["inventory", "item", "stock", "supply", "grocery", "shopping", "list"],
            "health": ["health", "medication", "medicine", "doctor", "appointment", "prescription"],
            "emergency": ["emergency", "contact", "urgent", "crisis", "help", "sos"],
            "family": ["family", "member", "relative", "relationship", "invite", "join"]
        }
        
        context = "general"
        for ctx, keywords in context_keywords.items():
            if any(keyword in query.lower() for keyword in keywords):
                context = ctx
                break
                
        print(f"Determined context: {context}")
        
        # Gather relevant context data based on the determined context
        context_data = {}
        
        if current_user.is_authenticated:
            # Add user info
            context_data['user'] = {
                'id': current_user.id,
                'username': current_user.username,
                'role': current_user.role,
                'family_id': current_user.family_id
            }
            
            # Add family info if applicable
            if current_user.family_id:
                try:
                    family_response = db.table('families').select('*').eq('id', current_user.family_id).single().execute()
                    if family_response.data:
                        context_data['family'] = family_response.data
                except Exception as e:
                    print(f"Error fetching family data: {str(e)}")
            
            # Add context-specific data
            try:
                if context == "tasks":
                    # Get pending tasks
                    tasks_response = db.table('tasks').select('*').eq('family_id', current_user.family_id).eq('status', 'Pending').order('due_date').execute()
                    if tasks_response.data:
                        context_data['tasks'] = tasks_response.data
                        
                elif context == "calendar":
                    # Get upcoming events
                    today = datetime.now().strftime('%Y-%m-%d')
                    events_response = db.table('events').select('*').eq('family_id', current_user.family_id).gte('date', today).order('date').limit(10).execute()
                    if events_response.data:
                        context_data['events'] = events_response.data
                        
                elif context == "finance":
                    # Get financial data
                    finance_response = db.table('finances').select('*').eq('family_id', current_user.family_id).execute()
                    if finance_response.data:
                        context_data['finances'] = finance_response.data
                        
                elif context == "chat":
                    # Get recent messages
                    chat_response = db.table('chats').select('*').eq('family_id', current_user.family_id).order('timestamp', desc=True).limit(10).execute()
                    if chat_response.data:
                        context_data['messages'] = chat_response.data
                        
                elif context == "memory":
                    # Get recent memories
                    memory_response = db.table('memories').select('*').eq('family_id', current_user.family_id).order('created_at', desc=True).limit(10).execute()
                    if memory_response.data:
                        context_data['memories'] = memory_response.data
                        
                elif context == "inventory":
                    # Get inventory items
                    inventory_response = db.table('inventory').select('*').eq('family_id', current_user.family_id).execute()
                    if inventory_response.data:
                        context_data['inventory'] = inventory_response.data
                        
                elif context == "health":
                    # Get health data
                    health_response = db.table('health').select('*').eq('user_id', current_user.id).execute()
                    if health_response.data:
                        context_data['health'] = health_response.data
                        
                elif context == "family":
                    # Get family members
                    members_response = db.table('users').select('id,username,role').eq('family_id', current_user.family_id).execute()
                    if members_response.data:
                        context_data['members'] = members_response.data
                        
                    # Get connected families
                    connections_response = db.table('family_connections').select('*').or_(
                        f'family_id1.eq.{current_user.family_id},family_id2.eq.{current_user.family_id}'
                    ).execute()
                    if connections_response.data:
                        context_data['connections'] = connections_response.data
            except Exception as e:
                print(f"Error fetching context data: {str(e)}")
        
        # Try to use the Grok API if available
        if grok_api_key and grok_api_url and grok_model:
            try:
                headers = {
                    "Authorization": f"Bearer {grok_api_key}",
                    "Content-Type": "application/json"
                }
                
                # Prepare the prompt with context data
                prompt = f"You are SphereBot, a helpful assistant for the FamilySphere family management app. The user has asked: '{query}'\n\n"
                
                # Add context data to the prompt
                if context_data:
                    prompt += "Here is some relevant context from the app:\n"
                    for key, value in context_data.items():
                        prompt += f"{key}: {json.dumps(value)}\n"
                
                prompt += "\nPlease provide a helpful, friendly response that addresses the user's query."
                
                payload = {
                    "model": grok_model,
                    "messages": [
                        {"role": "system", "content": "You are SphereBot, a helpful assistant for the FamilySphere family management app."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500
                }
                
                response = requests.post(grok_api_url, headers=headers, json=payload, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    if ai_response:
                        return jsonify({"response": ai_response})
                else:
                    print(f"Grok API error: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"Error calling Grok API: {str(e)}")
        
        # If we get here, either the API call failed or the API keys are not set
        # Use our context-aware fallback responses
        query_lower = query.lower()
        
        # Special case for asking why tasks are showing
        if "why" in query_lower and ("task" in query_lower or "telling me" in query_lower):
            return jsonify({
                "response": "I'm showing example tasks because I couldn't connect to the database or the AI service is currently unavailable. When fully connected, I'll show your actual tasks."
            })
        
        # Handle different contexts with specific responses
        if context == "tasks":
            # Check for specific task-related queries
            if any(term in query_lower for term in ["view", "show", "list", "what are", "pending"]):
                # Try to use real tasks from context_data if available
                if 'tasks' in context_data and context_data['tasks']:
                    tasks = context_data['tasks']
                    response_text = "Here are your pending tasks:\n\n"
                    
                    for i, task in enumerate(tasks, 1):
                        due_date = task.get('due_date', 'No due date')
                        title = task.get('title', 'Untitled task')
                        
                        # Format the due date
                        today = datetime.now().strftime('%Y-%m-%d')
                        if due_date == today:
                            due_str = "Due today"
                        else:
                            try:
                                task_date = datetime.strptime(due_date, '%Y-%m-%d').date()
                                due_str = task_date.strftime('%b %d')
                            except:
                                due_str = f"Due {due_date}"
                        
                        response_text += f"{i}. {title} ({due_str})\n"
                    
                    response_text += "\nWould you like to mark any of these as complete?"
                    return jsonify({"response": response_text})
                else:
                    # Fall back to generic response
                    return jsonify({
                        "response": "I couldn't retrieve your tasks at the moment. Please try again later or check the Tasks section of the app."
                    })
            elif any(term in query_lower for term in ["create", "add", "new"]):
                return jsonify({
                    "response": "To create a new task, please provide the following details:\n- Task title\n- Due date\n- Assigned to (optional)\n- Priority (optional)\n\nYou can create tasks directly in the Tasks section of the app."
                })
            elif any(term in query_lower for term in ["assign", "distribute", "give"]):
                # Try to use real family members if available
                if 'members' in context_data and context_data['members']:
                    members = context_data['members']
                    response_text = "You can assign tasks to the following family members:\n"
                    
                    for member in members:
                        response_text += f"- {member['username']} ({member['role']})\n"
                    
                    response_text += "\nWhich task would you like to assign and to whom?"
                    return jsonify({"response": response_text})
                else:
                    return jsonify({
                        "response": "I couldn't retrieve your family members at the moment. You can assign tasks in the Tasks section of the app."
                    })
            elif any(term in query_lower for term in ["complete", "mark", "done", "finish"]):
                return jsonify({
                    "response": "Which task would you like to mark as complete? Please specify the task name or number from your pending tasks list."
                })
            else:
                # General task management options
                return jsonify({
                    "response": "Here are some task management options:\n- View your pending tasks\n- Create a new task\n- Assign tasks to family members to distribute responsibilities\n- Mark tasks as completed"
                })
        elif context == "calendar":
            if any(term in query_lower for term in ["view", "show", "list", "what", "upcoming", "today"]):
                # Try to use real events from context_data if available
                if 'events' in context_data and context_data['events']:
                    events = context_data['events']
                    response_text = "Here are your upcoming events:\n\n"
                    
                    for i, event in enumerate(events, 1):
                        title = event.get('title', 'Untitled event')
                        date = event.get('date', 'No date')
                        time = event.get('time', 'No time')
                        
                        # Format the date
                        today = datetime.now().strftime('%Y-%m-%d')
                        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                        
                        if date == today:
                            date_str = "Today"
                        elif date == tomorrow:
                            date_str = "Tomorrow"
                        else:
                            try:
                                event_date = datetime.strptime(date, '%Y-%m-%d').date()
                                date_str = event_date.strftime('%b %d')
                            except:
                                date_str = date
                        
                        response_text += f"{i}. {title} ({date_str}, {time})\n"
                    
                    return jsonify({"response": response_text})
                else:
                    # Fall back to generic response
                    return jsonify({
                        "response": "I couldn't retrieve your events at the moment. Please try again later or check the Calendar section of the app."
                    })
            else:
                return jsonify({
                    "response": "I can help you manage your family calendar. You can:\n- View upcoming events\n- Add new events\n- Set reminders\n- Share events with family members"
                })
        elif context == "finance":
            if any(term in query_lower for term in ["view", "show", "summary", "overview", "budget", "current"]):
                return jsonify({
                    "response": "Here's your financial summary (sample data):\n\nBudget: $2,500.00\nSpent this month: $1,200.00\nRemaining: $1,300.00\n\nRecent expenses:\n1. Groceries - $120.00 (Yesterday)\n2. Utilities - $180.00 (Feb 28)\n3. Dining out - $65.00 (Feb 27)\n\nNote: This is example financial data for demonstration purposes only."
                })
            elif any(term in query_lower for term in ["add", "new", "record", "expense", "spending"]):
                return jsonify({
                    "response": "To add a new expense, please provide:\n- Amount\n- Category (e.g., Groceries, Utilities, Entertainment)\n- Date (defaults to today)\n- Description (optional)\n\nYou can add expenses in the Finance section of the app."
                })
            elif any(term in query_lower for term in ["set", "create", "update", "change", "modify", "budget"]):
                return jsonify({
                    "response": "To set or update your budget, please provide:\n- Budget amount\n- Time period (Monthly, Weekly, etc.)\n- Start date (optional)\n- Categories with allocations (optional)\n\nYou can manage your budget in the Finance section of the app."
                })
            elif any(term in query_lower for term in ["saving", "goal", "target", "plan"]):
                return jsonify({
                    "response": "Your current savings goals (sample data):\n\n1. Vacation - $1,500/$3,000 (50% complete)\n2. New Appliances - $800/$1,200 (67% complete)\n3. Emergency Fund - $5,000/$10,000 (50% complete)\n\nYou can add or update savings goals in the Finance section of the app."
                })
            elif any(term in query_lower for term in ["report", "analysis", "trend", "spending", "history"]):
                return jsonify({
                    "response": "Spending analysis (sample data):\n\nTop categories this month:\n1. Groceries - $450 (36% of budget)\n2. Utilities - $320 (80% of budget)\n3. Entertainment - $200 (67% of budget)\n\nCompared to last month:\n- Groceries: 5% increase\n- Utilities: 2% decrease\n- Entertainment: 15% increase\n\nNote: This is example data for demonstration purposes only."
                })
            else:
                return jsonify({
                    "response": "I can help you manage your family finances. You can:\n- View your current budget and spending\n- Add new expenses\n- Set or update your budget\n- Track savings goals\n- View spending reports and trends"
                })
        elif context == "chat":
            if any(term in query_lower for term in ["view", "show", "list", "messages", "recent"]):
                return jsonify({
                    "response": "Here are your recent messages (sample data):\n\nSarah (10:30 AM): Don't forget to pick up milk on your way home\nKids (11:45 AM): Can we have pizza for dinner?\nYou (12:15 PM): Sure, I'll order it around 5\n\nNote: These are example messages for demonstration purposes only."
                })
            elif any(term in query_lower for term in ["send", "message", "text"]):
                return jsonify({
                    "response": "Who would you like to send a message to? Available family members (sample):\n- Sarah\n- Kids\n- Mom\n- Dad\n\nNote: In test mode, messages won't actually be sent."
                })
            else:
                return jsonify({
                    "response": "Here are some chat options:\n- View recent messages\n- Send a new message to family members\n- Create a group chat\n- Share photos or files\n\nNote: I'm currently in test mode and not connected to your actual database."
                })
        elif context == "memory":
            if any(term in query_lower for term in ["view", "show", "list", "photos", "pictures", "albums"]):
                return jsonify({
                    "response": "Here are your recent memories (sample data):\n\n1. Family Vacation (15 photos, added Feb 20)\n2. Birthday Party (8 photos, added Feb 15)\n3. Weekend BBQ (5 photos, added Feb 10)\n\nNote: These are example memories for demonstration purposes only."
                })
            elif any(term in query_lower for term in ["add", "new", "upload", "create"]):
                return jsonify({
                    "response": "To add new memories, please provide:\n- Album name\n- Photos to upload\n- Description (optional)\n- Tags (optional)\n\nNote: In test mode, memories won't actually be added to the database."
                })
            else:
                return jsonify({
                    "response": "Here are some memory management options:\n- View your photo albums\n- Upload new photos\n- Create themed collections\n- Share memories with family members\n\nNote: I'm currently in test mode and not connected to your actual database."
                })
        elif context == "inventory":
            if any(term in query_lower for term in ["view", "show", "list", "items", "stock"]):
                return jsonify({
                    "response": "Here's your current inventory (sample data):\n\nGroceries:\n- Milk (1 gallon, expires in 5 days)\n- Bread (1 loaf, expires in 3 days)\n- Eggs (6 remaining)\n\nHousehold:\n- Paper towels (2 rolls)\n- Laundry detergent (running low)\n\nNote: This is example inventory data for demonstration purposes only."
                })
            elif any(term in query_lower for term in ["add", "new", "purchase", "bought"]):
                return jsonify({
                    "response": "To add items to your inventory, please provide:\n- Item name\n- Quantity\n- Category (e.g., Groceries, Household)\n- Expiration date (optional)\n\nNote: In test mode, items won't actually be added to the database."
                })
            elif any(term in query_lower for term in ["remove", "used", "consumed", "finished"]):
                return jsonify({
                    "response": "Which item would you like to remove from inventory? Please specify the item name and quantity.\n\nNote: In test mode, items won't actually be removed from the database."
                })
            else:
                return jsonify({
                    "response": "Here are some inventory management options:\n- View your current inventory\n- Add new items\n- Remove used items\n- Set up automatic shopping lists\n- Get low stock alerts\n\nNote: I'm currently in test mode and not connected to your actual database."
                })
        elif context == "health":
            if any(term in query_lower for term in ["view", "show", "list", "medications", "prescriptions"]):
                return jsonify({
                    "response": "Here are your medications (sample data):\n\n1. Vitamin D (1 pill daily, morning)\n2. Allergy medication (1 pill daily, evening)\n\nUpcoming appointments:\n- Dr. Smith, March 10, 2:00 PM\n\nNote: This is example health data for demonstration purposes only."
                })
            elif any(term in query_lower for term in ["add", "new", "medication", "prescription"]):
                return jsonify({
                    "response": "To add a new medication reminder, please provide:\n- Medication name\n- Dosage\n- Frequency\n- Time of day\n- Start date\n- End date (optional)\n\nNote: In test mode, medications won't actually be added to the database."
                })
            elif any(term in query_lower for term in ["appointment", "schedule", "doctor"]):
                return jsonify({
                    "response": "To add a new health appointment, please provide:\n- Doctor/Provider name\n- Date\n- Time\n- Purpose\n- Location\n\nNote: In test mode, appointments won't actually be added to the database."
                })
            else:
                return jsonify({
                    "response": "Here are some health management options:\n- View your medications\n- Add medication reminders\n- Schedule doctor appointments\n- Track health metrics\n- Set up emergency contacts\n\nNote: I'm currently in test mode and not connected to your actual database."
                })
        elif context == "emergency":
            return jsonify({
                "response": "Emergency features:\n\n- Set up emergency contacts\n- Share your location with family members\n- Access quick dial for emergency services\n- Store important documents securely\n\nNote: These features are for demonstration purposes only in test mode."
            })
        elif context == "family":
            if any(term in query_lower for term in ["view", "show", "list", "members"]):
                return jsonify({
                    "response": "Family members (sample data):\n\n- JP (Admin)\n- Sarah (Member)\n- Kids (Kid)\n\nConnected families:\n- Grandparents\n- Cousins\n\nNote: This is example family data for demonstration purposes only."
                })
            elif any(term in query_lower for term in ["add", "invite", "new"]):
                return jsonify({
                    "response": "To invite a new family member, please provide:\n- Email address\n- Name\n- Role (Admin, Member, Kid)\n\nAlternatively, you can share your family code: ABC123\n\nNote: In test mode, invitations won't actually be sent."
                })
            else:
                return jsonify({
                    "response": "Here are some family management options:\n- View family members\n- Invite new members\n- Connect with extended family\n- Manage member roles and permissions\n\nNote: I'm currently in test mode and not connected to your actual database."
                })
        else:
            # General help
            return jsonify({
                "response": "I'm SphereBot, your family assistant! I can help with:\n\n- Tasks and chores\n- Calendar and events\n- Family finances\n- Family chat\n- Photo memories\n- Household inventory\n- Health tracking\n- Emergency features\n- Family member management\n\nWhat would you like help with today?\n\nNote: I'm currently in test mode and not connected to your actual database."
            })
            
    except Exception as e:
        print(f"Exception in spherebot_query: {str(e)}")
        return jsonify({"error": str(e)}), 500

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

@app.route('/print_calendar')
@login_required
def print_calendar():
    """Generate a printable version of the calendar."""
    from database import db
    import datetime
    
    # Get filter parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category = request.args.get('category')
    member_id = request.args.get('member_id')
    view_type = request.args.get('view', 'month')
    include_shared = request.args.get('include_shared', 'true') == 'true'
    
    # Get all events for the user's family
    query = db.table('events').select('*').eq('family_id', current_user.family_id)
    
    # Apply date filters if provided
    if start_date:
        query = query.gte('date', start_date)
    if end_date:
        query = query.lte('date', end_date)
        
    # Apply category filter if provided
    if category and category != 'all':
        query = query.eq('category', category)
        
    # Apply member filter if provided
    if member_id and member_id != 'all':
        query = query.eq('created_by', member_id)
        
    events_response = query.execute()
    events = events_response.data
    
    # Also get shared events that this family can see
    shared_events = []
    if include_shared:
        shared_query = db.table('events').select('*').neq('family_id', current_user.family_id)
        
        # Apply date filters if provided
        if start_date:
            shared_query = shared_query.gte('date', start_date)
        if end_date:
            shared_query = shared_query.lte('date', end_date)
            
        # Apply category filter if provided
        if category and category != 'all':
            shared_query = shared_query.eq('category', category)
            
        shared_response = shared_query.execute()
        
        # Filter shared events to only include those shared with this family
        for event_data in shared_response.data:
            shared_with = event_data.get('shared_with', '')
            if shared_with and current_user.family_id in shared_with.split(','):
                events.append(event_data)
    
    # Format events for the template
    formatted_events = []
    
    for event in events:
        formatted_event = format_event_for_calendar(event, is_family_event=True)
        formatted_events.append(formatted_event)
    
    for event in shared_events:
        formatted_event = format_event_for_calendar(event, is_family_event=False)
        formatted_events.append(formatted_event)
    
    # Get family members for display
    family_members_response = db.table('users').select('id, username').eq('family_id', current_user.family_id).execute()
    family_members = family_members_response.data
    
    # Create a member lookup dictionary
    member_lookup = {member['id']: member['username'] for member in family_members}
    
    # Sort events by date and time
    formatted_events.sort(key=lambda x: (x['start'], x.get('end', '')))
    
    # Group events by date for month view
    events_by_date = {}
    for event in formatted_events:
        date_str = event['start'].split('T')[0] if 'T' in event['start'] else event['start']
        if date_str not in events_by_date:
            events_by_date[date_str] = []
        events_by_date[date_str].append(event)
    
    # Set title based on date range
    if start_date and end_date:
        title = f"Calendar: {start_date} to {end_date}"
    elif start_date:
        title = f"Calendar: From {start_date}"
    elif end_date:
        title = f"Calendar: Until {end_date}"
    else:
        title = "Family Calendar"
    
    # Add category filter to title if applicable
    if category and category != 'all':
        title += f" - {category} Events"
    
    # Add member filter to title if applicable
    if member_id and member_id != 'all' and member_id in member_lookup:
        title += f" - {member_lookup[member_id]}'s Events"
    
    return render_template('print_calendar.html',
                          events=formatted_events,
                          events_by_date=events_by_date,
                          view_type=view_type,
                          title=title,
                          member_lookup=member_lookup,
                          page_title="Print Calendar")

# Calendar template routes
@app.route('/calendar/templates')
@login_required
def calendar_templates():
    """Display the calendar templates management page."""
    family_id = current_user.family_id
    
    # Get all templates for this family
    templates = db.table('calendar_templates').select('*').eq('family_id', family_id).execute()
    
    return render_template('calendar_templates.html', templates=templates.data)

@app.route('/api/calendar_templates')
@login_required
def get_calendar_templates():
    """API endpoint to get calendar templates for the current family."""
    family_id = current_user.family_id
    
    # Get all templates for this family
    templates = db.table('calendar_templates').select('*').eq('family_id', family_id).execute()
    
    return jsonify({'templates': templates.data})

@app.route('/save_calendar_template', methods=['POST'])
@login_required
def save_calendar_template():
    """Save a new or update an existing calendar template."""
    family_id = current_user.family_id
    
    template_id = request.form.get('template_id')
    template_name = request.form.get('template_name')
    event_title = request.form.get('event_title')
    event_category = request.form.get('event_category')
    event_location = request.form.get('event_location')
    event_description = request.form.get('event_description')
    all_day = True if request.form.get('all_day') else False
    event_time = request.form.get('event_time')
    event_end_time = request.form.get('event_end_time')
    recurrence_pattern = request.form.get('recurrence_pattern')
    
    # Validate required fields
    if not template_name or not event_title:
        flash('Template name and event title are required.', 'danger')
        return redirect(url_for('calendar_templates'))
    
    template_data = {
        'template_name': template_name,
        'event_title': event_title,
        'event_category': event_category,
        'event_location': event_location,
        'event_description': event_description,
        'all_day': all_day,
        'event_time': event_time,
        'event_end_time': event_end_time,
        'recurrence_pattern': recurrence_pattern,
        'family_id': family_id,
        'created_by': current_user.id,
        'updated_at': datetime.now().isoformat()
    }
    
    try:
        if template_id:
            # Update existing template
            result = db.table('calendar_templates').update(template_data).eq('id', template_id).eq('family_id', family_id).execute()
            flash('Template updated successfully', 'success')
        else:
            # Create new template
            template_data['created_at'] = datetime.now().isoformat()
            result = db.table('calendar_templates').insert(template_data).execute()
            flash('Template created successfully', 'success')
            
        return redirect(url_for('calendar_templates'))
    except Exception as e:
        app.logger.error(f"Error saving template: {str(e)}")
        flash(f'Error saving template: {str(e)}', 'danger')
        return redirect(url_for('calendar_templates'))

@app.route('/delete_calendar_template', methods=['POST'])
@login_required
def delete_calendar_template():
    """Delete a calendar template."""
    family_id = current_user.family_id
    template_id = request.form.get('template_id', '')
    
    if not template_id:
        flash('Template ID is required.', 'danger')
        return redirect(url_for('calendar_templates'))
    
    try:
        # Delete the template
        result = db.table('calendar_templates').delete().eq('id', template_id).eq('family_id', family_id).execute()
        flash('Template deleted successfully', 'success')
    except Exception as e:
        app.logger.error(f"Error deleting template: {str(e)}")
        flash(f'Error deleting template: {str(e)}', 'danger')
    
    return redirect(url_for('calendar_templates'))

@app.route('/use_calendar_template/<template_id>')
@login_required
def use_calendar_template(template_id):
    """Use a template to create a new event."""
    family_id = current_user.family_id
    
    # Get the template
    template_result = db.table('calendar_templates').select('*').eq('id', template_id).eq('family_id', family_id).execute()
    
    if not template_result.data:
        flash('Template not found.', 'danger')
        return redirect(url_for('calendar'))
    
    template = template_result.data[0]
    
    # Redirect to add event page with template data
    return redirect(url_for('add_event', 
                           template_id=template_id,
                           title=template['event_title'],
                           category=template['event_category'],
                           location=template['event_location'],
                           description=template['event_description'],
                           all_day='true' if template['all_day'] else '',
                           start_time=template['event_time'],
                           end_time=template['event_end_time'],
                           recurrence=template['recurrence_pattern']))

@app.route('/family/connections')
@login_required
def family_connections():
    return render_template('family_connections.html')

# Family Connection Routes
@app.route('/api/family_connections/connected')
@login_required
def get_connected_families():
    """Get list of families connected with the current family."""
    try:
        # Get current family's connections
        response = supabase.table('family_connections').select(
            'id, connected_family:connected_family_id(id, name), connected_date, shared_features'
        ).eq('family_id', current_user.family_id).execute()

        families = []
        for conn in response.data:
            families.append({
                'id': conn['connected_family']['id'],
                'name': conn['connected_family']['name'],
                'connected_date': conn['connected_date'],
                'shared_features': conn['shared_features'] or []
            })

        return jsonify({'success': True, 'families': families})
    except Exception as e:
        app.logger.error(f"Error getting connected families: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to load connected families'}), 500

@app.route('/api/family_connections/requests')
@login_required
def get_connection_requests():
    """Get incoming and outgoing connection requests."""
    try:
        # Get incoming requests
        incoming = supabase.table('family_connection_requests').select(
            'id, family:requesting_family_id(id, name), request_date'
        ).eq('requested_family_id', current_user.family_id).eq('status', 'pending').execute()

        # Get outgoing requests
        outgoing = supabase.table('family_connection_requests').select(
            'id, family:requested_family_id(id, name), request_date'
        ).eq('requesting_family_id', current_user.family_id).eq('status', 'pending').execute()

        return jsonify({
            'success': True,
            'incoming': [{
                'id': req['id'],
                'family_name': req['family']['name'],
                'request_date': req['request_date']
            } for req in incoming.data],
            'outgoing': [{
                'id': req['id'],
                'family_name': req['family']['name'],
                'request_date': req['request_date']
            } for req in outgoing.data]
        })
    except Exception as e:
        app.logger.error(f"Error getting connection requests: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to load connection requests'}), 500

@app.route('/api/family_connections/request', methods=['POST'])
@login_required
def send_connection_request():
    """Send a connection request to another family."""
    try:
        data = request.get_json()
        family_code = data.get('family_code')
        
        if not family_code:
            return jsonify({'success': False, 'message': 'Family code is required'})
        
        # Find the family by code
        family = supabase.table('families').select('id').eq('code', family_code).single().execute()
        if not family.data:
            return jsonify({'success': False, 'message': 'Family not found'})
        
        requested_family_id = family.data['id']
        
        # Check if already connected
        existing_connection = supabase.table('family_connections').select('id').or_(
            f'and(family_id.eq.{current_user.family_id},connected_family_id.eq.{requested_family_id})',
            f'and(family_id.eq.{requested_family_id},connected_family_id.eq.{current_user.family_id})'
        ).execute()
        
        if existing_connection.data:
            return jsonify({'success': False, 'message': 'Already connected with this family'})
        
        # Check for existing pending request
        existing_request = supabase.table('family_connection_requests').select('id').or_(
            f'and(requesting_family_id.eq.{current_user.family_id},requested_family_id.eq.{requested_family_id})',
            f'and(requesting_family_id.eq.{requested_family_id},requested_family_id.eq.{current_user.family_id})'
        ).eq('status', 'pending').execute()

        if existing_request.data:
            return jsonify({'success': False, 'message': 'A connection request already exists'})
        
        # Create the request
        supabase.table('family_connection_requests').insert({
            'requesting_family_id': current_user.family_id,
            'requested_family_id': requested_family_id,
            'status': 'pending',
            'request_date': datetime.utcnow().isoformat()
        }).execute()

        return jsonify({'success': True, 'message': 'Connection request sent successfully'})
    except Exception as e:
        app.logger.error(f"Error sending connection request: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to send connection request'}), 500

@app.route('/api/family_connections/accept/<request_id>', methods=['POST'])
@login_required
def accept_connection_request(request_id):
    """Accept a connection request."""
    try:
        # Get the request
        request_data = supabase.table('family_connection_requests').select(
            'requesting_family_id, requested_family_id, status'
        ).eq('id', request_id).single().execute()

        if not request_data.data:
            return jsonify({'success': False, 'message': 'Request not found'})
        
        if request_data.data['status'] != 'pending':
            return jsonify({'success': False, 'message': 'Request is no longer pending'})
        
        if request_data.data['requested_family_id'] != current_user.family_id:
            return jsonify({'success': False, 'message': 'Not authorized to accept this request'})
        
        # Create connection
        supabase.table('family_connections').insert([
            {
                'family_id': request_data.data['requesting_family_id'],
                'connected_family_id': request_data.data['requested_family_id'],
                'connected_date': datetime.utcnow().isoformat(),
                'shared_features': []
            }
        ]).execute()

        # Update request status
        supabase.table('family_connection_requests').update({
            'status': 'accepted',
            'response_date': datetime.utcnow().isoformat()
        }).eq('id', request_id).execute()

        return jsonify({'success': True, 'message': 'Connection request accepted'})
    except Exception as e:
        app.logger.error(f"Error accepting connection request: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to accept connection request'}), 500

@app.route('/api/family_connections/reject/<request_id>', methods=['POST'])
@login_required
def reject_connection_request(request_id):
    """Reject a connection request."""
    try:
        # Get the request
        request_data = supabase.table('family_connection_requests').select(
            'requested_family_id, status'
        ).eq('id', request_id).single().execute()

        if not request_data.data:
            return jsonify({'success': False, 'message': 'Request not found'})
        
        if request_data.data['status'] != 'pending':
            return jsonify({'success': False, 'message': 'Request is no longer pending'})
        
        if request_data.data['requested_family_id'] != current_user.family_id:
            return jsonify({'success': False, 'message': 'Not authorized to reject this request'})
        
        # Update request status
        supabase.table('family_connection_requests').update({
            'status': 'rejected',
            'response_date': datetime.utcnow().isoformat()
        }).eq('id', request_id).execute()

        return jsonify({'success': True, 'message': 'Connection request rejected'})
    except Exception as e:
        app.logger.error(f"Error rejecting connection request: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to reject connection request'}), 500

@app.route('/api/family_connections/cancel/<request_id>', methods=['POST'])
@login_required
def cancel_connection_request(request_id):
    """Cancel an outgoing connection request."""
    try:
        # Get the request
        request_data = supabase.table('family_connection_requests').select(
            'requesting_family_id, status'
        ).eq('id', request_id).single().execute()

        if not request_data.data:
            return jsonify({'success': False, 'message': 'Request not found'})
        
        if request_data.data['status'] != 'pending':
            return jsonify({'success': False, 'message': 'Request is no longer pending'})
        
        if request_data.data['requesting_family_id'] != current_user.family_id:
            return jsonify({'success': False, 'message': 'Not authorized to cancel this request'})
        
        # Update request status
        supabase.table('family_connection_requests').update({
            'status': 'cancelled',
            'response_date': datetime.utcnow().isoformat()
        }).eq('id', request_id).execute()

        return jsonify({'success': True, 'message': 'Connection request cancelled'})
    except Exception as e:
        app.logger.error(f"Error cancelling connection request: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to cancel connection request'}), 500

@app.route('/api/family_connections/sharing/<family_id>')
@login_required
def get_sharing_settings(family_id):
    """Get sharing settings for a connected family."""
    try:
        # Get the connection
        connection = supabase.table('family_connections').select(
            'shared_features'
        ).or_(
            f'family_id.eq.{current_user.family_id},connected_family_id.eq.{family_id}',
            f'family_id.eq.{family_id},connected_family_id.eq.{current_user.family_id}'
        ).single().execute()

        if not connection.data:
            return jsonify({'success': False, 'message': 'Connection not found'})
        
        shared_features = connection.data.get('shared_features', [])
        settings = {
            'calendar': 'calendar' in shared_features,
            'tasks': 'tasks' in shared_features,
            'photos': 'photos' in shared_features,
            'shopping': 'shopping' in shared_features,
            'emergency': 'emergency' in shared_features,
            'documents': 'documents' in shared_features
        }

        return jsonify({'success': True, 'settings': settings})
    except Exception as e:
        app.logger.error(f"Error getting sharing settings: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to load sharing settings'}), 500

@app.route('/api/family_connections/sharing/<family_id>', methods=['POST'])
@login_required
def update_sharing_settings(family_id):
    """Update sharing settings for a connected family."""
    try:
        data = request.get_json()
        
        # Get the connection
        connection = supabase.table('family_connections').select('id').or_(
            f'family_id.eq.{current_user.family_id},connected_family_id.eq.{family_id}',
            f'family_id.eq.{family_id},connected_family_id.eq.{current_user.family_id}'
        ).single().execute()

        if not connection.data:
            return jsonify({'success': False, 'message': 'Connection not found'})
        
        # Update shared features
        shared_features = []
        for feature, enabled in data.items():
            if enabled:
                shared_features.append(feature)

        supabase.table('family_connections').update({
            'shared_features': shared_features
        }).eq('id', connection.data['id']).execute()

        return jsonify({'success': True, 'message': 'Sharing settings updated successfully'})
    except Exception as e:
        app.logger.error(f"Error updating sharing settings: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to update sharing settings'}), 500

@app.route('/api/family_connections/disconnect/<family_id>', methods=['POST'])
@login_required
def disconnect_family(family_id):
    """Disconnect from a family."""
    try:
        # Delete the connection
        supabase.table('family_connections').delete().or_(
            f'family_id.eq.{current_user.family_id},connected_family_id.eq.{family_id}',
            f'family_id.eq.{family_id},connected_family_id.eq.{current_user.family_id}'
        ).execute()

        # Delete all shared items
        tables = ['shared_events', 'shared_tasks', 'shared_photos', 'shared_shopping_lists', 'shared_emergency_contacts']
        for table in tables:
            supabase.table(table).delete().or_(
                f'family_id.eq.{current_user.family_id},shared_with.cs.{{{family_id}}}',
                f'family_id.eq.{family_id},shared_with.cs.{{{current_user.family_id}}}'
            ).execute()

        return jsonify({'success': True, 'message': 'Family disconnected successfully'})
    except Exception as e:
        app.logger.error(f"Error disconnecting family: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to disconnect family'}), 500

@app.route('/api/family_connections/shared/events')
@login_required
def get_shared_events():
    """Get events shared with or by connected families."""
    try:
        # Get connected family IDs
        connections = supabase.table('family_connections').select(
            'id, connected_family_id, shared_features'
        ).or_(
            f'family_id.eq.{current_user.family_id}',
            f'connected_family_id.eq.{current_user.family_id}'
        ).execute()

        shared_events = []
        for conn in connections.data:
            if 'calendar' not in conn.get('shared_features', []):
                continue

            other_family_id = conn['connected_family_id'] if conn['family_id'] == current_user.family_id else conn['family_id']

            # Get events shared by the other family
            events = supabase.table('events').select(
                'id, title, start_date, end_date, description, family_id'
            ).eq('family_id', other_family_id).contains('shared_with', [str(current_user.family_id)]).execute()

            shared_events.extend(events.data or [])

        return jsonify({'success': True, 'events': shared_events})
    except Exception as e:
        app.logger.error(f"Error getting shared events: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to load shared events'}), 500

@app.route('/api/family_connections/shared/tasks')
@login_required
def get_shared_tasks():
    """Get tasks shared with or by connected families."""
    try:
        # Get connected family IDs
        connections = supabase.table('family_connections').select(
            'id, connected_family_id, shared_features'
        ).or_(
            f'family_id.eq.{current_user.family_id}',
            f'connected_family_id.eq.{current_user.family_id}'
        ).execute()

        shared_tasks = []
        for conn in connections.data:
            if 'tasks' not in conn.get('shared_features', []):
                continue

            other_family_id = conn['connected_family_id'] if conn['family_id'] == current_user.family_id else conn['family_id']

            # Get tasks shared by the other family
            tasks = supabase.table('tasks').select(
                'id, title, description, due_date, status, family_id'
            ).eq('family_id', other_family_id).contains('shared_with', [str(current_user.family_id)]).execute()

            shared_tasks.extend(tasks.data or [])

        return jsonify({'success': True, 'tasks': shared_tasks})
    except Exception as e:
        app.logger.error(f"Error getting shared tasks: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to load shared tasks'}), 500

@app.route('/api/family_connections/shared/photos')
@login_required
def get_shared_photos():
    """Get photos shared with or by connected families."""
    try:
        # Get connected family IDs
        connections = supabase.table('family_connections').select(
            'id, connected_family_id, shared_features'
        ).or_(
            f'family_id.eq.{current_user.family_id}',
            f'connected_family_id.eq.{current_user.family_id}'
        ).execute()

        shared_photos = []
        for conn in connections.data:
            if 'photos' not in conn.get('shared_features', []):
                continue

            other_family_id = conn['connected_family_id'] if conn['family_id'] == current_user.family_id else conn['family_id']

            # Get photos shared by the other family
            photos = supabase.table('photos').select(
                'id, title, description, url, taken_date, family_id'
            ).eq('family_id', other_family_id).contains('shared_with', [str(current_user.family_id)]).execute()

            shared_photos.extend(photos.data or [])

        return jsonify({'success': True, 'photos': shared_photos})
    except Exception as e:
        app.logger.error(f"Error getting shared photos: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to load shared photos'}), 500

@app.route('/api/family_connections/shared/shopping')
@login_required
def get_shared_shopping_lists():
    """Get shopping lists shared with or by connected families."""
    try:
        # Get connected family IDs
        connections = supabase.table('family_connections').select(
            'id, connected_family_id, shared_features'
        ).or_(
            f'family_id.eq.{current_user.family_id}',
            f'connected_family_id.eq.{current_user.family_id}'
        ).execute()

        shared_lists = []
        for conn in connections.data:
            if 'shopping' not in conn.get('shared_features', []):
                continue

            other_family_id = conn['connected_family_id'] if conn['family_id'] == current_user.family_id else conn['family_id']

            # Get shopping lists shared by the other family
            lists = supabase.table('shopping_lists').select(
                'id, name, items, created_date, family_id'
            ).eq('family_id', other_family_id).contains('shared_with', [str(current_user.family_id)]).execute()

            shared_lists.extend(lists.data or [])

        return jsonify({'success': True, 'lists': shared_lists})
    except Exception as e:
        app.logger.error(f"Error getting shared shopping lists: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to load shared shopping lists'}), 500

@app.route('/api/family_connections/shared/emergency')
@login_required
def get_shared_emergency_contacts():
    """Get emergency contacts shared with or by connected families."""
    try:
        # Get connected family IDs
        connections = supabase.table('family_connections').select(
            'id, connected_family_id, shared_features'
        ).or_(
            f'family_id.eq.{current_user.family_id}',
            f'connected_family_id.eq.{current_user.family_id}'
        ).execute()

        shared_contacts = []
        for conn in connections.data:
            if 'emergency' not in conn.get('shared_features', []):
                continue

            other_family_id = conn['connected_family_id'] if conn['family_id'] == current_user.family_id else conn['family_id']

            # Get emergency contacts shared by the other family
            contacts = supabase.table('emergency_contacts').select(
                'id, name, relationship, phone, email, address, notes, family_id'
            ).eq('family_id', other_family_id).contains('shared_with', [str(current_user.family_id)]).execute()

            shared_contacts.extend(contacts.data or [])

        return jsonify({'success': True, 'contacts': shared_contacts})
    except Exception as e:
        app.logger.error(f"Error getting shared emergency contacts: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to load shared emergency contacts'}), 500

@app.route('/api/family_connections/share/<item_type>/<item_id>', methods=['POST'])
@login_required
def share_item(item_type, item_id):
    """Share an item with connected families."""
    try:
        data = request.get_json()
        family_ids = data.get('family_ids', [])
        
        if not family_ids:
            return jsonify({'success': False, 'message': 'No families selected to share with'}), 400

        # Verify all families are connected and sharing is enabled
        for family_id in family_ids:
            connection = supabase.table('family_connections').select('shared_features').or_(
                f'family_id.eq.{current_user.family_id},connected_family_id.eq.{family_id}',
                f'family_id.eq.{family_id},connected_family_id.eq.{current_user.family_id}'
            ).single().execute()

            if not connection.data:
                return jsonify({'success': False, 'message': f'Family {family_id} is not connected'}), 400

            feature_map = {
                'event': 'calendar',
                'task': 'tasks',
                'photo': 'photos',
                'shopping_list': 'shopping',
                'emergency_contact': 'emergency'
            }
            required_feature = feature_map.get(item_type)
            
            if required_feature and required_feature not in connection.data.get('shared_features', []):
                return jsonify({'success': False, 'message': f'Sharing {item_type}s is not enabled for family {family_id}'}), 400

        # Update the item's shared_with field
        table_map = {
            'event': 'events',
            'task': 'tasks',
            'photo': 'photos',
            'shopping_list': 'shopping_lists',
            'emergency_contact': 'emergency_contacts'
        }
        
        table_name = table_map.get(item_type)
        if not table_name:
            return jsonify({'success': False, 'message': 'Invalid item type'}), 400

        # Get current item to verify ownership
        item = supabase.table(table_name).select('family_id, shared_with').eq('id', item_id).single().execute()
        
        if not item.data or item.data['family_id'] != current_user.family_id:
            return jsonify({'success': False, 'message': 'Item not found or not authorized'}), 404

        # Update shared_with field
        current_shared = item.data.get('shared_with', [])
        new_shared = list(set(current_shared + family_ids))  # Remove duplicates
        
        supabase.table(table_name).update({
            'shared_with': new_shared
        }).eq('id', item_id).execute()

        return jsonify({'success': True, 'message': f'{item_type.title()} shared successfully'})
    except Exception as e:
        app.logger.error(f"Error sharing {item_type}: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to share {item_type}'}), 500

@app.route('/api/family_connections/unshare/<item_type>/<item_id>', methods=['POST'])
@login_required
def unshare_item(item_type, item_id):
    """Stop sharing an item with specific families."""
    try:
        data = request.get_json()
        family_ids = data.get('family_ids', [])
        
        if not family_ids:
            return jsonify({'success': False, 'message': 'No families selected to unshare with'}), 400

        table_map = {
            'event': 'events',
            'task': 'tasks',
            'photo': 'photos',
            'shopping_list': 'shopping_lists',
            'emergency_contact': 'emergency_contacts'
        }
        
        table_name = table_map.get(item_type)
        if not table_name:
            return jsonify({'success': False, 'message': 'Invalid item type'}), 400

        # Get current item to verify ownership
        item = supabase.table(table_name).select('family_id, shared_with').eq('id', item_id).single().execute()
        
        if not item.data or item.data['family_id'] != current_user.family_id:
            return jsonify({'success': False, 'message': 'Item not found or not authorized'}), 404

        # Update shared_with field
        current_shared = item.data.get('shared_with', [])
        new_shared = [fid for fid in current_shared if fid not in family_ids]
        
        supabase.table(table_name).update({
            'shared_with': new_shared
        }).eq('id', item_id).execute()

        return jsonify({'success': True, 'message': f'{item_type.title()} unshared successfully'})
    except Exception as e:
        app.logger.error(f"Error unsharing {item_type}: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to unshare {item_type}'}), 500

@app.route('/spherebot/test_query', methods=['POST'])
@csrf.exempt  # Exempt this route from CSRF protection for testing
def spherebot_test_query():
    """Test route for SphereBot queries without login requirement."""
    try:
        # Validate request
        if not request.is_json:
            print("Request is not JSON")
            return jsonify({"error": "Request must be JSON"}), 400
            
        data = request.get_json()
        print(f"Received data: {data}")
        
        if not data or 'query' not in data:
            print("Missing query parameter")
            return jsonify({"error": "Missing query parameter"}), 400
            
        query = data['query']
        if not query or not isinstance(query, str):
            print(f"Invalid query parameter: {query}")
            return jsonify({"error": "Invalid query parameter"}), 400
        
        # Determine the context based on the query content
        context_keywords = {
            "calendar": ["calendar", "schedule", "event", "appointment", "meeting", "remind", "when"],
            "tasks": ["task", "chore", "assignment", "todo", "to-do", "to do", "work", "job"],
            "finance": ["money", "budget", "finance", "spending", "expense", "cost", "save", "bill", "payment"],
            "chat": ["message", "chat", "conversation", "talk", "discuss", "communicate"],
            "memory": ["photo", "picture", "memory", "album", "remember", "moment", "capture"],
            "inventory": ["inventory", "item", "stock", "supply", "grocery", "shopping", "list"],
            "health": ["health", "medication", "medicine", "doctor", "appointment", "prescription"],
            "emergency": ["emergency", "contact", "urgent", "crisis", "help", "sos"],
            "family": ["family", "member", "relative", "relationship", "invite", "join"]
        }
        
        context = "general"
        for ctx, keywords in context_keywords.items():
            if any(keyword in query.lower() for keyword in keywords):
                context = ctx
                break
                
        print(f"Determined context: {context}")
        
        # Special case for asking why tasks are showing
        query_lower = query.lower()
        if "why" in query_lower and ("task" in query_lower or "telling me" in query_lower):
            return jsonify({
                "response": "I'm currently in test mode and not connected to your actual database. The tasks I'm showing are just examples to demonstrate how I would display your real tasks when properly connected to your account."
            })
        
        # Handle different contexts with specific responses
        if context == "tasks":
            # Check for specific task-related queries
            if any(term in query_lower for term in ["view", "show", "list", "what are", "pending"]):
                return jsonify({
                    "response": "These are sample tasks for demonstration purposes only:\n\n1. Walk the dog (Due today)\n2. Buy groceries (Due tomorrow)\n3. Call mom (Due March 5)\n\nNote: These are not your actual tasks. I'm currently in test mode without access to your real data."
                })
            elif any(term in query_lower for term in ["create", "add", "new"]):
                return jsonify({
                    "response": "To create a new task, please provide the following details:\n- Task title\n- Due date\n- Assigned to (optional)\n- Priority (optional)\n\nNote: In test mode, tasks won't actually be created in the database."
                })
            elif any(term in query_lower for term in ["assign", "distribute", "give"]):
                return jsonify({
                    "response": "These are sample family members for demonstration purposes:\n- JP (Admin)\n- Sarah (Member)\n- Kids (Kid)\n\nNote: These may not be your actual family members. I'm currently in test mode."
                })
            elif any(term in query_lower for term in ["complete", "mark", "done", "finish"]):
                return jsonify({
                    "response": "Which task would you like to mark as complete? Please specify the task name or number from your pending tasks list.\n\nNote: In test mode, tasks won't actually be marked as complete in the database."
                })
            else:
                # General task management options
                return jsonify({
                    "response": "Here are some task management options:\n- View your pending tasks\n- Create a new task\n- Assign tasks to family members to distribute responsibilities\n- Mark tasks as completed\n\nNote: I'm currently in test mode and not connected to your actual database."
                })
        elif context == "calendar":
            if any(term in query_lower for term in ["view", "show", "list", "what", "upcoming", "today"]):
                return jsonify({
                    "response": "Here are your upcoming events (sample data):\n\n1. Family Dinner (Today, 6:00 PM)\n2. Doctor's Appointment (Tomorrow, 10:00 AM)\n3. Soccer Practice (March 3, 4:30 PM)\n4. Movie Night (March 5, 7:00 PM)\n\nNote: These are example events for demonstration purposes only."
                })
            elif any(term in query_lower for term in ["create", "add", "new", "schedule"]):
                return jsonify({
                    "response": "To create a new event, please provide the following details:\n- Event title\n- Date\n- Time\n- Location (optional)\n- Description (optional)\n- Attendees (optional)\n\nNote: In test mode, events won't actually be created in the database."
                })
            elif any(term in query_lower for term in ["edit", "update", "change", "modify", "reschedule"]):
                return jsonify({
                    "response": "Which event would you like to edit? Please specify the event name or number from your upcoming events list.\n\nNote: In test mode, events won't actually be modified in the database."
                })
            else:
                return jsonify({
                    "response": "Here are some calendar management options:\n- View your upcoming events\n- Create a new event\n- Edit existing events\n- Set reminders for important dates\n\nNote: I'm currently in test mode and not connected to your actual database."
                })
        elif context == "finance":
            if any(term in query_lower for term in ["view", "show", "list", "what", "summary", "overview"]):
                return jsonify({
                    "response": "Here's your financial summary (sample data):\n\nBudget: $2,500.00\nSpent this month: $1,200.00\nRemaining: $1,300.00\n\nRecent expenses:\n1. Groceries - $120.00 (Yesterday)\n2. Utilities - $180.00 (Feb 28)\n3. Dining out - $65.00 (Feb 27)\n\nNote: This is example financial data for demonstration purposes only."
                })
            elif any(term in query_lower for term in ["add", "new", "expense", "spent", "purchase"]):
                return jsonify({
                    "response": "To add a new expense, please provide the following details:\n- Category (e.g., Groceries, Utilities, Entertainment)\n- Amount\n- Date\n- Description (optional)\n\nNote: In test mode, expenses won't actually be added to the database."
                })
            elif any(term in query_lower for term in ["budget", "set", "limit", "goal"]):
                return jsonify({
                    "response": "To set a budget, please specify:\n- Category (e.g., Groceries, Utilities, Entertainment)\n- Monthly limit\n\nCurrent budget categories (sample):\n- Groceries: $500/month\n- Utilities: $300/month\n- Entertainment: $200/month\n\nNote: In test mode, budgets won't actually be set in the database."
                })
            elif any(term in query_lower for term in ["saving", "goal", "target", "plan"]):
                return jsonify({
                    "response": "Your current savings goals (sample data):\n\n1. Vacation - $1,500/$3,000 (50% complete)\n2. New Appliances - $800/$1,200 (67% complete)\n3. Emergency Fund - $5,000/$10,000 (50% complete)\n\nYou can add or update savings goals in the Finance section of the app."
                })
            elif any(term in query_lower for term in ["report", "analysis", "trend", "spending", "history"]):
                return jsonify({
                    "response": "Spending analysis (sample data):\n\nTop categories this month:\n1. Groceries - $450 (36% of budget)\n2. Utilities - $320 (80% of budget)\n3. Entertainment - $200 (67% of budget)\n\nCompared to last month:\n- Groceries: 5% increase\n- Utilities: 2% decrease\n- Entertainment: 15% increase\n\nNote: This is example data for demonstration purposes only."
                })
            else:
                return jsonify({
                    "response": "I can help you manage your family finances. You can:\n- View your current budget and spending\n- Add new expenses\n- Set or update your budget\n- Track savings goals\n- View spending reports and trends"
                })
        elif context == "chat":
            if any(term in query_lower for term in ["view", "show", "list", "messages", "recent"]):
                return jsonify({
                    "response": "Here are your recent messages (sample data):\n\nSarah (10:30 AM): Don't forget to pick up milk on your way home\nKids (11:45 AM): Can we have pizza for dinner?\nYou (12:15 PM): Sure, I'll order it around 5\n\nNote: These are example messages for demonstration purposes only."
                })
            elif any(term in query_lower for term in ["send", "message", "text"]):
                return jsonify({
                    "response": "Who would you like to send a message to? Available family members (sample):\n- Sarah\n- Kids\n- Mom\n- Dad\n\nNote: In test mode, messages won't actually be sent."
                })
            else:
                return jsonify({
                    "response": "Here are some chat options:\n- View recent messages\n- Send a new message to family members\n- Create a group chat\n- Share photos or files\n\nNote: I'm currently in test mode and not connected to your actual database."
                })
        elif context == "memory":
            if any(term in query_lower for term in ["view", "show", "list", "photos", "pictures", "albums"]):
                return jsonify({
                    "response": "Here are your recent memories (sample data):\n\n1. Family Vacation (15 photos, added Feb 20)\n2. Birthday Party (8 photos, added Feb 15)\n3. Weekend BBQ (5 photos, added Feb 10)\n\nNote: These are example memories for demonstration purposes only."
                })
            elif any(term in query_lower for term in ["add", "new", "upload", "create"]):
                return jsonify({
                    "response": "To add new memories, please provide:\n- Album name\n- Photos to upload\n- Description (optional)\n- Tags (optional)\n\nNote: In test mode, memories won't actually be added to the database."
                })
            else:
                return jsonify({
                    "response": "Here are some memory management options:\n- View your photo albums\n- Upload new photos\n- Create themed collections\n- Share memories with family members\n\nNote: I'm currently in test mode and not connected to your actual database."
                })
        elif context == "inventory":
            if any(term in query_lower for term in ["view", "show", "list", "items", "stock"]):
                return jsonify({
                    "response": "Here's your current inventory (sample data):\n\nGroceries:\n- Milk (1 gallon, expires in 5 days)\n- Bread (1 loaf, expires in 3 days)\n- Eggs (6 remaining)\n\nHousehold:\n- Paper towels (2 rolls)\n- Laundry detergent (running low)\n\nNote: This is example inventory data for demonstration purposes only."
                })
            elif any(term in query_lower for term in ["add", "new", "purchase", "bought"]):
                return jsonify({
                    "response": "To add items to your inventory, please provide:\n- Item name\n- Quantity\n- Category (e.g., Groceries, Household)\n- Expiration date (optional)\n\nNote: In test mode, items won't actually be added to the database."
                })
            elif any(term in query_lower for term in ["remove", "used", "consumed", "finished"]):
                return jsonify({
                    "response": "Which item would you like to remove from inventory? Please specify the item name and quantity.\n\nNote: In test mode, items won't actually be removed from the database."
                })
            else:
                return jsonify({
                    "response": "Here are some inventory management options:\n- View your current inventory\n- Add new items\n- Remove used items\n- Set up automatic shopping lists\n- Get low stock alerts\n\nNote: I'm currently in test mode and not connected to your actual database."
                })
        elif context == "health":
            if any(term in query_lower for term in ["view", "show", "list", "medications", "prescriptions"]):
                return jsonify({
                    "response": "Here are your medications (sample data):\n\n1. Vitamin D (1 pill daily, morning)\n2. Allergy medication (1 pill daily, evening)\n\nUpcoming appointments:\n- Dr. Smith, March 10, 2:00 PM\n\nNote: This is example health data for demonstration purposes only."
                })
            elif any(term in query_lower for term in ["add", "new", "medication", "prescription"]):
                return jsonify({
                    "response": "To add a new medication reminder, please provide:\n- Medication name\n- Dosage\n- Frequency\n- Time of day\n- Start date\n- End date (optional)\n\nNote: In test mode, medications won't actually be added to the database."
                })
            elif any(term in query_lower for term in ["appointment", "schedule", "doctor"]):
                return jsonify({
                    "response": "To add a new health appointment, please provide:\n- Doctor/Provider name\n- Date\n- Time\n- Purpose\n- Location\n\nNote: In test mode, appointments won't actually be added to the database."
                })
            else:
                return jsonify({
                    "response": "Here are some health management options:\n- View your medications\n- Add medication reminders\n- Schedule doctor appointments\n- Track health metrics\n- Set up emergency contacts\n\nNote: I'm currently in test mode and not connected to your actual database."
                })
        elif context == "emergency":
            return jsonify({
                "response": "Emergency features:\n\n- Set up emergency contacts\n- Share your location with family members\n- Access quick dial for emergency services\n- Store important documents securely\n\nNote: These features are for demonstration purposes only in test mode."
            })
        elif context == "family":
            if any(term in query_lower for term in ["view", "show", "list", "members"]):
                return jsonify({
                    "response": "Family members (sample data):\n\n- JP (Admin)\n- Sarah (Member)\n- Kids (Kid)\n\nConnected families:\n- Grandparents\n- Cousins\n\nNote: This is example family data for demonstration purposes only."
                })
            elif any(term in query_lower for term in ["add", "invite", "new"]):
                return jsonify({
                    "response": "To invite a new family member, please provide:\n- Email address\n- Name\n- Role (Admin, Member, Kid)\n\nAlternatively, you can share your family code: ABC123\n\nNote: In test mode, invitations won't actually be sent."
                })
            else:
                return jsonify({
                    "response": "Here are some family management options:\n- View family members\n- Invite new members\n- Connect with extended family\n- Manage member roles and permissions\n\nNote: I'm currently in test mode and not connected to your actual database."
                })
        else:
            # General help
            return jsonify({
                "response": "I'm SphereBot, your family assistant! I can help with:\n\n- Tasks and chores\n- Calendar and events\n- Family finances\n- Family chat\n- Photo memories\n- Household inventory\n- Health tracking\n- Emergency features\n- Family member management\n\nWhat would you like help with today?\n\nNote: I'm currently in test mode and not connected to your actual database."
            })
            
    except Exception as e:
        print(f"Exception in spherebot_test_query: {str(e)}")
        return jsonify({"error": str(e)}), 500

def get_default_suggestion(context):
    """Get a default suggestion based on the context."""
    suggestions = {
        "calendar": "I can help you manage your family calendar. You can:\n- View upcoming events\n- Add new events\n- Set reminders\n- Share events with family members",
        "tasks": "I can help you manage family tasks. You can:\n- View pending tasks\n- Create new tasks\n- Assign tasks to family members\n- Mark tasks as completed",
        "finance": "I can help you manage your family finances. You can:\n- Track expenses\n- Set budgets\n- Monitor spending\n- Set financial goals",
        "chat": "I can help with family communication. You can:\n- Send messages to family members\n- Create group chats\n- Share updates\n- Stay connected with your loved ones",
        "memory": "I can help you manage family memories. You can:\n- View photo albums\n- Upload new photos\n- Create collections\n- Share memories with family",
        "inventory": "I can help you manage household inventory. You can:\n- Track grocery items\n- Manage household supplies\n- Get low stock alerts\n- Create shopping lists",
        "health": "I can help with family health tracking. You can:\n- Set medication reminders\n- Track appointments\n- Monitor health metrics\n- Store medical information",
        "emergency": "I can help with family emergency features. You can:\n- Set up emergency contacts\n- Share location\n- Access emergency services\n- Store important documents",
        "family": "I can help with family management. You can:\n- Add family members\n- Connect with extended family\n- Manage roles and permissions\n- Share updates with loved ones",
        "general": "I'm SphereBot, your family assistant! I can help with tasks, calendar, finances, chat, memories, inventory, health tracking, and more. What would you like help with today?"
    }
    return suggestions.get(context, suggestions["general"])

@app.route('/emergency/plan/add', methods=['POST'])
@login_required
def add_emergency_plan():
    """Add a new emergency plan."""
    from database import db
    import uuid
    from datetime import datetime
    
    try:
        # Get form data
        title = request.form.get('title')
        plan_type = request.form.get('plan_type', 'General')  # Fire, Medical, Natural Disaster, etc.
        description = request.form.get('description', '')
        meeting_place = request.form.get('meeting_place', '')
        steps = request.form.get('steps', '')
        contacts = request.form.getlist('contacts', [])
        
        # Validation
        if not title:
            flash('Plan title is required.', 'danger')
            return redirect(url_for('emergency'))
            
        # Create plan with UUID
        plan_id = str(uuid.uuid4())
        plan_data = {
            'id': plan_id,
            'title': title,
            'plan_type': plan_type,
            'description': description,
            'meeting_place': meeting_place,
            'steps': steps,
            'family_id': current_user.family_id,
            'created_by': current_user.id,
            'created_at': datetime.now().isoformat()
        }
        
        # Insert plan into database
        db.table('emergency_plans').insert(plan_data).execute()
        
        # Link emergency contacts to this plan if provided
        if contacts:
            for contact_id in contacts:
                link_id = str(uuid.uuid4())
                link_data = {
                    'id': link_id,
                    'plan_id': plan_id,
                    'contact_id': contact_id,
                    'created_at': datetime.now().isoformat()
                }
                db.table('emergency_plan_contacts').insert(link_data).execute()
        
        flash('Emergency plan added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding emergency plan: {str(e)}', 'danger')
    
    return redirect(url_for('emergency'))

@app.route('/emergency/document/add', methods=['POST'])
@login_required
def add_emergency_document():
    """Add a new emergency document."""
    from database import db
    import uuid
    from datetime import datetime
    
    try:
        # Get form data
        title = request.form.get('title')
        document_type = request.form.get('document_type', 'General')  # Insurance, Medical, Legal, etc.
        description = request.form.get('description', '')
        file_url = request.form.get('file_url', '')  # In a real app, this would be file upload
        expiration_date = request.form.get('expiration_date', '')
        applies_to = request.form.getlist('applies_to', [])  # User IDs
        
        # Validation
        if not title:
            flash('Document title is required.', 'danger')
            return redirect(url_for('emergency'))
            
        # Create document with UUID
        document_id = str(uuid.uuid4())
        document_data = {
            'id': document_id,
            'title': title,
            'document_type': document_type,
            'description': description,
            'file_url': file_url,
            'family_id': current_user.family_id,
            'created_by': current_user.id,
            'created_at': datetime.now().isoformat()
        }
        
        if expiration_date:
            document_data['expiration_date'] = expiration_date
        
        # Insert document into database
        db.table('emergency_documents').insert(document_data).execute()
        
        # Link document to specific family members if provided
        if applies_to:
            for user_id in applies_to:
                link_id = str(uuid.uuid4())
                link_data = {
                    'id': link_id,
                    'document_id': document_id,
                    'user_id': user_id,
                    'created_at': datetime.now().isoformat()
                }
                db.table('emergency_document_users').insert(link_data).execute()
        
        flash('Emergency document added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding emergency document: {str(e)}', 'danger')
    
    return redirect(url_for('emergency'))
