#!/usr/bin/env python3
"""
Vercel serverless function entry point for SkyStream Flask app
"""
import os
import sys

# Add the backend directory to Python path
backend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
sys.path.insert(0, backend_dir)

# Import the Flask app
from app import app

# Vercel expects the app to be available as 'app'
# This is the WSGI application that Vercel will use
if __name__ == "__main__":
    app.run()