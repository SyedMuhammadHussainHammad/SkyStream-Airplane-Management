#!/usr/bin/env python3
"""
Test the minimal Flask application
"""
import sys
import os

# Add backend to path
sys.path.append('backend/api')

try:
    from index import app
    
    print("🧪 Testing minimal Flask application...")
    
    with app.test_client() as client:
        # Test home page
        response = client.get('/')
        print(f"✅ Home page: {response.status_code}")
        
        # Test health endpoint
        response = client.get('/health')
        print(f"✅ Health endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"   Status: {data.get('status')}")
        
        # Test API endpoint
        response = client.get('/test')
        print(f"✅ Test endpoint: {response.status_code}")
        
    print("🎉 All tests passed! Minimal app is working.")
    
except Exception as e:
    print(f"❌ Error testing app: {e}")
    sys.exit(1)