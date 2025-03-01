from app import app
from database import db

# Create application context
with app.app_context():
    # Create all tables
    db.create_all()
    print("Database updated successfully!")
