#!/usr/bin/env python3
"""
Simple deployment verification script
Run this after deploying to Vercel to verify everything works
"""
import requests
import sys

def test_deployment(base_url):
    """Test key endpoints of the deployed application"""
    
    print(f"🧪 Testing deployment at: {base_url}")
    print("=" * 50)
    
    tests = [
        ("Home Page", "/"),
        ("Login Page", "/login"),
        ("Register Page", "/register"),
        ("Flight Search", "/flights/search"),
        ("Contact Page", "/contact"),
        ("Health Check", "/health"),
        ("Database Status", "/db-status"),
    ]
    
    passed = 0
    failed = 0
    
    for name, endpoint in tests:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {name} - OK ({response.status_code})")
                passed += 1
            else:
                print(f"❌ {name} - FAILED ({response.status_code})")
                failed += 1
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {name} - ERROR: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Deployment successful!")
        return True
    else:
        print("⚠️  Some tests failed. Check your deployment.")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_deployment.py <your-vercel-url>")
        print("Example: python test_deployment.py https://skystream.vercel.app")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    success = test_deployment(base_url)
    sys.exit(0 if success else 1)