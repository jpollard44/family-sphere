import os
from datetime import timedelta

# Base directory of the application
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Application Settings
class Config:
    # Secret key for session management and CSRF protection
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'familysphere.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-Login settings
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    
    # File upload settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # SphereBot AI settings
    SPHEREBOT_ENABLED = True
    GROK_API_KEY = os.environ.get('GROK_API_KEY') or 'xai-Tko4SwhVpHl4cIh36vvMxdRTdGCA2h3IXiZCUtuXEHBqOVSqT01t5VCEHmQy3bnvYPXVKgUaYzM7ywJx'
    GROK_API_URL = os.environ.get('GROK_API_URL') or 'https://api.x.ai/v1/chat/completions'
    GROK_MODEL = os.environ.get('GROK_MODEL') or 'grok-2-latest'
    
    # Email settings (for notifications and password reset)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Timezone settings
    TIMEZONE = os.environ.get('TIMEZONE') or 'UTC'
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.path.join(BASE_DIR, 'logs', 'familysphere.log')


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'familysphere_dev.db')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    # Use PostgreSQL in production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://user:password@localhost/familysphere'
    
    # In production, ensure a strong secret key is set
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # CSRF settings for production
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SSL_STRICT = False  # Allow CSRF tokens to work in both HTTP and HTTPS
    
    # Additional production settings
    PREFERRED_URL_SCHEME = 'https'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Get configuration based on environment
def get_config():
    env = os.environ.get('FLASK_ENV', 'default')
    return config[env]
