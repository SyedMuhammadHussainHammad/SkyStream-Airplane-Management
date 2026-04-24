# 🎯 SkyStream - Clean Project Structure

## 📁 Essential Files Only

Your project is now clean and contains only the necessary files to run your website.

### 🏗️ Core Application Files

```
SkyStream/
├── backend/                 # Flask Application
│   ├── app.py              # Main Flask app
│   ├── routes.py           # URL routes & views
│   ├── models.py           # Database models
│   ├── forms.py            # Form definitions
│   ├── seed.py             # Database seeding
│   ├── requirements.txt    # Backend dependencies
│   ├── database.db         # SQLite database
│   └── instance/           # Database instance
│
├── templates/              # HTML Templates
│   ├── base.html           # Base template
│   ├── home.html           # Home page
│   ├── login.html          # Login page
│   ├── register.html       # Registration
│   ├── search.html         # Flight search
│   ├── packages.html       # Package selection
│   ├── passengers.html     # Passenger details
│   ├── checkout.html       # Payment page
│   ├── ticket.html         # Ticket display
│   ├── my_bookings.html    # User bookings
│   ├── admin_dashboard.html # Admin panel
│   ├── admin_add_flight.html # Add flights
│   ├── admin_staff_detail.html # Staff details
│   ├── staff_dashboard.html # Staff panel
│   ├── airplane_3d_integrated.html # Seat selection
│   ├── contact.html        # Contact page
│   ├── privacy.html        # Privacy policy
│   ├── terms.html          # Terms of service
│   └── errors/             # Error pages
│       ├── 403.html
│       ├── 404.html
│       └── 500.html
│
├── static/                 # Static Assets
│   ├── css/               # CSS files (empty)
│   └── js/                # JavaScript files (empty)
│
├── api/                   # Vercel Deployment
│   └── index.py           # Serverless function entry
│
├── instance/              # Database Instance
│   └── skystream.db       # Main database file
│
├── venv/                  # Virtual Environment
│   ├── bin/               # Python binaries
│   ├── lib/               # Python packages
│   └── include/           # Header files
│
├── .env                   # Environment variables
├── .gitignore            # Git ignore rules
├── README.md             # Project documentation
├── requirements.txt      # Project dependencies
├── run.py               # Simple run script
├── start_website.py     # Easy startup script
├── runtime.txt          # Python version for Vercel
└── vercel.json          # Vercel deployment config
```

## 🚀 How to Start Your Website

### Quick Start
```bash
python3 start_website.py
```

### Manual Start
```bash
source venv/bin/activate
cd backend
python app.py
```

### Alternative
```bash
python3 run.py
```

## 🌐 Access Your Website

- **Home**: http://127.0.0.1:5000/
- **Admin**: http://127.0.0.1:5000/admin/dashboard
- **Login**: admin@skystream.com / admin123

## 🗑️ Removed Files (39 files deleted)

✅ All test files  
✅ All backup files  
✅ All minimal files  
✅ All Docker files  
✅ All seed scripts (except main seed.py)  
✅ All migration scripts  
✅ All documentation files  
✅ All cache files  
✅ Duplicate templates  

## 📦 What's Left

**Total Files**: ~30 essential files only  
**Core App**: 7 Python files  
**Templates**: 18 HTML files  
**Config**: 5 configuration files  

Your project is now clean, minimal, and production-ready! 🎉