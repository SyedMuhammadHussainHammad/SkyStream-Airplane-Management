#!/usr/bin/env python3
"""
Quick Database Seeding Script for SkyStream Airlines
===================================================

Creates:
- Admin user: hussain@skystream.com / hussain9887
- 8 staff members
- 7 days of flights between all Pakistani cities
- Aircraft fleet
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, bcrypt
from models import (
    User, StaffProfile, Flight, Roster, Plane, Seat,
    Booking, Passenger, Ticket, SeatLock, PaymentTransaction
)
from datetime import datetime, timedelta
import random

# Pakistani cities with airport codes
CITIES = {
    'Karachi (KHI)': {'code': 'KHI', 'name': 'Karachi'},
    'Lahore (LHE)': {'code': 'LHE', 'name': 'Lahore'},
    'Islamabad (ISB)': {'code': 'ISB', 'name': 'Islamabad'},
    'Peshawar (PEW)': {'code': 'PEW', 'name': 'Peshawar'},
    'Quetta (UET)': {'code': 'UET', 'name': 'Quetta'},
    'Multan (MUX)': {'code': 'MUX', 'name': 'Multan'},
    'Faisalabad (LYP)': {'code': 'LYP', 'name': 'Faisalabad'},
    'Sialkot (SKT)': {'code': 'SKT', 'name': 'Sialkot'},
}

# Flight durations between cities (in minutes)
FLIGHT_DURATIONS = {
    ('KHI', 'LHE'): 105, ('KHI', 'ISB'): 120, ('KHI', 'PEW'): 135, ('KHI', 'UET'): 90,
    ('KHI', 'MUX'): 75, ('KHI', 'LYP'): 95, ('KHI', 'SKT'): 125, ('LHE', 'ISB'): 75,
    ('LHE', 'PEW'): 90, ('LHE', 'UET'): 150, ('LHE', 'MUX'): 45, ('LHE', 'LYP'): 30,
    ('LHE', 'SKT'): 25, ('ISB', 'PEW'): 45, ('ISB', 'UET'): 180, ('ISB', 'MUX'): 90,
    ('ISB', 'LYP'): 75, ('ISB', 'SKT'): 60, ('PEW', 'UET'): 195, ('PEW', 'MUX'): 105,
    ('PEW', 'LYP'): 90, ('PEW', 'SKT'): 75, ('UET', 'MUX'): 120, ('UET', 'LYP'): 135,
    ('UET', 'SKT'): 165, ('MUX', 'LYP'): 35, ('MUX', 'SKT'): 55, ('LYP', 'SKT'): 45,
}

def get_flight_duration(origin_code, dest_code):
    """Get flight duration between two cities."""
    key = (origin_code, dest_code)
    reverse_key = (dest_code, origin_code)
    
    if key in FLIGHT_DURATIONS:
        minutes = FLIGHT_DURATIONS[key]
    elif reverse_key in FLIGHT_DURATIONS:
        minutes = FLIGHT_DURATIONS[reverse_key]
    else:
        minutes = 90  # Default 1.5 hours
    
    hours = minutes // 60
    mins = minutes % 60
    
    if hours > 0 and mins > 0:
        return f"{hours}h {mins}m"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{mins}m"

def clean_database():
    """Clean and recreate database."""
    print("🧹 Cleaning database...")
    db.drop_all()
    db.create_all()
    print("✅ Database cleaned and recreated")

def create_admin():
    """Create admin user with specified credentials."""
    print("👨‍💼 Creating admin user...")
    
    admin_user = User(
        first_name='Hussain',
        last_name='Admin',
        phone_number='03000000000',
        email='hussain@skystream.com',
        age=30,
        password=bcrypt.generate_password_hash('hussain9887').decode('utf-8'),
        role='admin'
    )
    
    db.session.add(admin_user)
    db.session.commit()
    print("✅ Admin user created - hussain@skystream.com / hussain9887")
    return admin_user

def create_planes():
    """Create aircraft fleet."""
    print("✈️ Creating aircraft fleet...")
    
    planes_data = [
        ('SKY-001', 'Boeing 737-800', 189, 'Karachi (KHI)'),
        ('SKY-002', 'Boeing 737-800', 189, 'Lahore (LHE)'),
        ('SKY-003', 'Airbus A320neo', 165, 'Islamabad (ISB)'),
        ('SKY-004', 'Boeing 777-300ER', 396, 'Karachi (KHI)'),
        ('SKY-005', 'Airbus A321neo', 220, 'Lahore (LHE)'),
        ('SKY-006', 'ATR 72-600', 78, 'Peshawar (PEW)'),
        ('SKY-007', 'Embraer E190', 114, 'Multan (MUX)'),
        ('SKY-008', 'ATR 72-600', 78, 'Quetta (UET)'),
    ]
    
    planes = []
    for plane_id, model, capacity, airport in planes_data:
        plane = Plane(
            plane_id=plane_id,
            model=model,
            capacity=capacity,
            current_airport=airport,
            status='on_ground'
        )
        planes.append(plane)
    
    db.session.add_all(planes)
    db.session.commit()
    print(f"✅ Created {len(planes)} aircraft")
    return planes

def create_staff():
    """Create 8 staff members."""
    print("👥 Creating 8 staff members...")
    
    hashed_pw = bcrypt.generate_password_hash('skystream2024').decode('utf-8')
    
    staff_data = [
        ('Captain', 'Ahmed', 'Rashid', '03001234501', 'ahmed.rashid@skystream.com', 45, 'STF-2001', 'Pilot', 120000),
        ('Captain', 'Fatima', 'Malik', '03001234502', 'fatima.malik@skystream.com', 42, 'STF-2002', 'Pilot', 118000),
        ('First Officer', 'Hassan', 'Ali', '03001234503', 'hassan.ali@skystream.com', 32, 'STF-2003', 'Co-Pilot', 85000),
        ('First Officer', 'Zara', 'Ahmed', '03001234504', 'zara.ahmed@skystream.com', 29, 'STF-2004', 'Co-Pilot', 82000),
        ('Purser', 'Ayesha', 'Nawaz', '03001234505', 'ayesha.nawaz@skystream.com', 34, 'STF-2005', 'Purser', 65000),
        ('Flight Attendant', 'Saira', 'Javed', '03001234506', 'saira.javed@skystream.com', 26, 'STF-2006', 'Cabin Crew', 45000),
        ('Engineer', 'Tariq', 'Rahman', '03001234507', 'tariq.rahman@skystream.com', 44, 'STF-2007', 'Flight Engineer', 95000),
        ('Ground Operations', 'Shahid', 'Mahmood', '03001234508', 'shahid.mahmood@skystream.com', 37, 'STF-2008', 'Ground Operations', 55000),
    ]
    
    staff_users = []
    staff_profiles = []
    
    for title, first_name, last_name, phone, email, age, staff_id, role, salary in staff_data:
        user = User(
            first_name=first_name,
            last_name=last_name,
            phone_number=phone,
            email=email,
            age=age,
            password=hashed_pw,
            role='staff',
            staff_id=staff_id
        )
        staff_users.append(user)
    
    db.session.add_all(staff_users)
    db.session.commit()
    
    # Create staff profiles
    for i, (title, first_name, last_name, phone, email, age, staff_id, role, salary) in enumerate(staff_data):
        profile = StaffProfile(
            user_id=staff_users[i].id,
            role=role,
            salary=salary,
            completed_duties=random.randint(10, 50),
            feedback_rating=round(random.uniform(4.2, 5.0), 1),
            reward_points=random.randint(500, 2000)
        )
        staff_profiles.append(profile)
    
    db.session.add_all(staff_profiles)
    db.session.commit()
    
    print(f"✅ Created {len(staff_users)} staff members")
    return staff_users, staff_profiles

def create_7_day_flights(planes):
    """Create flights between all cities for next 7 days."""
    print("🗓️ Creating 7-day flight schedule...")
    
    base_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    flights = []
    city_list = list(CITIES.keys())
    
    # Flight times throughout the day
    flight_times = [6, 9, 12, 15, 18, 21]
    
    for day in range(7):
        current_date = base_date + timedelta(days=day)
        print(f"  📅 Creating flights for day {day + 1}/7")
        
        # Create flights between all city pairs
        for origin in city_list:
            for destination in city_list:
                if origin == destination:
                    continue
                
                origin_code = CITIES[origin]['code']
                dest_code = CITIES[destination]['code']
                
                # Major routes get 2 flights per day, others get 1
                if (origin_code, dest_code) in [('KHI', 'LHE'), ('LHE', 'KHI'), 
                                               ('LHE', 'ISB'), ('ISB', 'LHE'),
                                               ('ISB', 'KHI'), ('KHI', 'ISB')]:
                    flights_per_day = 2
                else:
                    flights_per_day = 1
                
                for flight_num in range(flights_per_day):
                    # Select appropriate plane
                    selected_plane = random.choice(planes)
                    
                    # Assign flight time
                    base_hour = flight_times[flight_num % len(flight_times)]
                    flight_time = current_date.replace(
                        hour=base_hour,
                        minute=random.choice([0, 15, 30, 45]),
                        second=0
                    )
                    
                    flight = Flight(
                        plane_id=selected_plane.id,
                        origin=origin,
                        destination=destination,
                        duration=get_flight_duration(origin_code, dest_code),
                        departure_time=flight_time,
                        status=random.choice(['on_time', 'on_time', 'on_time', 'delayed'])
                    )
                    flights.append(flight)
    
    # Batch insert flights
    db.session.add_all(flights)
    db.session.commit()
    
    # Generate seats for all flights
    print("💺 Generating seats for all flights...")
    for flight in flights:
        Seat.generate_for_flight(flight.id)
    
    print(f"✅ Created {len(flights)} flights over 7 days")
    return flights

def create_sample_customers():
    """Create a few sample customers."""
    print("👤 Creating sample customers...")
    
    customers_data = [
        ('Sarah', 'Mitchell', '03111234567', 'sarah.mitchell@example.com', 31, 'customer123'),
        ('Ali', 'Hassan', '03221234567', 'ali.hassan@example.com', 28, 'password123'),
        ('Maria', 'Rodriguez', '03331234567', 'maria.rodriguez@example.com', 35, 'password123'),
    ]
    
    customers = []
    for first, last, phone, email, age, password in customers_data:
        user = User(
            first_name=first,
            last_name=last,
            phone_number=phone,
            email=email,
            age=age,
            password=bcrypt.generate_password_hash(password).decode('utf-8'),
            role='customer'
        )
        customers.append(user)
    
    db.session.add_all(customers)
    db.session.commit()
    
    print(f"✅ Created {len(customers)} sample customers")
    return customers

def quick_seed():
    """Main seeding function."""
    print("🚀 Starting Quick Database Setup for SkyStream Airlines")
    print("=" * 60)
    
    with app.app_context():
        # Step 1: Clean database
        clean_database()
        
        # Step 2: Create admin user
        admin = create_admin()
        
        # Step 3: Create aircraft fleet
        planes = create_planes()
        
        # Step 4: Create 8 staff members
        staff_users, staff_profiles = create_staff()
        
        # Step 5: Create 7-day flight schedule
        flights = create_7_day_flights(planes)
        
        # Step 6: Create sample customers
        customers = create_sample_customers()
        
        print("\n" + "=" * 60)
        print("🎉 QUICK DATABASE SETUP COMPLETED!")
        print("=" * 60)
        print("\n📊 SUMMARY:")
        print(f"   ✈️  Aircraft Fleet: {len(planes)} planes")
        print(f"   🗓️  Flight Schedule: {len(flights)} flights over 7 days")
        print(f"   👥  Staff Members: {len(staff_users)} employees")
        print(f"   👤  Sample Customers: {len(customers)} users")
        print(f"   🎫  Full connectivity between all {len(CITIES)} Pakistani cities")
        
        print("\n🔐 LOGIN CREDENTIALS:")
        print("   👨‍💼 ADMIN:")
        print("      Email: hussain@skystream.com")
        print("      Password: hussain9887")
        print("\n   👨‍✈️ STAFF (All 8 staff members):")
        print("      Password: skystream2024")
        print("      Staff IDs: STF-2001 to STF-2008")
        print("\n   👤 SAMPLE CUSTOMERS:")
        print("      Email: sarah.mitchell@example.com | Password: customer123")
        print("      Email: ali.hassan@example.com | Password: password123")
        print("      Email: maria.rodriguez@example.com | Password: password123")
        
        print("\n🌟 FEATURES:")
        print("   • 7-day flight schedule with full city connectivity")
        print("   • Realistic flight times and durations")
        print("   • 8 diverse staff members with Pakistani names")
        print("   • Multiple aircraft types")
        print("   • Clean database (no old entries)")
        
        print("\n" + "=" * 60)

if __name__ == '__main__':
    quick_seed()