#!/usr/bin/env python3
"""
Simple script to run the SkyStream Flask application
"""
import os
import sys

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import flask
        import flask_sqlalchemy
        import flask_bcrypt
        import flask_login
        import flask_wtf
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("\nPlease install the required dependencies:")
        print("pip install -r requirements.txt")
        print("\nOr if you're using a virtual environment:")
        print("python -m venv venv")
        print("source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
        print("pip install -r requirements.txt")
        return False

def main():
    print("=" * 50)
    print("SkyStream Flight Booking System")
    print("=" * 50)
    
    if not check_dependencies():
        return
    
    # Add backend directory to path
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    sys.path.insert(0, backend_dir)

    # Change to backend directory
    os.chdir(backend_dir)

    # Import and run the app
    try:
        from app import app
        print("\n✅ Application loaded successfully!")
        print("🌐 Access the application at: http://localhost:5000")
        print("🔑 Default admin login: admin@skystream.com / admin123")
        print("\nPress Ctrl+C to stop the server")
        print("-" * 50)
        app.run(host="0.0.0.0", port=5000, debug=True)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        print("\nPlease check that all dependencies are installed correctly.")

if __name__ == "__main__":
    main()