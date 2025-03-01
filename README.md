# FamilySphere

FamilySphere is a comprehensive web-based platform designed to streamline family management and coordination. It serves as a centralized hub where families can organize daily activities, finances, chores, communication, memories, and more, while facilitating connections with extended family or trusted groups.

## Features

FamilySphere offers a suite of features, each enhanced by SphereBot AI:

- **Shared Calendar**: Manage events with conflict detection and sharing options
- **Financial Hub**: Track budgets, allowances, and goals
- **Chore Management**: Assign tasks with a points-based auction system
- **Communication Center**: Enable family chats and polls
- **Memory Vault**: Store and share photos/videos
- **Household Inventory**: Track items and facilitate borrowing
- **Health Tracker**: Monitor medications with reminders
- **Extended Family Connection**: Build family trees and invite members
- **Personal Dashboards**: Customizable widgets
- **Emergency Features**: SOS alerts and location sharing
- **Member Management**: Admins add users with roles
- **Data Sharing**: Share events or tasks with other families
- **Settings**: Customize themes and privacy

## Technology Stack

- **Backend**: Python with Flask, Flask-SQLAlchemy, Flask-Login
- **Frontend**: HTML, CSS (Bootstrap), JavaScript
- **Database**: SQLite (development), PostgreSQL (production-ready)
- **AI Integration**: SphereBot AI leverages an LLM API for intelligent features

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/familysphere.git
   cd familysphere
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Run the application:
   ```
   python app.py
   ```

6. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

## User Roles

- **Admin**: Full control, including member management
- **Member**: Broad access, restricted from sensitive data unless permitted
- **Kid**: Limited to chores, chat, and memories
- **Extended**: Custom access to shared content

## SphereBot AI

SphereBot AI is an intelligent assistant that enhances the user experience by:

- Providing context-aware suggestions
- Automating routine tasks
- Analyzing family data to offer insights
- Responding to natural language queries

## Project Structure

```
FamilySphere/
├── app.py             # Main Flask app
├── models.py          # Database models
├── routes.py          # Backend logic and routes
├── templates/         # HTML templates
├── static/            # CSS, JS, and images
└── requirements.txt   # Dependencies
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Deployment on Render.com

FamilySphere can be easily deployed on Render.com using the following steps:

### Option 1: Deploy via GitHub

1. Fork or push this repository to your GitHub account
2. Log in to [Render.com](https://render.com)
3. Click "New" and select "Web Service"
4. Connect your GitHub account and select the FamilySphere repository
5. Configure the following settings:
   - **Name**: family-sphere (or your preferred name)
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free (or select another plan if needed)
6. Add the following environment variables:
   - `SUPABASE_URL`: Your Supabase URL
   - `SUPABASE_ANON_KEY`: Your Supabase anonymous key
   - `SECRET_KEY`: A secure random string
   - `FLASK_ENV`: production
   - `FLASK_APP`: app.py
7. Click "Create Web Service"

### Option 2: Deploy via Render Blueprint

1. Fork or push this repository to your GitHub account
2. Ensure the `render.yaml` file is in the root directory
3. Log in to [Render.com](https://render.com)
4. Click "New" and select "Blueprint"
5. Connect your GitHub account and select the FamilySphere repository
6. Render will automatically detect the `render.yaml` file and configure the services
7. Add your environment variables when prompted
8. Click "Apply"

### Post-Deployment

After deployment, you'll need to:

1. Set up your database tables in Supabase if not already done
2. Create an initial admin user through the registration page
3. Configure any additional settings through the application interface

Your FamilySphere application will be available at the URL provided by Render (typically `https://your-service-name.onrender.com`).

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask team for the excellent web framework
- Bootstrap team for the responsive design components
- All contributors who have helped shape this project
