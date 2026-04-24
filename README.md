# SkyStream Flight Booking System

A comprehensive flight booking and management system built with Flask.

## Features

- Flight search and booking
- User registration and authentication
- Admin dashboard for flight and staff management
- Staff dashboard for roster management
- 3D airplane seat selection
- Payment processing simulation
- Ticket generation and management

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python run.py
```

Or alternatively, run from the backend directory:

```bash
cd backend
python app.py
```

### 3. Access the Application

Open your browser and go to: http://localhost:5000

## Default Admin Access

- Email: admin@skystream.com
- Password: admin123

## Project Structure

```
├── backend/           # Flask application
│   ├── app.py        # Main application file
│   ├── routes.py     # URL routes and views
│   ├── models.py     # Database models
│   ├── forms.py      # WTForms definitions
│   └── requirements.txt
├── templates/        # HTML templates
├── static/          # CSS, JS, and static files
├── run.py           # Simple run script
└── requirements.txt # Project dependencies
```

## Development

The application uses SQLite by default for local development. The database file will be created automatically when you first run the application.

For production deployment, set the `DATABASE_URL` environment variable to your production database URL.

## Environment Variables

- `SECRET_KEY`: Flask secret key (auto-generated if not set)
- `DATABASE_URL`: Database connection string (defaults to SQLite)
- `PORT`: Port to run the application (defaults to 5000)