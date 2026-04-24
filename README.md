# SkyStream Flight Booking System

A comprehensive flight booking and management system built with Flask.

## ✅ Status: RESOLVED - Application Running Successfully!

Your website has been successfully restored from serverless back to the original Flask application and is now running on **http://localhost:5000**

## Features

- Flight search and booking
- User registration and authentication
- Admin dashboard for flight and staff management
- Staff dashboard for roster management
- 3D airplane seat selection
- Payment processing simulation
- Ticket generation and management

## Quick Start

### 1. Start the Application

**Option 1: Using the startup script (Recommended)**
```bash
./start.sh
```

**Option 2: Using Python directly**
```bash
source venv/bin/activate
cd backend
python app.py
```

**Option 3: Using the run script**
```bash
python3 run.py
```

### 2. Access the Application

Open your browser and go to: **http://localhost:5000**

### 3. Test the Application

```bash
python3 test_app.py
```

## Default Admin Access

- **Email:** admin@skystream.com
- **Password:** admin123

## What Was Fixed

✅ Removed all serverless configurations (vercel.json, api/ directory)  
✅ Restored original Flask application structure  
✅ Fixed decorator import order issue in routes.py  
✅ Created virtual environment with all dependencies  
✅ Added convenient startup scripts  
✅ Verified application is running and accessible  

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
├── venv/            # Virtual environment
├── start.sh         # Startup script (recommended)
├── run.py           # Python run script
├── test_app.py      # Application test script
└── requirements.txt # Project dependencies
```

## Development

The application uses SQLite by default for local development. The database file will be created automatically when you first run the application.

For production deployment, set the `DATABASE_URL` environment variable to your production database URL.

## Environment Variables

- `SECRET_KEY`: Flask secret key (auto-generated if not set)
- `DATABASE_URL`: Database connection string (defaults to SQLite)
- `PORT`: Port to run the application (defaults to 5000)

## Troubleshooting

If you encounter any issues:

1. **Port already in use**: Kill existing processes with `lsof -ti:5000 | xargs kill -9`
2. **Dependencies missing**: Run `source venv/bin/activate && pip install -r requirements.txt`
3. **Test the app**: Run `python3 test_app.py` to verify everything is working