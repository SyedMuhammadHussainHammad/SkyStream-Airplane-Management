#!/usr/bin/env python3
"""
Simple test script to verify the SkyStream application is working
"""
import sys
import os
import requests

# Add backend to path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

def test_app():
    """Test if the application is running and responding"""
    try:
        # Test home page
        response = requests.get('http://localhost:5000', timeout=5)
        if response.status_code == 200:
            print("✅ Home page is accessible")
        else:
            print(f"❌ Home page returned status code: {response.status_code}")
            return False
        
        # Test health endpoint
        response = requests.get('http://localhost:5000/health', timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint is working")
            health_data = response.json()
            print(f"   Status: {health_data.get('status', 'unknown')}")
        else:
            print(f"❌ Health endpoint returned status code: {response.status_code}")
        
        # Test database status
        response = requests.get('http://localhost:5000/db-status', timeout=5)
        if response.status_code == 200:
            print("✅ Database is accessible")
            db_data = response.json()
            print(f"   Users: {db_data.get('tables', {}).get('users', 0)}")
            print(f"   Flights: {db_data.get('tables', {}).get('flights', 0)}")
            print(f"   Planes: {db_data.get('tables', {}).get('planes', 0)}")
        else:
            print(f"❌ Database status returned status code: {response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to the application. Make sure it's running on http://localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Error testing application: {e}")
        return False

if __name__ == "__main__":
    print("Testing SkyStream Application...")
    print("=" * 40)
    
    if test_app():
        print("\n🎉 Application is running successfully!")
        print("🌐 Access your website at: http://localhost:5000")
        print("🔑 Admin login: admin@skystream.com / admin123")
    else:
        print("\n❌ Application test failed. Please check the server logs.")