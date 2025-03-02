import requests
import os
from datetime import datetime

# Test script to verify calendar export functionality
def test_export_calendar():
    print("Testing calendar export functionality...")
    
    # Base URL of the application
    base_url = "http://localhost:8089"
    
    # Login to get a session
    login_url = f"{base_url}/login"
    
    # Replace with valid credentials
    login_data = {
        "username": "test_user",
        "password": "test_password"
    }
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Get CSRF token
    response = session.get(login_url)
    if response.status_code != 200:
        print(f"Failed to access login page: {response.status_code}")
        return
    
    # Extract CSRF token from the response
    csrf_token = None
    for cookie in session.cookies:
        if cookie.name == 'csrf_token':
            csrf_token = cookie.value
            break
    
    if not csrf_token:
        print("Failed to get CSRF token")
        return
    
    # Login
    login_data['csrf_token'] = csrf_token
    response = session.post(login_url, data=login_data)
    
    if response.status_code != 200 and not response.history:
        print(f"Login failed: {response.status_code}")
        return
    
    # Export calendar
    export_url = f"{base_url}/export_calendar"
    response = session.get(export_url)
    
    if response.status_code != 200:
        print(f"Export failed: {response.status_code}")
        return
    
    # Save the exported calendar
    filename = f"test_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
    with open(filename, 'wb') as f:
        f.write(response.content)
    
    print(f"Calendar exported successfully to {filename}")
    print(f"Content type: {response.headers.get('Content-Type')}")
    print(f"Content length: {len(response.content)} bytes")
    
    # Print the first 200 characters of the file
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read(200)
        print(f"File preview: {content}...")

if __name__ == "__main__":
    test_export_calendar()
