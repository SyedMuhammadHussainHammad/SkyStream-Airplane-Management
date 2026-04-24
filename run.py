#!/usr/bin/env python3
"""
Simple script to run the SkyStream Flask application
"""
import os
import sys
import subprocess

def activate_venv_and_run():
    """Activate virtual environment and run the application"""
    venv_path = os.path.join(os.path.dirname(__file__), 'venv')
    
    if os.path.exists(venv_path):
        # Use the virtual environment's Python
        if os.name == 'nt':  # Windows
            python_path = os.path.join(venv_path, 'Scripts', 'python.exe')
        else:  # Unix/Linux/macOS
            python_path = os.path.join(venv_path, 'bin', 'python')
        
        if os.path.exists(python_path):
            print("=" * 50)
            print("SkyStream Flight Booking System")
            print("=" * 50)
            print("🔧 Using virtual environment...")
            
            # Run the app using the virtual environment's Python
            backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
            env = os.environ.copy()
            env['PYTHONPATH'] = backend_dir
            
            print("✅ Starting application...")
            print("🌐 Access the application at: http://localhost:5000")
            print("🔑 Default admin login: admin@skystream.com / admin123")
            print("\nPress Ctrl+C to stop the server")
            print("-" * 50)
            
            subprocess.run([python_path, os.path.join(backend_dir, 'app.py')], 
                         cwd=backend_dir, env=env)
            return True
    
    return False

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
        print("python3 -m venv venv")
        print("source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
        print("pip install -r requirements.txt")
        return False

def main():
    # First try to use virtual environment
    if activate_venv_and_run():
        return
    
    # Fallback to system Python
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