#!/usr/bin/env python3
"""
Simple script to start SkyStream website
"""
import os
import sys
import subprocess
import time
import webbrowser

def start_website():
    print("🚀 Starting SkyStream Flight Booking System")
    print("=" * 50)
    
    # Check if virtual environment exists
    venv_path = "venv"
    if not os.path.exists(venv_path):
        print("❌ Virtual environment not found!")
        print("Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt")
        return False
    
    # Start the Flask application
    try:
        print("🔧 Starting Flask server...")
        
        # Change to backend directory
        backend_dir = "backend"
        if not os.path.exists(backend_dir):
            print("❌ Backend directory not found!")
            return False
        
        # Start the server
        env = os.environ.copy()
        env['FLASK_ENV'] = 'development'
        env['FLASK_DEBUG'] = '1'
        
        print("✅ Server starting...")
        print("🌐 Your website will be available at: http://127.0.0.1:5000")
        print("🔑 Default admin login: admin@skystream.com / admin123")
        print("\n📋 Available pages:")
        print("  • Home: http://127.0.0.1:5000/")
        print("  • Login: http://127.0.0.1:5000/login")
        print("  • Register: http://127.0.0.1:5000/register")
        print("  • Search Flights: http://127.0.0.1:5000/flights/search")
        print("  • Admin Dashboard: http://127.0.0.1:5000/admin/dashboard")
        print("\nPress Ctrl+C to stop the server")
        print("-" * 50)
        
        # Run the Flask app
        if os.name == 'nt':  # Windows
            python_cmd = os.path.join(venv_path, 'Scripts', 'python.exe')
        else:  # Unix/Linux/macOS
            python_cmd = os.path.join(venv_path, 'bin', 'python')
        
        subprocess.run([python_cmd, 'app.py'], cwd=backend_dir, env=env)
        
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped successfully!")
        return True
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

if __name__ == "__main__":
    start_website()