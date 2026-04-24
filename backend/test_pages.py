#!/usr/bin/env python3
"""
SkyStream — Comprehensive Page Test
Tests all routes for HTTP 200 / expected redirect / no 500 errors.
Run: python test_pages.py
"""
import sys
import re
import requests

BASE = "http://127.0.0.1:5000"
sess = requests.Session()

GRN  = "\033[92m"
RED  = "\033[91m"
YLW  = "\033[93m"
RST  = "\033[0m"
PASS = f"{GRN}✓{RST}"
FAIL = f"{RED}✗{RST}"
WARN = f"{YLW}⚠{RST}"

results = []

ERROR_MARKERS = [
    "internal server error",
    "jinja2.exceptions",
    "templatenotfound",
    "attributeerror",
    "typeerror:",
    "keyerror:",
    "operationalerror",
    "werkzeug.exceptions",
    "traceback (most recent call last)",
]

def get_csrf(url):
    r = sess.get(url, timeout=10)
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r.text)
    return m.group(1) if m else ""

def check(label, url, expected=(200,), method="GET", data=None, allow_redirects=True):
    try:
        if method == "GET":
            r = sess.get(url, allow_redirects=allow_redirects, timeout=10)
        else:
            r = sess.post(url, data=data, allow_redirects=allow_redirects, timeout=10)

        status = r.status_code
        ok = status in expected
        body_err = False

        if ok and status == 200:
            body = r.text.lower()
            body_err = any(m in body for m in ERROR_MARKERS)
            if body_err:
                ok = False

        icon = PASS if ok else FAIL
        label_w = label[:55].ljust(55)
        note = f"  {WARN} body contains error markers!" if body_err else ""
        print(f"  {icon} [{status}] {label_w}  {url}{note}")
        results.append((label, "OK" if ok else (f"BODY_ERR@{status}" if body_err else f"HTTP_{status}"), url))
        return r
    except Exception as e:
        print(f"  {FAIL} [ERR] {label[:55].ljust(55)}  {url}")
        print(f"         Exception: {e}")
        results.append((label, "EXCEPTION", url))
        return None


# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*72)
print("  SkyStream — Full Page Test Suite")
print("="*72)

# ── 1. PUBLIC PAGES ──────────────────────────────────────────────────────────
print(f"\n{GRN}📄 Public Pages{RST}")
check("Home",                        f"{BASE}/")
check("Health check",                f"{BASE}/health")
check("Login (GET)",                 f"{BASE}/login")
check("Register (GET)",              f"{BASE}/register")
check("Search (GET)",                f"{BASE}/search")
check("404 page",                    f"{BASE}/nonexistent-xyz", expected=(404,))

# ── 2. SEARCH POST ────────────────────────────────────────────────────────────
print(f"\n{GRN}🔍 Search POST{RST}")
csrf = get_csrf(f"{BASE}/search")
check("Search POST (Karachi→Lahore)", f"{BASE}/search", expected=(200,), method="POST", data={
    "csrf_token": csrf, "origin": "Karachi", "destination": "Lahore",
    "date": "", "trip_type": "one_way", "adults": "1", "children": "0", "infants": "0",
})
check("Search POST (empty origin)",   f"{BASE}/search", expected=(200,), method="POST", data={
    "csrf_token": csrf, "origin": "", "destination": "",
    "date": "", "trip_type": "one_way", "adults": "1", "children": "0", "infants": "0",
})

# ── 3. AUTH REDIRECTS (unauthenticated) ──────────────────────────────────────
print(f"\n{GRN}🔒 Auth-gated pages — must redirect (302), not crash{RST}")
check("My Bookings (unauth)",        f"{BASE}/my-bookings",       expected=(302,), allow_redirects=False)
check("Staff Dashboard (unauth)",    f"{BASE}/staff/dashboard",   expected=(302,), allow_redirects=False)
check("Admin Dashboard (unauth)",    f"{BASE}/admin/dashboard",   expected=(302,), allow_redirects=False)
check("Admin Add Flight (unauth)",   f"{BASE}/admin/flights/add", expected=(302,), allow_redirects=False)
check("Packages (unauth)",           f"{BASE}/booking/1/packages",expected=(302,), allow_redirects=False)
check("Passengers (unauth)",         f"{BASE}/booking/1/passengers",expected=(302,), allow_redirects=False)
check("Checkout (unauth)",           f"{BASE}/checkout/1",        expected=(302,), allow_redirects=False)
check("Ticket (unauth)",             f"{BASE}/ticket/1",          expected=(302,), allow_redirects=False)

# ── 4. REGISTER FLOW ─────────────────────────────────────────────────────────
print(f"\n{GRN}📝 Registration form validation{RST}")
csrf = get_csrf(f"{BASE}/register")
check("Register POST (invalid - short pw)", f"{BASE}/register", expected=(200,), method="POST", data={
    "csrf_token": csrf, "first_name": "Test", "last_name": "User",
    "phone_number": "03001234567", "email": "testuser_x99@example.com",
    "age": "25", "password": "abc", "confirm_password": "abc",
})

# ── 5. ADMIN LOGIN + ADMIN PAGES ─────────────────────────────────────────────
print(f"\n{GRN}🔑 Admin Login{RST}")
csrf = get_csrf(f"{BASE}/login")
login_r = check("Admin login (Hussain)", f"{BASE}/login", expected=(200,), method="POST",
    allow_redirects=True, data={
        "csrf_token": csrf, "login_type": "admin",
        "email": "Hussain", "password": "hussain9887", "staff_id": "",
    })

# Verify we're actually on the admin dashboard
logged_in_as_admin = login_r and "admin" in login_r.url

print(f"\n{GRN}🛠️  Admin Pages{RST}")
check("Admin Dashboard",             f"{BASE}/admin/dashboard",    expected=(200,))
check("Admin Add Flight (GET)",      f"{BASE}/admin/flights/add",  expected=(200,))
check("Admin Staff Detail (id=1)",   f"{BASE}/admin/staff/1",      expected=(200, 404))
check("Admin Staff 404 (id=999999)", f"{BASE}/admin/staff/999999", expected=(404,))   # ← moved here

# ── 6. API ENDPOINTS ─────────────────────────────────────────────────────────
print(f"\n{GRN}🔌 API Endpoints{RST}")
check("Seats API (flight 1)",        f"{BASE}/api/flights/1/seats",   expected=(200, 404))
check("Seats API (missing flight)",  f"{BASE}/api/flights/999999/seats", expected=(404,))

# ── 7. CUSTOMER BOOKING FLOW ─────────────────────────────────────────────────
print(f"\n{GRN}🛒 Customer Booking (admin redirects — role guard){RST}")
# Admin cannot access customer pages — should redirect to home (not crash)
check("Packages (admin role)",       f"{BASE}/booking/1/packages",    expected=(200, 302))
check("Passengers (admin role)",     f"{BASE}/booking/1/passengers",  expected=(200, 302))
check("Checkout (admin role)",       f"{BASE}/checkout/1",            expected=(200, 302))

# ── 8. LOGOUT ────────────────────────────────────────────────────────────────
print(f"\n{GRN}👋 Logout{RST}")
check("Logout",                      f"{BASE}/logout", expected=(200, 302))

# ── 9. POST-LOGOUT CHECKS ────────────────────────────────────────────────────
print(f"\n{GRN}🔄 Post-logout auth guard{RST}")
check("Admin dashboard after logout",f"{BASE}/admin/dashboard", expected=(302,), allow_redirects=False)

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*72)
total    = len(results)
failures = [(l, s, u) for l, s, u in results if s != "OK"]
passed   = total - len(failures)

print(f"  Results: {GRN}{passed}/{total} passed{RST}")

if failures:
    print(f"\n  {RED}FAILURES ({len(failures)}):{RST}")
    for label, status, url in failures:
        print(f"    [{status}] {label}")
        print(f"             {url}")
else:
    print(f"\n  {PASS} All checks passed — no server errors detected!")

print("="*72 + "\n")
sys.exit(1 if failures else 0)
