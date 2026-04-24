from app import app, db, bcrypt
from models import User, StaffProfile, Flight, Roster, Plane
from datetime import datetime, timedelta

def seed_database():
    with app.app_context():
        # Drop and recreate all tables (fresh seed) — use CASCADE for PostgreSQL FK constraints
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

        # ----------------------------------------------------------------
        # 1. Create Planes
        # ----------------------------------------------------------------
        plane1 = Plane(
            plane_id='SKY-001',
            model='Boeing 737-800',
            capacity=189,
            current_airport='Karachi (KHI)',
            status='on_ground'
        )
        plane2 = Plane(
            plane_id='SKY-002',
            model='Airbus A320neo',
            capacity=165,
            current_airport='Lahore (LHE)',
            status='on_ground'
        )
        plane3 = Plane(
            plane_id='SKY-003',
            model='Boeing 777-300ER',
            capacity=396,
            current_airport='Islamabad (ISB)',
            status='on_ground'
        )
        plane4 = Plane(
            plane_id='SKY-004',
            model='ATR 72-600',
            capacity=78,
            current_airport='Karachi (KHI)',
            status='on_ground'
        )
        plane5 = Plane(
            plane_id='SKY-005',
            model='Boeing 777-200LR',
            capacity=317,
            current_airport='Lahore (LHE)',
            status='on_ground'
        )
        db.session.add_all([plane1, plane2, plane3, plane4, plane5])
        db.session.commit()

        # ----------------------------------------------------------------
        # 2. Create Flights (assigned to planes) - Pakistan routes with multiple flights per date
        # ----------------------------------------------------------------
        base_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Karachi to Lahore flights - 5 flights on different dates/times
        flights = []
        for i in range(5):
            flights.append(Flight(
                plane_id=[plane1.id, plane4.id][i % 2],
                origin='Karachi (KHI)',
                destination='Lahore (LHE)',
                duration='1h 45m',
                departure_time=base_date + timedelta(days=i, hours=6 + i*2),
                status='on_time'
            ))
        
        # Lahore to Islamabad flights - 5 flights on different dates/times
        for i in range(5):
            flights.append(Flight(
                plane_id=[plane2.id, plane5.id][i % 2],
                origin='Lahore (LHE)',
                destination='Islamabad (ISB)',
                duration='1h 15m',
                departure_time=base_date + timedelta(days=i, hours=8 + i*2),
                status='on_time'
            ))
        
        # Islamabad to Karachi flights - 5 flights on different dates/times
        for i in range(5):
            flights.append(Flight(
                plane_id=[plane3.id, plane1.id][i % 2],
                origin='Islamabad (ISB)',
                destination='Karachi (KHI)',
                duration='2h',
                departure_time=base_date + timedelta(days=i, hours=10 + i*2),
                status='on_time'
            ))
        
        # Karachi to Peshawar flights - 5 flights on different dates/times
        for i in range(5):
            flights.append(Flight(
                plane_id=[plane4.id, plane2.id][i % 2],
                origin='Karachi (KHI)',
                destination='Peshawar (PEW)',
                duration='2h 15m',
                departure_time=base_date + timedelta(days=i, hours=12 + i*2),
                status='on_time'
            ))
        
        # Lahore to Peshawar flights - 5 flights on different dates/times
        for i in range(5):
            flights.append(Flight(
                plane_id=[plane5.id, plane3.id][i % 2],
                origin='Lahore (LHE)',
                destination='Peshawar (PEW)',
                duration='1h 30m',
                departure_time=base_date + timedelta(days=i, hours=14 + i*2),
                status='on_time'
            ))
        
        db.session.add_all(flights)
        db.session.commit()

        # ----------------------------------------------------------------
        # 3. Create Staff Users  (STF-1001 … STF-1008 hardcoded)
        # ----------------------------------------------------------------
        hashed_pw = bcrypt.generate_password_hash('password123').decode('utf-8')

        staff_data = [
            # (first, last, phone, email, age, staff_id)
            ('James',    'Carter',   '03001234567', 'james.carter@skystream.com',   35, 'STF-1001'),
            ('Aisha',    'Rahman',   '03009876543', 'aisha.rahman@skystream.com',   29, 'STF-1002'),
            ('Omar',     'Farooq',   '03111122233', 'omar.farooq@skystream.com',    42, 'STF-1003'),
            ('Sana',     'Malik',    '03214455667', 'sana.malik@skystream.com',     31, 'STF-1004'),
            ('Bilal',    'Ahmed',    '03335566778', 'bilal.ahmed@skystream.com',    38, 'STF-1005'),
            ('Fatima',   'Siddiqui', '03446677889', 'fatima.siddiqui@skystream.com',26, 'STF-1006'),
            ('Tariq',    'Hussain',  '03557788990', 'tariq.hussain@skystream.com',  45, 'STF-1007'),
            ('Mariam',   'Khan',     '03668899001', 'mariam.khan@skystream.com',    33, 'STF-1008'),
        ]
        staff_users = []
        for fn, ln, ph, em, ag, sid in staff_data:
            u = User(first_name=fn, last_name=ln, phone_number=ph,
                     email=em, age=ag, password=hashed_pw,
                     role='staff', staff_id=sid)
            staff_users.append(u)
        db.session.add_all(staff_users)
        db.session.commit()

        # ----------------------------------------------------------------
        # 4. Create Staff Profiles
        # ----------------------------------------------------------------
        profile_data = [
            # (user_index, role, salary, duties, rating, points)
            (0, 'Pilot',       95000.0, 48, 4.9, 2400),
            (1, 'Cabin Crew',  42000.0, 22, 4.7,  890),
            (2, 'Co-Pilot',    78000.0, 35, 4.8, 1750),
            (3, 'Purser',      55000.0, 30, 4.6, 1200),
            (4, 'Engineer',    88000.0, 41, 4.5, 2100),
            (5, 'Cabin Crew',  40000.0, 18, 4.8,  740),
            (6, 'Pilot',       97000.0, 52, 5.0, 3100),
            (7, 'Co-Pilot',    76000.0, 27, 4.7, 1350),
        ]
        profiles = []
        for idx, role, salary, duties, rating, pts in profile_data:
            p = StaffProfile(user_id=staff_users[idx].id, role=role,
                             salary=salary, completed_duties=duties,
                             feedback_rating=rating, reward_points=pts)
            profiles.append(p)
        db.session.add_all(profiles)
        db.session.commit()

        # ----------------------------------------------------------------
        # 5. Create Admin User  (hardcoded: Hussain / hussain9887)
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

        # ----------------------------------------------------------------
        # 7. Assign Staff to Rosters
        # ----------------------------------------------------------------
        all_flights = Flight.query.limit(8).all()
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
        for i, profile in enumerate(profiles):
            if i < len(all_flights):
                rosters.append(Roster(
                    staff_profile_id=profile.id,
                    flight_id=all_flights[i].id,
                    hotel=hotels[i],
                    travel_id=f'TRV-{9900+i+1}-{chr(65+i)}',
                ))
        db.session.add_all(rosters)
        db.session.commit()

        print("✅ Database seeded successfully!")
        print("-------------------------------------------")
        print("  ADMIN LOGIN   → Username: Hussain  | PW: hussain9887")
        print("  Staff IDs     → STF-1001 … STF-1008 | PW: password123")
        print("  Customer      → Email: sarah.mitchell@example.com | PW: customer123")
        print("-------------------------------------------")

if __name__ == '__main__':
    seed_database()

