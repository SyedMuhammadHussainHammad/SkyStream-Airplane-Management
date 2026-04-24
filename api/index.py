#!/usr/bin/env python3
"""
Vercel serverless function entry point for SkyStream Flask app
"""
import os
import sys

# Add the backend directory to Python path
backend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import the Flask app
from app import app

# This is the WSGI application that Vercel will use
# Vercel expects the app to be available as 'app'
application = app

if __name__ == "__main__":
    app.run()