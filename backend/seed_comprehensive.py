"""
Comprehensive seed script with 10 days of flights covering all major Pakistan routes
"""
from app import app, db, bcrypt
from models import User, StaffProfile, Flight, Roster, Plane
from datetime import datetime, timedelta

def seed_database():
    with app.app_context():
        # Drop and recreate all tables
        from sqlalchemy import text as _text
        with db.engine.connect() as conn:
            conn.execute(_text("""
                DROP TABLE IF EXISTS
                    ticket, passenger, booking, roster, staff_profile,
                    seat, flight, plane, "user"
                CASCADE
            """))
            conn.commit()
        db.create_all()

        print("🔄 Creating comprehensive database...")

        # ----------------------------------------------------------------
        # 1. Create Planes (8 aircraft for better coverage)
        # ----------------------------------------------------------------
        planes_data = [
            ('SKY-001', 'Boeing 737-800', 189, 'Karachi (KHI)'),
            ('SKY-002', 'Airbus A320neo', 165, 'Lahore (LHE)'),
            ('SKY-003', 'Boeing 777-300ER', 396, 'Islamabad (ISB)'),
            ('SKY-004', 'ATR 72-600', 78, 'Peshawar (PEW)'),
            ('SKY-005', 'Boeing 777-200LR', 317, 'Multan (MUX)'),
            ('SKY-006', 'Airbus A321neo', 220, 'Karachi (KHI)'),
            ('SKY-007', 'Boeing 737-900', 215, 'Lahore (LHE)'),
            ('SKY-008', 'ATR 42-600', 50, 'Quetta (UET)'),
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

        # ----------------------------------------------------------------
        # 2. Create Comprehensive Flight Network (10 days)
        # ----------------------------------------------------------------
        base_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Define all major routes with durations
        routes = [
            ('Karachi (KHI)', 'Lahore (LHE)', '1h 45m'),
            ('Lahore (LHE)', 'Karachi (KHI)', '1h 45m'),
            ('Karachi (KHI)', 'Islamabad (ISB)', '2h 10m'),
            ('Islamabad (ISB)', 'Karachi (KHI)', '2h 10m'),
            ('Karachi (KHI)', 'Peshawar (PEW)', '2h 30m'),
            ('Peshawar (PEW)', 'Karachi (KHI)', '2h 30m'),
            ('Karachi (KHI)', 'Multan (MUX)', '1h 30m'),
            ('Multan (MUX)', 'Karachi (KHI)', '1h 30m'),
            ('Karachi (KHI)', 'Quetta (UET)', '1h 50m'),
            ('Quetta (UET)', 'Karachi (KHI)', '1h 50m'),
            ('Lahore (LHE)', 'Islamabad (ISB)', '1h 15m'),
            ('Islamabad (ISB)', 'Lahore (LHE)', '1h 15m'),
            ('Lahore (LHE)', 'Peshawar (PEW)', '1h 30m'),
            ('Peshawar (PEW)', 'Lahore (LHE)', '1h 30m'),
            ('Lahore (LHE)', 'Multan (MUX)', '1h 10m'),
            ('Multan (MUX)', 'Lahore (LHE)', '1h 10m'),
            ('Islamabad (ISB)', 'Peshawar (PEW)', '1h 05m'),
            ('Peshawar (PEW)', 'Islamabad (ISB)', '1h 05m'),
            ('Islamabad (ISB)', 'Multan (MUX)', '1h 25m'),
            ('Multan (MUX)', 'Islamabad (ISB)', '1h 25m'),
            ('Islamabad (ISB)', 'Quetta (UET)', '1h 45m'),
            ('Quetta (UET)', 'Islamabad (ISB)', '1h 45m'),
        ]
        
        flights = []
        flight_times = [6, 9, 12, 15, 18, 21]  # Multiple flights per day
        
        # Create flights for 10 days
        for day in range(10):
            for origin, destination, duration in routes:
                # 2-3 flights per route per day
                num_flights = 2 if len(routes) > 15 else 3
                for flight_idx in range(num_flights):
                    hour = flight_times[flight_idx % len(flight_times)]
                    minute = (flight_idx * 15) % 60
                    
                    departure = base_date + timedelta(days=day, hours=hour, minutes=minute)
                    
                    # Assign plane based on route
                    plane = planes[hash(f"{origin}{destination}{day}{flight_idx}") % len(planes)]
                    
                    flight = Flight(
                        plane_id=plane.id,
                        origin=origin,
                        destination=destination,
                        duration=duration,
                        departure_time=departure,
                        status='on_time'
                    )
                    flights.append(flight)
        
        db.session.add_all(flights)
        db.session.commit()
        print(f"✅ Created {len(flights)} flights across 10 days")

        # ----------------------------------------------------------------
        # 3. Create Staff Users
        # ----------------------------------------------------------------
        hashed_pw = bcrypt.generate_password_hash('password123').decode('utf-8')

        staff_data = [
            ('James', 'Carter', '03001234567', 'james.carter@skystream.com', 35, 'STF-1001'),
            ('Aisha', 'Rahman', '03009876543', 'aisha.rahman@skystream.com', 29, 'STF-1002'),
            ('Omar', 'Farooq', '03111122233', 'omar.farooq@skystream.com', 42, 'STF-1003'),
            ('Sana', 'Malik', '03214455667', 'sana.malik@skystream.com', 31, 'STF-1004'),
            ('Bilal', 'Ahmed', '03335566778', 'bilal.ahmed@skystream.com', 38, 'STF-1005'),
            ('Fatima', 'Siddiqui', '03446677889', 'fatima.siddiqui@skystream.com', 26, 'STF-1006'),
            ('Tariq', 'Hussain', '03557788990', 'tariq.hussain@skystream.com', 45, 'STF-1007'),
            ('Mariam', 'Khan', '03668899001', 'mariam.khan@skystream.com', 33, 'STF-1008'),
        ]
        
        staff_users = []
        for fn, ln, ph, em, ag, sid in staff_data:
            u = User(first_name=fn, last_name=ln, phone_number=ph,
                     email=em, age=ag, password=hashed_pw,
                     role='staff', staff_id=sid)
            staff_users.append(u)
        
        db.session.add_all(staff_users)
        db.session.commit()
        print(f"✅ Created {len(staff_users)} staff members")

        # ----------------------------------------------------------------
        # 4. Create Staff Profiles
        # ----------------------------------------------------------------
        profile_data = [
            (0, 'Pilot', 95000.0, 48, 4.9, 2400),
            (1, 'Cabin Crew', 42000.0, 22, 4.7, 890),
            (2, 'Co-Pilot', 78000.0, 35, 4.8, 1750),
            (3, 'Purser', 55000.0, 30, 4.6, 1200),
            (4, 'Engineer', 88000.0, 41, 4.5, 2100),
            (5, 'Cabin Crew', 40000.0, 18, 4.8, 740),
            (6, 'Pilot', 97000.0, 52, 5.0, 3100),
            (7, 'Co-Pilot', 76000.0, 27, 4.7, 1350),
        ]
        
        profiles = []
        for idx, role, salary, duties, rating, pts in profile_data:
            p = StaffProfile(user_id=staff_users[idx].id, role=role,
                             salary=salary, completed_duties=duties,
                             feedback_rating=rating, reward_points=pts)
            profiles.append(p)
        
        db.session.add_all(profiles)
        db.session.commit()
        print(f"✅ Created {len(profiles)} staff profiles")

        # ----------------------------------------------------------------
        # 5. Create Admin User
        # ----------------------------------------------------------------
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
        print("✅ Created admin user")

        # ----------------------------------------------------------------
        # 6. Create Sample Customer
        # ----------------------------------------------------------------
        customer = User(
            first_name='Sarah',
            last_name='Mitchell',
            phone_number='05551234567',
            email='sarah.mitchell@example.com',
            age=31,
            password=bcrypt.generate_password_hash('customer123').decode('utf-8'),
            role='customer'
        )
        db.session.add(customer)
        db.session.commit()
        print("✅ Created sample customer")

        # ----------------------------------------------------------------
        # 7. Assign Staff to Sample Rosters
        # ----------------------------------------------------------------
        hotels = [
            'Pearl Continental Hotel Lahore',
            'Marriott Hotel Islamabad',
            'Karachi Marriott Hotel',
            'Serena Hotel Islamabad',
            'PC Hotel Karachi',
            'Avari Hotel Lahore',
            'Ramada Hotel Peshawar',
            'Shelton Hotel Islamabad',
        ]
        
        rosters = []
        sample_flights = Flight.query.limit(8).all()
        for i, profile in enumerate(profiles):
            if i < len(sample_flights):
                rosters.append(Roster(
                    staff_profile_id=profile.id,
                    flight_id=sample_flights[i].id,
                    hotel=hotels[i],
                    travel_id=f'TRV-{9900+i+1}-{chr(65+i)}',
                ))
        
        db.session.add_all(rosters)
        db.session.commit()
        print(f"✅ Created {len(rosters)} roster assignments")

        print("\n" + "="*60)
        print("✅ DATABASE SEEDED SUCCESSFULLY!")
        print("="*60)
        print(f"  📊 Total Flights: {len(flights)} (10 days coverage)")
        print(f"  ✈️  Total Aircraft: {len(planes)}")
        print(f"  👥 Staff Members: {len(staff_users)}")
        print("="*60)
        print("  🔐 LOGIN CREDENTIALS:")
        print("  Admin    → Email: hussain@skystream.com | PW: hussain9887")
        print("  Staff    → IDs: STF-1001 to STF-1008 | PW: password123")
        print("  Customer → Email: sarah.mitchell@example.com | PW: customer123")
        print("="*60)

if __name__ == '__main__':
    seed_database()
