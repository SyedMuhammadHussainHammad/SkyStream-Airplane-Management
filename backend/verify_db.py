#!/usr/bin/env python3
"""
Database Verification Script
===========================
Verifies the database contents after seeding.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, StaffProfile, Flight, Plane
from datetime import datetime

def verify_database():
    """Verify database contents."""
    print("🔍 Verifying Database Contents")
    print("=" * 50)
    
    with app.app_context():
        # Check admin user
        admin = User.query.filter_by(email='hussain@skystream.com').first()
        if admin:
            print(f"✅ Admin user found: {admin.first_name} {admin.last_name}")
            print(f"   Email: {admin.email}")
            print(f"   Role: {admin.role}")
        else:
            print("❌ Admin user not found!")
        
        # Check staff members
        staff = User.query.filter_by(role='staff').all()
        print(f"\n👥 Staff Members ({len(staff)} found):")
        for s in staff:
            print(f"   • {s.first_name} {s.last_name} ({s.staff_id}) - {s.email}")
        
        # Check planes
        planes = Plane.query.all()
        print(f"\n✈️ Aircraft Fleet ({len(planes)} planes):")
        for p in planes:
            print(f"   • {p.plane_id} - {p.model} (Capacity: {p.capacity})")
        
        # Check flights
        flights = Flight.query.all()
        print(f"\n🗓️ Flight Schedule ({len(flights)} flights):")
        
        # Group flights by date
        flights_by_date = {}
        for f in flights:
            date_key = f.departure_time.strftime('%Y-%m-%d')
            if date_key not in flights_by_date:
                flights_by_date[date_key] = []
            flights_by_date[date_key].append(f)
        
        for date, day_flights in sorted(flights_by_date.items()):
            print(f"   📅 {date}: {len(day_flights)} flights")
        
        # Check city connectivity
        origins = set(f.origin for f in flights)
        destinations = set(f.destination for f in flights)
        print(f"\n🌍 City Connectivity:")
        print(f"   Origins: {len(origins)} cities")
        print(f"   Destinations: {len(destinations)} cities")
        
        all_cities = origins.union(destinations)
        for city in sorted(all_cities):
            outbound = len([f for f in flights if f.origin == city])
            inbound = len([f for f in flights if f.destination == city])
            print(f"   • {city}: {outbound} outbound, {inbound} inbound")
        
        # Check customers
        customers = User.query.filter_by(role='customer').all()
        print(f"\n👤 Sample Customers ({len(customers)} found):")
        for c in customers:
            print(f"   • {c.first_name} {c.last_name} - {c.email}")
        
        print("\n" + "=" * 50)
        print("✅ Database verification completed!")

if __name__ == '__main__':
    verify_database()