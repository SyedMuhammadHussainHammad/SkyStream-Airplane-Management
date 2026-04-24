#!/usr/bin/env python3
"""
Quick website checker - run this to verify your website is working
"""
import requests
import sys

def check_website():
    base_urls = [
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://0.0.0.0:5000"
    ]
    
    print("🔍 Checking SkyStream website...")
    print("=" * 50)
    
    working_url = None
    
    for url in base_urls:
        try:
            print(f"Testing {url}...")
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ SUCCESS: Website is running at {url}")
                working_url = url
                break
            else:
                print(f"❌ FAILED: {url} returned {response.status_code}")
        except requests.exceptions.ConnectionRefusedError:
            print(f"❌ FAILED: {url} - Connection refused (server not running)")
        except requests.exceptions.Timeout:
            print(f"❌ FAILED: {url} - Timeout")
        except Exception as e:
            print(f"❌ FAILED: {url} - {e}")
    
    if working_url:
        print("\n🎉 Your website is working!")
        print(f"📱 Open this URL in your browser: {working_url}")
        print("\n📋 Available pages:")
        pages = [
            "/", "/login", "/register", "/flights/search", 
            "/contact", "/privacy", "/terms"
        ]
        
        for page in pages:
            try:
                resp = requests.get(f"{working_url}{page}", timeout=3)
                status = "✅" if resp.status_code == 200 else "❌"
                print(f"  {status} {working_url}{page}")
            except:
                print(f"  ❌ {working_url}{page}")
                
    else:
        print("\n❌ Website is not running!")
        print("\n🚀 To start your website:")
        print("1. Open terminal")
        print("2. Run: source venv/bin/activate")
        print("3. Run: python backend/app.py")
        print("4. Open http://localhost:5000 in your browser")

if __name__ == "__main__":
    check_website()