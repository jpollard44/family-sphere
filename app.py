from flask import Flask
from flask_login import LoginManager
import os
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'default-secret-key')

# Additional CSRF configuration
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_SSL_STRICT'] = False  # Allow CSRF tokens to work in both HTTP and HTTPS
app.config['WTF_CSRF_METHODS'] = ['POST', 'PUT', 'PATCH', 'DELETE']

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Import models and routes
from models import User
from routes import *

@login_manager.user_loader
def load_user(user_id):
    from supabase_config import get_supabase_client
    supabase = get_supabase_client()
    
    # Query the users table for the user with the given ID
    response = supabase.table('users').select('*').eq('id', user_id).execute()
    
    if response.data:
        user_data = response.data[0]
        return User(
            id=user_data['id'],
            username=user_data['username'],
            password_hash=user_data['password_hash'],
            role=user_data['role'],
            family_id=user_data['family_id']
        )
    return None

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'
    port = int(os.environ.get('PORT', 8089))
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
