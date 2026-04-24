#!/usr/bin/env python3
"""
Comprehensive Database Seeding Script for SkyStream Airlines
============================================================

This script creates a complete 30-day flight schedule with:
- Full connectivity between all Pakistani cities
- Realistic flight times and schedules
- Comprehensive staff roster
- Clean database without manual entries

Usage: python comprehensive_seed.py
"""

from app import app, db, bcrypt
from models import (
    User, StaffProfile, Flight, Roster, Plane, Seat,
    Booking, Passenger, Ticket, SeatLock, PaymentTransaction
)
from datetime import datetime, timedelta
import random

# Pakistani cities with airport codes and realistic flight durations
CITIES = {
    'Karachi (KHI)': {'code': 'KHI', 'name': 'Karachi'},
    'Lahore (LHE)': {'code': 'LHE', 'name': 'Lahore'},
    'Islamabad (ISB)': {'code': 'ISB', 'name': 'Islamabad'},
    'Peshawar (PEW)': {'code': 'PEW', 'name': 'Peshawar'},
    'Quetta (UET)': {'code': 'UET', 'name': 'Quetta'},
    'Multan (MUX)': {'code': 'MUX', 'name': 'Multan'},
    'Faisalabad (LYP)': {'code': 'LYP', 'name': 'Faisalabad'},
    'Sialkot (SKT)': {'code': 'SKT', 'name': 'Sialkot'},
    'Rahim Yar Khan (RYK)': {'code': 'RYK', 'name': 'Rahim Yar Khan'},
    'Sukkur (SKZ)': {'code': 'SKZ', 'name': 'Sukkur'},
}

# Flight durations between cities (in minutes)
FLIGHT_DURATIONS = {
    ('KHI', 'LHE'): 105,  # 1h 45m
    ('KHI', 'ISB'): 120,  # 2h
    ('KHI', 'PEW'): 135,  # 2h 15m
    ('KHI', 'UET'): 90,   # 1h 30m
    ('KHI', 'MUX'): 75,   # 1h 15m
    ('KHI', 'LYP'): 95,   # 1h 35m
    ('KHI', 'SKT'): 125,  # 2h 5m
    ('KHI', 'RYK'): 65,   # 1h 5m
    ('KHI', 'SKZ'): 55,   # 55m
    ('LHE', 'ISB'): 75,   # 1h 15m
    ('LHE', 'PEW'): 90,   # 1h 30m
    ('LHE', 'UET'): 150,  # 2h 30m
    ('LHE', 'MUX'): 45,   # 45m
    ('LHE', 'LYP'): 30,   # 30m
    ('LHE', 'SKT'): 25,   # 25m
    ('LHE', 'RYK'): 85,   # 1h 25m
    ('LHE', 'SKZ'): 110,  # 1h 50m
    ('ISB', 'PEW'): 45,   # 45m
    ('ISB', 'UET'): 180,  # 3h
    ('ISB', 'MUX'): 90,   # 1h 30m
    ('ISB', 'LYP'): 75,   # 1h 15m
    ('ISB', 'SKT'): 60,   # 1h
    ('ISB', 'RYK'): 120,  # 2h
    ('ISB', 'SKZ'): 135,  # 2h 15m
    ('PEW', 'UET'): 195,  # 3h 15m
    ('PEW', 'MUX'): 105,  # 1h 45m
    ('PEW', 'LYP'): 90,   # 1h 30m
    ('PEW', 'SKT'): 75,   # 1h 15m
    ('PEW', 'RYK'): 150,  # 2h 30m
    ('PEW', 'SKZ'): 165,  # 2h 45m
    ('UET', 'MUX'): 120,  # 2h
    ('UET', 'LYP'): 135,  # 2h 15m
    ('UET', 'SKT'): 165,  # 2h 45m
    ('UET', 'RYK'): 105,  # 1h 45m
    ('UET', 'SKZ'): 90,   # 1h 30m
    ('MUX', 'LYP'): 35,   # 35m
    ('MUX', 'SKT'): 55,   # 55m
    ('MUX', 'RYK'): 40,   # 40m
    ('MUX', 'SKZ'): 75,   # 1h 15m
    ('LYP', 'SKT'): 45,   # 45m
    ('LYP', 'RYK'): 70,   # 1h 10m
    ('LYP', 'SKZ'): 95,   # 1h 35m
    ('SKT', 'RYK'): 85,   # 1h 25m
    ('SKT', 'SKZ'): 120,  # 2h
    ('RYK', 'SKZ'): 45,   # 45m
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
        # Fallback for any missing routes
        minutes = 90
    
    hours = minutes // 60
    mins = minutes % 60
    
    if hours > 0 and mins > 0:
        return f"{hours}h {mins}m"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{mins}m"

def clean_database():
    """Clean the database and remove all existing data."""
    print("🧹 Cleaning database...")
    
    with app.app_context():
        # Drop all tables in correct order to avoid foreign key constraints
        db.drop_all()
        db.create_all()
        print("✅ Database cleaned and recreated")

def create_planes():
    """Create a fleet of planes for SkyStream Airlines."""
    print("✈️ Creating aircraft fleet...")
    
    planes_data = [
        # Boeing Fleet
        ('SKY-001', 'Boeing 737-800', 189, 'Karachi (KHI)'),
        ('SKY-002', 'Boeing 737-800', 189, 'Lahore (LHE)'),
        ('SKY-003', 'Boeing 737-MAX 8', 178, 'Islamabad (ISB)'),
        ('SKY-004', 'Boeing 777-300ER', 396, 'Karachi (KHI)'),
        ('SKY-005', 'Boeing 777-200LR', 317, 'Lahore (LHE)'),
        
        # Airbus Fleet
        ('SKY-006', 'Airbus A320neo', 165, 'Islamabad (ISB)'),
        ('SKY-007', 'Airbus A321neo', 220, 'Peshawar (PEW)'),
        ('SKY-008', 'Airbus A330-300', 335, 'Karachi (KHI)'),
        ('SKY-009', 'Airbus A350-900', 325, 'Lahore (LHE)'),
        
        # Regional Fleet
        ('SKY-010', 'ATR 72-600', 78, 'Quetta (UET)'),
        ('SKY-011', 'ATR 72-600', 78, 'Multan (MUX)'),
        ('SKY-012', 'Embraer E190', 114, 'Faisalabad (LYP)'),
        ('SKY-013', 'Embraer E175', 88, 'Sialkot (SKT)'),
        ('SKY-014', 'Bombardier Q400', 86, 'Sukkur (SKZ)'),
        ('SKY-015', 'ATR 42-600', 50, 'Rahim Yar Khan (RYK)'),
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

def create_comprehensive_flights(planes):
    """Create 30 days of flights ensuring connectivity between all cities."""
    print("🗓️ Creating 30-day comprehensive flight schedule...")
    
    base_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    flights = []
    city_list = list(CITIES.keys())
    
    # Flight times throughout the day
    flight_times = [6, 8, 10, 12, 14, 16, 18, 20]
    
    for day in range(30):
        current_date = base_date + timedelta(days=day)
        daily_flights = []
        
        # Ensure every city has flights to every other city at least once per week
        for origin in city_list:
            for destination in city_list:
                if origin == destination:
                    continue
                
                origin_code = CITIES[origin]['code']
                dest_code = CITIES[destination]['code']
                
                # Major routes (KHI-LHE, LHE-ISB, ISB-KHI) get multiple daily flights
                if (origin_code, dest_code) in [('KHI', 'LHE'), ('LHE', 'KHI'), 
                                               ('LHE', 'ISB'), ('ISB', 'LHE'),
                                               ('ISB', 'KHI'), ('KHI', 'ISB')]:
                    flights_per_day = 3
                # Secondary routes get 1-2 flights per day
                elif origin_code in ['KHI', 'LHE', 'ISB'] or dest_code in ['KHI', 'LHE', 'ISB']:
                    flights_per_day = 2 if day % 2 == 0 else 1
                # Regional routes get flights every 2-3 days
                else:
                    flights_per_day = 1 if day % 3 == 0 else 0
                
                for flight_num in range(flights_per_day):
                    # Select appropriate plane based on route popularity
                    if (origin_code, dest_code) in [('KHI', 'LHE'), ('LHE', 'KHI')]:
                        # Major routes get larger planes
                        suitable_planes = [p for p in planes if p.capacity >= 165]
                    elif origin_code in ['UET', 'RYK', 'SKZ'] or dest_code in ['UET', 'RYK', 'SKZ']:
                        # Regional routes get smaller planes
                        suitable_planes = [p for p in planes if p.capacity <= 114]
                    else:
                        # Medium routes get medium planes
                        suitable_planes = [p for p in planes if 114 <= p.capacity <= 220]
                    
                    if not suitable_planes:
                        suitable_planes = planes  # Fallback to any plane
                    
                    selected_plane = random.choice(suitable_planes)
                    
                    # Assign flight time
                    base_hour = flight_times[flight_num % len(flight_times)]
                    flight_time = current_date.replace(
                        hour=base_hour,
                        minute=random.choice([0, 15, 30, 45]),
                        second=0
                    )
                    
                    # Add some randomness to avoid exact same times
                    flight_time += timedelta(minutes=random.randint(-15, 15))
                    
                    flight = Flight(
                        plane_id=selected_plane.id,
                        origin=origin,
                        destination=destination,
                        duration=get_flight_duration(origin_code, dest_code),
                        departure_time=flight_time,
                        status=random.choice(['on_time', 'on_time', 'on_time', 'delayed'])  # 75% on time
                    )
                    daily_flights.append(flight)
        
        flights.extend(daily_flights)
        if day % 5 == 0:
            print(f"  📅 Generated flights for day {day + 1}/30")
    
    # Batch insert flights
    db.session.add_all(flights)
    db.session.commit()
    
    # Generate seats for all flights
    print("💺 Generating seats for all flights...")
    for flight in flights:
        Seat.generate_for_flight(flight.id)
    
    print(f"✅ Created {len(flights)} flights over 30 days")
    return flights

def create_comprehensive_staff():
    """Create a diverse and comprehensive staff roster."""
    print("👥 Creating comprehensive staff roster...")
    
    hashed_pw = bcrypt.generate_password_hash('skystream2024').decode('utf-8')
    
    # Comprehensive staff data with Pakistani names and diverse roles
    staff_data = [
        # Pilots
        ('Captain', 'Ahmed', 'Rashid', '03001234501', 'ahmed.rashid@skystream.com', 45, 'STF-2001', 'Pilot', 120000),
        ('Captain', 'Fatima', 'Malik', '03001234502', 'fatima.malik@skystream.com', 42, 'STF-2002', 'Pilot', 118000),
        ('Captain', 'Omar', 'Khan', '03001234503', 'omar.khan@skystream.com', 48, 'STF-2003', 'Pilot', 125000),
        ('Captain', 'Aisha', 'Siddiqui', '03001234504', 'aisha.siddiqui@skystream.com', 39, 'STF-2004', 'Pilot', 115000),
        
        # Co-Pilots
        ('First Officer', 'Hassan', 'Ali', '03001234505', 'hassan.ali@skystream.com', 32, 'STF-2005', 'Co-Pilot', 85000),
        ('First Officer', 'Zara', 'Ahmed', '03001234506', 'zara.ahmed@skystream.com', 29, 'STF-2006', 'Co-Pilot', 82000),
        ('First Officer', 'Bilal', 'Hussain', '03001234507', 'bilal.hussain@skystream.com', 35, 'STF-2007', 'Co-Pilot', 88000),
        ('First Officer', 'Mariam', 'Farooq', '03001234508', 'mariam.farooq@skystream.com', 31, 'STF-2008', 'Co-Pilot', 84000),
        
        # Flight Engineers
        ('Engineer', 'Tariq', 'Rahman', '03001234509', 'tariq.rahman@skystream.com', 44, 'STF-2009', 'Flight Engineer', 95000),
        ('Engineer', 'Sana', 'Qureshi', '03001234510', 'sana.qureshi@skystream.com', 38, 'STF-2010', 'Flight Engineer', 92000),
        ('Engineer', 'Imran', 'Sheikh', '03001234511', 'imran.sheikh@skystream.com', 41, 'STF-2011', 'Flight Engineer', 97000),
        
        # Cabin Crew - Pursers
        ('Purser', 'Ayesha', 'Nawaz', '03001234512', 'ayesha.nawaz@skystream.com', 34, 'STF-2012', 'Purser', 65000),
        ('Purser', 'Kamran', 'Iqbal', '03001234513', 'kamran.iqbal@skystream.com', 36, 'STF-2013', 'Purser', 67000),
        ('Purser', 'Nadia', 'Butt', '03001234514', 'nadia.butt@skystream.com', 33, 'STF-2014', 'Purser', 64000),
        
        # Cabin Crew - Flight Attendants
        ('Flight Attendant', 'Saira', 'Javed', '03001234515', 'saira.javed@skystream.com', 26, 'STF-2015', 'Cabin Crew', 45000),
        ('Flight Attendant', 'Usman', 'Chaudhry', '03001234516', 'usman.chaudhry@skystream.com', 28, 'STF-2016', 'Cabin Crew', 47000),
        ('Flight Attendant', 'Hina', 'Saleem', '03001234517', 'hina.saleem@skystream.com', 25, 'STF-2017', 'Cabin Crew', 44000),
        ('Flight Attendant', 'Adnan', 'Mirza', '03001234518', 'adnan.mirza@skystream.com', 30, 'STF-2018', 'Cabin Crew', 48000),
        ('Flight Attendant', 'Rabia', 'Khattak', '03001234519', 'rabia.khattak@skystream.com', 27, 'STF-2019', 'Cabin Crew', 46000),
        ('Flight Attendant', 'Faisal', 'Baig', '03001234520', 'faisal.baig@skystream.com', 29, 'STF-2020', 'Cabin Crew', 47500),
        
        # Ground Staff
        ('Ground Operations', 'Shahid', 'Mahmood', '03001234521', 'shahid.mahmood@skystream.com', 37, 'STF-2021', 'Ground Operations', 55000),
        ('Ground Operations', 'Rubina', 'Ashraf', '03001234522', 'rubina.ashraf@skystream.com', 32, 'STF-2022', 'Ground Operations', 53000),
        ('Ground Operations', 'Nasir', 'Gondal', '03001234523', 'nasir.gondal@skystream.com', 40, 'STF-2023', 'Ground Operations', 57000),
        
        # Maintenance Crew
        ('Maintenance', 'Rasheed', 'Ahmad', '03001234524', 'rasheed.ahmad@skystream.com', 43, 'STF-2024', 'Aircraft Mechanic', 75000),
        ('Maintenance', 'Samina', 'Riaz', '03001234525', 'samina.riaz@skystream.com', 35, 'STF-2025', 'Avionics Technician', 72000),
        ('Maintenance', 'Javaid', 'Akhtar', '03001234526', 'javaid.akhtar@skystream.com', 39, 'STF-2026', 'Aircraft Mechanic', 74000),
        
        # Customer Service
        ('Customer Service', 'Farah', 'Noor', '03001234527', 'farah.noor@skystream.com', 28, 'STF-2027', 'Customer Service', 42000),
        ('Customer Service', 'Waseem', 'Akram', '03001234528', 'waseem.akram@skystream.com', 31, 'STF-2028', 'Customer Service', 44000),
        ('Customer Service', 'Shazia', 'Pervez', '03001234529', 'shazia.pervez@skystream.com', 29, 'STF-2029', 'Customer Service', 43000),
        
        # Security
        ('Security', 'Mushtaq', 'Gill', '03001234530', 'mushtaq.gill@skystream.com', 36, 'STF-2030', 'Security Officer', 50000),
        ('Security', 'Nasreen', 'Bibi', '03001234531', 'nasreen.bibi@skystream.com', 33, 'STF-2031', 'Security Officer', 49000),
    ]
    
    staff_users = []
    staff_profiles = []
    
    for title, first_name, last_name, phone, email, age, staff_id, role, salary in staff_data:
        # Create user
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
    
    # Add all users first
    db.session.add_all(staff_users)
    db.session.commit()
    
    # Create staff profiles
    for i, (title, first_name, last_name, phone, email, age, staff_id, role, salary) in enumerate(staff_data):
        profile = StaffProfile(
            user_id=staff_users[i].id,
            role=role,
            salary=salary,
            completed_duties=random.randint(10, 100),
            feedback_rating=round(random.uniform(4.2, 5.0), 1),
            reward_points=random.randint(500, 3000)
        )
        staff_profiles.append(profile)
    
    db.session.add_all(staff_profiles)
    db.session.commit()
    
    print(f"✅ Created {len(staff_users)} staff members")
    return staff_users, staff_profiles

def create_admin_and_customers():
    """Create admin user and sample customers."""
    print("👤 Creating admin and sample customers...")
    
    # Admin user (keeping existing credentials)
    admin_user = User(
        first_name='Hussain',
        last_name='Admin',
        phone_number='03000000000',
        email='hussain@skystream.com',
        age=30,
        password=bcrypt.generate_password_hash('hussain9887').decode('utf-8'),
        role='admin'
    )
    
    # Sample customers
    customers_data = [
        ('Sarah', 'Mitchell', '03111234567', 'sarah.mitchell@example.com', 31, 'customer123'),
        ('Ali', 'Hassan', '03221234567', 'ali.hassan@example.com', 28, 'password123'),
        ('Maria', 'Rodriguez', '03331234567', 'maria.rodriguez@example.com', 35, 'password123'),
        ('Ahmed', 'Khan', '03441234567', 'ahmed.khan@example.com', 42, 'password123'),
        ('Fatima', 'Sheikh', '03551234567', 'fatima.sheikh@example.com', 29, 'password123'),
    ]
    
    users = [admin_user]
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
        users.append(user)
    
    db.session.add_all(users)
    db.session.commit()
    
    print(f"✅ Created admin and {len(customers_data)} sample customers")
    return users

def assign_staff_to_flights(staff_profiles, flights):
    """Assign staff to flights in a realistic roster pattern."""
    print("📋 Creating staff rosters...")
    
    # Hotels for different cities
    hotels_by_city = {
        'Karachi (KHI)': ['Pearl Continental Karachi', 'Marriott Hotel Karachi', 'Avari Towers Karachi'],
        'Lahore (LHE)': ['Pearl Continental Lahore', 'Marriott Hotel Lahore', 'Avari Hotel Lahore'],
        'Islamabad (ISB)': ['Serena Hotel Islamabad', 'Marriott Hotel Islamabad', 'Pearl Continental Rawalpindi'],
        'Peshawar (PEW)': ['Pearl Continental Peshawar', 'Ramada Hotel Peshawar', 'Shelton Hotel Peshawar'],
        'Quetta (UET)': ['Serena Hotel Quetta', 'Quetta Continental Hotel', 'Bloom Hotel Quetta'],
        'Multan (MUX)': ['Ramada Hotel Multan', 'Multan Continental Hotel', 'Hotel One Multan'],
        'Faisalabad (LYP)': ['Serena Hotel Faisalabad', 'Hotel One Faisalabad', 'Regent Plaza Faisalabad'],
        'Sialkot (SKT)': ['Sialkot Continental Hotel', 'Hotel Shelton Sialkot', 'Royal Hotel Sialkot'],
        'Rahim Yar Khan (RYK)': ['Hotel One RYK', 'Continental Hotel RYK', 'Royal Hotel RYK'],
        'Sukkur (SKZ)': ['Hotel One Sukkur', 'Sukkur Continental', 'Royal Hotel Sukkur'],
    }
    
    rosters = []
    flight_sample = random.sample(flights, min(len(flights), len(staff_profiles) * 3))
    
    for i, profile in enumerate(staff_profiles):
        # Assign 2-3 flights per staff member
        staff_flights = flight_sample[i*2:(i+1)*2+1] if i*2 < len(flight_sample) else []
        
        for j, flight in enumerate(staff_flights):
            destination_hotels = hotels_by_city.get(flight.destination, ['Hotel Continental'])
            
            roster = Roster(
                staff_profile_id=profile.id,
                flight_id=flight.id,
                hotel=random.choice(destination_hotels),
                travel_id=f'TRV-{2024}{str(i+1).zfill(3)}-{chr(65+j)}'
            )
            rosters.append(roster)
    
    db.session.add_all(rosters)
    db.session.commit()
    
    print(f"✅ Created {len(rosters)} staff roster assignments")

def comprehensive_seed():
    """Main seeding function that orchestrates the entire process."""
    print("🚀 Starting comprehensive database seeding for SkyStream Airlines")
    print("=" * 70)
    
    with app.app_context():
        # Step 1: Clean database
        clean_database()
        
        # Step 2: Create aircraft fleet
        planes = create_planes()
        
        # Step 3: Create comprehensive flight schedule
        flights = create_comprehensive_flights(planes)
        
        # Step 4: Create comprehensive staff
        staff_users, staff_profiles = create_comprehensive_staff()
        
        # Step 5: Create admin and customers
        users = create_admin_and_customers()
        
        # Step 6: Assign staff to flights
        assign_staff_to_flights(staff_profiles, flights)
        
        print("\n" + "=" * 70)
        print("🎉 COMPREHENSIVE DATABASE SEEDING COMPLETED!")
        print("=" * 70)
        print("\n📊 SUMMARY:")
        print(f"   ✈️  Aircraft Fleet: {len(planes)} planes")
        print(f"   🗓️  Flight Schedule: {len(flights)} flights over 30 days")
        print(f"   👥  Staff Members: {len(staff_users)} employees")
        print(f"   🎫  Full connectivity between all {len(CITIES)} Pakistani cities")
        print(f"   💺  Seats generated for all flights")
        
        print("\n🔐 LOGIN CREDENTIALS:")
        print("   👨‍💼 ADMIN:")
        print("      Email: hussain@skystream.com")
        print("      Password: hussain9887")
        print("\n   👨‍✈️ STAFF (All staff members):")
        print("      Password: skystream2024")
        print("      Staff IDs: STF-2001 to STF-2031")
        print("\n   👤 SAMPLE CUSTOMERS:")
        print("      Email: sarah.mitchell@example.com | Password: customer123")
        print("      Email: ali.hassan@example.com | Password: password123")
        print("      (+ 3 more sample customers)")
        
        print("\n🌟 FEATURES:")
        print("   • 30-day comprehensive flight schedule")
        print("   • Full city-to-city connectivity")
        print("   • Realistic flight times and durations")
        print("   • Diverse staff roster with Pakistani names")
        print("   • Multiple aircraft types for different routes")
        print("   • Clean database (no manual entries)")
        
        print("\n" + "=" * 70)

if __name__ == '__main__':
    comprehensive_seed()