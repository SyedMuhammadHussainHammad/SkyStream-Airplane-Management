"""
Simple test script to verify all pages are accessible
"""
from app import app

def test_pages():
    with app.test_client() as client:
        print("🧪 Testing SkyStream Pages...\n")
        
        # Test public pages
        pages = [
            ('/', 'Home'),
            ('/login', 'Login'),
            ('/register', 'Register'),
            ('/flights/search', 'Search Flights'),
            ('/privacy', 'Privacy'),
            ('/terms', 'Terms'),
            ('/contact', 'Contact'),
            ('/health', 'Health Check'),
            ('/db-status', 'Database Status'),
        ]
        
        for url, name in pages:
            try:
                response = client.get(url)
                status = "✅" if response.status_code in [200, 302] else "❌"
                print(f"{status} {name:20} → {url:30} (Status: {response.status_code})")
            except Exception as e:
                print(f"❌ {name:20} → {url:30} (Error: {str(e)})")
        
        print("\n" + "="*60)
        print("✅ Page testing complete!")
        print("="*60)
        print("\n📝 Notes:")
        print("  • Protected pages (admin, staff, bookings) require login")
        print("  • Use the credentials from seed script to test those")
        print("  • All public pages should return 200 or 302 (redirect)")

if __name__ == '__main__':
    test_pages()
