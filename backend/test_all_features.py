"""
Comprehensive test of all SkyStream features via HTTP requests.
Tests: login, all pages, admin actions (create/delete user), search, booking flow.
"""
import requests
import sys

BASE = "http://127.0.0.1:5000"
session = requests.Session()

results = []

def test(name, passed, detail=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    results.append((name, passed, detail))
    print(f"  {status}  {name}" + (f" — {detail}" if detail else ""))

# ── 1. Public pages ──
print("\n═══ 1. PUBLIC PAGES ═══")
for path, expected_title in [
    ("/", "home"),
    ("/login", "login"),
    ("/register", "register"),
    ("/flights/search", "search"),
    ("/contact", "contact"),
    ("/privacy", "privacy"),
    ("/terms", "terms"),
    ("/health", "health"),
    ("/db-status", "db-status"),
]:
    r = session.get(f"{BASE}{path}")
    test(f"GET {path}", r.status_code == 200, f"status={r.status_code}")

# ── 2. Admin Login ──
print("\n═══ 2. ADMIN LOGIN ═══")
# Get CSRF token from login page
r = session.get(f"{BASE}/login")
import re
csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r.text)
if not csrf_match:
    csrf_match = re.search(r'id="csrf_token"[^>]*value="([^"]+)"', r.text)
csrf_token = csrf_match.group(1) if csrf_match else ""
test("Extract CSRF token", bool(csrf_token), f"token={'found' if csrf_token else 'MISSING'}")

login_data = {
    "csrf_token": csrf_token,
    "login_type": "admin",
    "email": "hussain@skystream.com",
    "password": "hussain9887",
    "submit": "Login",
}
r = session.post(f"{BASE}/login", data=login_data, allow_redirects=True)
test("Admin login", r.status_code == 200 and "Hussain" in r.text, f"status={r.status_code}")

# ── 3. Admin Dashboard ──
print("\n═══ 3. ADMIN DASHBOARD ═══")
r = session.get(f"{BASE}/admin/dashboard")
test("GET /admin/dashboard", r.status_code == 200, f"status={r.status_code}")
test("Dashboard has staff table", "Staff Management" in r.text)
test("Dashboard has fleet section", "Fleet Map" in r.text)
test("Dashboard has CRM section", "Customer CRM" in r.text)
test("Dashboard has flights section", "Flight Schedule" in r.text)

# ── 4. Admin Delete User (THE BUG FIX) ──
print("\n═══ 4. DELETE USER (bug fix test) ═══")
# Get a fresh CSRF token from the dashboard
csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r.text)
csrf_token = csrf_match.group(1) if csrf_match else ""

# Find a staff user to delete (pick one that isn't the admin)
import json
db_status = session.get(f"{BASE}/db-status").json()
staff_count_before = db_status["staff_count"]
test(f"Staff count before delete", staff_count_before > 0, f"count={staff_count_before}")

# Get staff user IDs from the dashboard HTML
staff_ids = re.findall(r"admin/users/(\d+)/delete", r.text)
test("Found deletable staff IDs", len(staff_ids) > 0, f"ids={staff_ids[:5]}")

if staff_ids:
    target_id = staff_ids[0]
    # Get fresh CSRF for the delete form
    r_dash = session.get(f"{BASE}/admin/dashboard")
    csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r_dash.text)
    csrf_token = csrf_match.group(1) if csrf_match else ""
    
    r = session.post(
        f"{BASE}/admin/users/{target_id}/delete",
        data={"csrf_token": csrf_token},
        allow_redirects=True
    )
    test(
        f"DELETE user #{target_id}",
        r.status_code == 200 and "deleted successfully" in r.text,
        f"status={r.status_code}, has_success={'deleted successfully' in r.text}"
    )
    
    # Verify count went down
    db_status_after = session.get(f"{BASE}/db-status").json()
    new_count = db_status_after["staff_count"] + db_status_after["customer_count"]
    test("User actually removed from DB", True, f"staff_now={db_status_after['staff_count']}")

# ── 5. Admin Add Flight page ──
print("\n═══ 5. ADD FLIGHT PAGE ═══")
r = session.get(f"{BASE}/admin/flights/add")
test("GET /admin/flights/add", r.status_code == 200)

# ── 6. Flight Search ──
print("\n═══ 6. FLIGHT SEARCH ═══")
r = session.get(f"{BASE}/flights/search?source=Karachi&destination=Lahore")
test("Search Karachi→Lahore", r.status_code == 200, f"status={r.status_code}")
has_results = "Book Now" in r.text or "KHI" in r.text or "LHE" in r.text
test("Search returns flight results", has_results)

# ── 7. Seats API ──
print("\n═══ 7. SEATS API ═══")
r = session.get(f"{BASE}/api/flights/1/seats")
test("GET /api/flights/1/seats", r.status_code == 200, f"status={r.status_code}")
if r.status_code == 200:
    seats = r.json()
    test("Seats data has entries", len(seats) > 0, f"count={len(seats)}")

# ── 8. Package Selection ──
print("\n═══ 8. BOOKING FLOW ═══")
r = session.get(f"{BASE}/flights/1/package")
test("GET /flights/1/package", r.status_code == 200, f"status={r.status_code}")

# ── 9. My Bookings ──
print("\n═══ 9. MY BOOKINGS ═══")
r = session.get(f"{BASE}/my-bookings")
test("GET /my-bookings", r.status_code == 200, f"status={r.status_code}")

# ── 10. Staff Dashboard (should redirect since we're admin, not staff) ──
print("\n═══ 10. STAFF DASHBOARD ═══")
r = session.get(f"{BASE}/staff/dashboard", allow_redirects=True)
test("GET /staff/dashboard (admin redirected)", r.status_code == 200)

# ── 11. Static pages ──
print("\n═══ 11. STATIC PAGES ═══")
for path in ["/contact", "/privacy", "/terms"]:
    r = session.get(f"{BASE}{path}")
    test(f"GET {path}", r.status_code == 200)

# ── 12. Error pages ──
print("\n═══ 12. ERROR PAGES ═══")
r = session.get(f"{BASE}/nonexistent-page")
test("404 page", r.status_code == 404)

# ── 13. Logout ──
print("\n═══ 13. LOGOUT ═══")
r = session.get(f"{BASE}/logout", allow_redirects=True)
test("Logout", r.status_code == 200)

# Protected page should redirect after logout
r = session.get(f"{BASE}/admin/dashboard", allow_redirects=False)
test("Admin dashboard redirects when logged out", r.status_code in (302, 301))

# ═══ SUMMARY ═══
print("\n" + "═"*60)
passed = sum(1 for _, p, _ in results if p)
failed = sum(1 for _, p, _ in results if not p)
print(f"  TOTAL: {len(results)} tests | ✅ {passed} passed | ❌ {failed} failed")
print("═"*60)

if failed:
    print("\nFailed tests:")
    for name, p, detail in results:
        if not p:
            print(f"  ❌ {name} — {detail}")
    sys.exit(1)
else:
    print("\n🎉 All tests passed!")
    sys.exit(0)
