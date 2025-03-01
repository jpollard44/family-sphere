from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin):
    """User model for authentication and role-based access."""
    
    def __init__(self, id=None, username=None, password_hash=None, role=None, family_id=None):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.family_id = family_id

    def set_password(self, password):
        """Set the password hash for the user."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)
    
    @classmethod
    def from_dict(cls, data):
        """Create a User instance from a dictionary."""
        return cls(
            id=data.get('id'),
            username=data.get('username'),
            password_hash=data.get('password_hash'),
            role=data.get('role'),
            family_id=data.get('family_id')
        )
    
    def to_dict(self):
        """Convert User instance to a dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'password_hash': self.password_hash,
            'role': self.role,
            'family_id': self.family_id
        }

class Family:
    """Family model for grouping users."""
    
    def __init__(self, id=None, name=None, code=None):
        self.id = id
        self.name = name
        self.code = code
    
    @classmethod
    def from_dict(cls, data):
        """Create a Family instance from a dictionary."""
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            code=data.get('code')
        )
    
    def to_dict(self):
        """Convert Family instance to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code
        }

class Event:
    """Event model for calendar management."""
    
    def __init__(self, id=None, title=None, date=None, time=None, location=None, description=None, 
                 family_id=None, created_by=None, shared_with=None):
        self.id = id
        self.title = title
        self.date = date
        self.time = time
        self.location = location
        self.description = description
        self.family_id = family_id
        self.created_by = created_by
        self.shared_with = shared_with
    
    @classmethod
    def from_dict(cls, data):
        """Create an Event instance from a dictionary."""
        return cls(
            id=data.get('id'),
            title=data.get('title'),
            date=data.get('date'),
            time=data.get('time'),
            location=data.get('location'),
            description=data.get('description'),
            family_id=data.get('family_id'),
            created_by=data.get('created_by'),
            shared_with=data.get('shared_with')
        )
    
    def to_dict(self):
        """Convert Event instance to a dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'date': self.date,
            'time': self.time,
            'location': self.location,
            'description': self.description,
            'family_id': self.family_id,
            'created_by': self.created_by,
            'shared_with': self.shared_with
        }

class Task:
    """Task model for chore management."""
    
    def __init__(self, id=None, title=None, description=None, due_date=None, assigned_to=None, 
                 points=0, status="Pending", family_id=None):
        self.id = id
        self.title = title
        self.description = description
        self.due_date = due_date
        self.assigned_to = assigned_to
        self.points = points
        self.status = status
        self.family_id = family_id
    
    @classmethod
    def from_dict(cls, data):
        """Create a Task instance from a dictionary."""
        return cls(
            id=data.get('id'),
            title=data.get('title'),
            description=data.get('description'),
            due_date=data.get('due_date'),
            assigned_to=data.get('assigned_to'),
            points=data.get('points', 0),
            status=data.get('status', "Pending"),
            family_id=data.get('family_id')
        )
    
    def to_dict(self):
        """Convert Task instance to a dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date,
            'assigned_to': self.assigned_to,
            'points': self.points,
            'status': self.status,
            'family_id': self.family_id
        }

class Finance:
    """Finance model for budget, goals, and allowances."""
    
    def __init__(self, id=None, type=None, title=None, description=None, amount=None, target_amount=None, 
                 due_date=None, assigned_to=None, family_id=None):
        self.id = id
        self.type = type
        self.title = title
        self.description = description
        self.amount = amount
        self.target_amount = target_amount
        self.due_date = due_date
        self.assigned_to = assigned_to
        self.family_id = family_id
    
    @classmethod
    def from_dict(cls, data):
        """Create a Finance instance from a dictionary."""
        return cls(
            id=data.get('id'),
            type=data.get('type'),
            title=data.get('title'),
            description=data.get('description'),
            amount=data.get('amount'),
            target_amount=data.get('target_amount'),
            due_date=data.get('due_date'),
            assigned_to=data.get('assigned_to'),
            family_id=data.get('family_id')
        )
    
    def to_dict(self):
        """Convert Finance instance to a dictionary."""
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'description': self.description,
            'amount': self.amount,
            'target_amount': self.target_amount,
            'due_date': self.due_date,
            'assigned_to': self.assigned_to,
            'family_id': self.family_id
        }

class Chat:
    """Chat model for family communication."""
    
    def __init__(self, id=None, message=None, sender_id=None, family_id=None, timestamp=None, 
                 thread_id=None, is_poll=False, poll_options=None):
        self.id = id
        self.message = message
        self.sender_id = sender_id
        self.family_id = family_id
        self.timestamp = timestamp
        self.thread_id = thread_id
        self.is_poll = is_poll
        self.poll_options = poll_options
    
    @classmethod
    def from_dict(cls, data):
        """Create a Chat instance from a dictionary."""
        return cls(
            id=data.get('id'),
            message=data.get('message'),
            sender_id=data.get('sender_id'),
            family_id=data.get('family_id'),
            timestamp=data.get('timestamp'),
            thread_id=data.get('thread_id'),
            is_poll=data.get('is_poll', False),
            poll_options=data.get('poll_options')
        )
    
    def to_dict(self):
        """Convert Chat instance to a dictionary."""
        return {
            'id': self.id,
            'message': self.message,
            'sender_id': self.sender_id,
            'family_id': self.family_id,
            'timestamp': self.timestamp,
            'thread_id': self.thread_id,
            'is_poll': self.is_poll,
            'poll_options': self.poll_options
        }

class Memory:
    """Memory model for storing family photos and videos."""
    
    def __init__(self, id=None, title=None, photo_url=None, description=None, date=None, 
                 family_id=None, created_by=None, shared_with=None):
        self.id = id
        self.title = title
        self.photo_url = photo_url
        self.description = description
        self.date = date
        self.family_id = family_id
        self.created_by = created_by
        self.shared_with = shared_with
    
    @classmethod
    def from_dict(cls, data):
        """Create a Memory instance from a dictionary."""
        return cls(
            id=data.get('id'),
            title=data.get('title'),
            photo_url=data.get('photo_url'),
            description=data.get('description'),
            date=data.get('date'),
            family_id=data.get('family_id'),
            created_by=data.get('created_by'),
            shared_with=data.get('shared_with')
        )
    
    def to_dict(self):
        """Convert Memory instance to a dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'photo_url': self.photo_url,
            'description': self.description,
            'date': self.date,
            'family_id': self.family_id,
            'created_by': self.created_by,
            'shared_with': self.shared_with
        }

class Inventory:
    """Inventory model for household items."""
    
    def __init__(self, id=None, item_name=None, description=None, quantity=None, category=None, 
                 location=None, notes=None, restock_threshold=None, family_id=None, is_borrowed=False, 
                 borrowed_by=None):
        self.id = id
        self.item_name = item_name
        self.description = description
        self.quantity = quantity
        self.category = category
        self.location = location
        self.notes = notes
        self.restock_threshold = restock_threshold
        self.family_id = family_id
        self.is_borrowed = is_borrowed
        self.borrowed_by = borrowed_by
    
    @classmethod
    def from_dict(cls, data):
        """Create an Inventory instance from a dictionary."""
        return cls(
            id=data.get('id'),
            item_name=data.get('item_name'),
            description=data.get('description'),
            quantity=data.get('quantity'),
            category=data.get('category'),
            location=data.get('location'),
            notes=data.get('notes'),
            restock_threshold=data.get('restock_threshold'),
            family_id=data.get('family_id'),
            is_borrowed=data.get('is_borrowed', False),
            borrowed_by=data.get('borrowed_by')
        )
    
    def to_dict(self):
        """Convert Inventory instance to a dictionary."""
        return {
            'id': self.id,
            'item_name': self.item_name,
            'description': self.description,
            'quantity': self.quantity,
            'category': self.category,
            'location': self.location,
            'notes': self.notes,
            'restock_threshold': self.restock_threshold,
            'family_id': self.family_id,
            'is_borrowed': self.is_borrowed,
            'borrowed_by': self.borrowed_by
        }

class Health:
    """Health model for medication tracking and reminders."""
    
    def __init__(self, id=None, user_id=None, medication=None, dosage=None, frequency=None, 
                 reminder_time=None, start_date=None, end_date=None, notes=None):
        self.id = id
        self.user_id = user_id
        self.medication = medication
        self.dosage = dosage
        self.frequency = frequency
        self.reminder_time = reminder_time
        self.start_date = start_date
        self.end_date = end_date
        self.notes = notes
    
    @classmethod
    def from_dict(cls, data):
        """Create a Health instance from a dictionary."""
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id'),
            medication=data.get('medication'),
            dosage=data.get('dosage'),
            frequency=data.get('frequency'),
            reminder_time=data.get('reminder_time'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            notes=data.get('notes')
        )
    
    def to_dict(self):
        """Convert Health instance to a dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'medication': self.medication,
            'dosage': self.dosage,
            'frequency': self.frequency,
            'reminder_time': self.reminder_time,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'notes': self.notes
        }

class Emergency:
    """Emergency model for SOS features."""
    
    def __init__(self, id=None, user_id=None, family_id=None, location=None, timestamp=None, 
                 sos_status=False, resolved=False, resolved_by=None, notes=None):
        self.id = id
        self.user_id = user_id
        self.family_id = family_id
        self.location = location
        self.timestamp = timestamp
        self.sos_status = sos_status
        self.resolved = resolved
        self.resolved_by = resolved_by
        self.notes = notes
    
    @classmethod
    def from_dict(cls, data):
        """Create an Emergency instance from a dictionary."""
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id'),
            family_id=data.get('family_id'),
            location=data.get('location'),
            timestamp=data.get('timestamp'),
            sos_status=data.get('sos_status', False),
            resolved=data.get('resolved', False),
            resolved_by=data.get('resolved_by'),
            notes=data.get('notes')
        )
    
    def to_dict(self):
        """Convert Emergency instance to a dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'family_id': self.family_id,
            'location': self.location,
            'timestamp': self.timestamp,
            'sos_status': self.sos_status,
            'resolved': self.resolved,
            'resolved_by': self.resolved_by,
            'notes': self.notes
        }

class EmergencyContact:
    """Emergency Contact model for storing emergency contacts."""
    
    def __init__(self, id=None, name=None, relation=None, phone=None, email=None, address=None, 
                 notes=None, is_primary=False, family_id=None):
        self.id = id
        self.name = name
        self.relation = relation
        self.phone = phone
        self.email = email
        self.address = address
        self.notes = notes
        self.is_primary = is_primary
        self.family_id = family_id
    
    @classmethod
    def from_dict(cls, data):
        """Create an EmergencyContact instance from a dictionary."""
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            relation=data.get('relation'),
            phone=data.get('phone'),
            email=data.get('email'),
            address=data.get('address'),
            notes=data.get('notes'),
            is_primary=data.get('is_primary', False),
            family_id=data.get('family_id')
        )
    
    def to_dict(self):
        """Convert EmergencyContact instance to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'relation': self.relation,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'notes': self.notes,
            'is_primary': self.is_primary,
            'family_id': self.family_id
        }

class Settings:
    """Settings model for user preferences."""
    
    def __init__(self, id=None, user_id=None, theme=None, notifications=True, spherebot_enabled=True, 
                 location_sharing=False, dashboard_widgets=None):
        self.id = id
        self.user_id = user_id
        self.theme = theme
        self.notifications = notifications
        self.spherebot_enabled = spherebot_enabled
        self.location_sharing = location_sharing
        self.dashboard_widgets = dashboard_widgets
    
    @classmethod
    def from_dict(cls, data):
        """Create a Settings instance from a dictionary."""
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id'),
            theme=data.get('theme'),
            notifications=data.get('notifications', True),
            spherebot_enabled=data.get('spherebot_enabled', True),
            location_sharing=data.get('location_sharing', False),
            dashboard_widgets=data.get('dashboard_widgets')
        )
    
    def to_dict(self):
        """Convert Settings instance to a dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'theme': self.theme,
            'notifications': self.notifications,
            'spherebot_enabled': self.spherebot_enabled,
            'location_sharing': self.location_sharing,
            'dashboard_widgets': self.dashboard_widgets
        }
