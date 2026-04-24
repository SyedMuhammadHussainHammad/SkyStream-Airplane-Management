"""
seed_pakistan.py — SkyStream Pakistan
Seeds: 1 Super Admin, 60 Staff (SS-PAK-001..060), 10 Planes (AP-*),
       6 Pakistani airports as Flights interconnecting them.
"""
from app import app, db, bcrypt
from models import User, StaffProfile, Flight, StaffRoster, Plane
from datetime import datetime, timedelta
import random

# ── Pakistani airports ──────────────────────────────────────────────────────
AIRPORTS = [
    'Karachi (KHI)',
    'Lahore (LHE)',
    'Islamabad (ISB)',
    'Peshawar (PEW)',
    'Multan (MUX)',
    'Quetta (UET)',
]

# ── 10 planes with AP-* Pakistani registrations ─────────────────────────────
PLANES_DATA = [
    ('AP-BGL', 'Boeing 777-300ER',   396),
    ('AP-BGJ', 'Airbus A320neo',     165),
    ('AP-BHO', 'Boeing 737-800',     189),
    ('AP-BGY', 'Airbus A321neo',     194),
    ('AP-BKI', 'Boeing 777-200LR',   305),
    ('AP-BMH', 'Airbus A320ceo',     150),
    ('AP-BIG', 'Boeing 737-300',     149),
    ('AP-BHX', 'Airbus A330-300',    295),
    ('AP-BMA', 'Boeing 787-8',       242),
    ('AP-BNA', 'Airbus A310-300',    220),
]

# ── 60 realistic Pakistani names  ────────────────────────────────────────────
FIRST_NAMES = [
    'Ahmed','Ali','Usman','Hassan','Bilal','Faisal','Tariq','Asad','Imran','Zain',
    'Hamza','Malik','Raza','Saad','Junaid','Fahad','Naveed','Waseem','Akbar','Zahid',
    'Sana','Ayesha','Fatima','Nadia','Maria','Hina','Zara','Sara','Iqra','Maham',
    'Amna','Rabia','Sidra','Komal','Noor','Bushra','Saima','Shabnam','Rida','Mehwish',
    'Kamran','Omer','Adnan','Sohail','Shahid','Rizwan','Nasir','Qaiser','Waqas','Arif',
    'Tahir','Kashif','Danish','Babar','Fawad','Salman','Irfan','Rehan','Zubair','Farhan',
]

LAST_NAMES = [
    'Khan','Ahmed','Malik','Sheikh','Qureshi','Mirza','Chaudhry','Iqbal','Siddiqui','Hussain',
    'Ali','Shah','Raza','Butt','Bhatti','Javed','Nawaz','Aslam','Anwar','Hameed',
    'Baig','Gilani','Khawaja','Cheema','Dogar','Awan','Tarar','Bajwa','Niazi','Lodhi',
]

ROLES = ['Pilot', 'Co-Pilot', 'Cabin Crew', 'Purser', 'Engineer']


def seed_pakistan():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # ── 1. Super Admin ──────────────────────────────────────────────────
        admin = User(
            first_name='Hussain',
            last_name='Admin',
            phone_number='03001000001',
            email='hussain@skystream.pk',
            age=30,
            password=bcrypt.generate_password_hash('hussain9887').decode('utf-8'),
            role='admin',
        )
        db.session.add(admin)
        db.session.commit()

        # ── 2. Planes ───────────────────────────────────────────────────────
        planes = []
        statuses = ['on_ground', 'on_ground', 'on_ground', 'on_ground', 'on_ground',
                    'in_flight', 'in_flight', 'in_flight', 'maintenance', 'on_ground']
        for idx, (tail, model, cap) in enumerate(PLANES_DATA):
            airport = AIRPORTS[idx % len(AIRPORTS)]
            plane = Plane(
                plane_id=tail,
                model=model,
                capacity=cap,
                current_airport=airport,
                status=statuses[idx],
            )
            db.session.add(plane)
        db.session.commit()
        planes = Plane.query.order_by(Plane.id).all()

        # ── 3. Flights connecting Pakistani cities ──────────────────────────
        flight_routes = [
            ('Karachi (KHI)',    'Islamabad (ISB)',  '2h 00m', 2,  0, 'on_time'),
            ('Lahore (LHE)',     'Karachi (KHI)',    '1h 30m', 3,  4, 'on_time'),
            ('Islamabad (ISB)', 'Peshawar (PEW)',   '0h 45m', 4,  8, 'on_time'),
            ('Karachi (KHI)',    'Quetta (UET)',     '1h 20m', 6,  0, 'on_time'),
            ('Lahore (LHE)',     'Multan (MUX)',     '0h 55m', 7,  6, 'delayed'),
            ('Islamabad (ISB)', 'Lahore (LHE)',     '0h 50m', 5,  2, 'on_time'),
            ('Peshawar (PEW)',  'Karachi (KHI)',    '2h 10m', 9,  0, 'on_time'),
            ('Multan (MUX)',    'Islamabad (ISB)', '1h 15m', 3,  2, 'on_time'),
            ('Quetta (UET)',    'Lahore (LHE)',     '1h 45m', 8,  4, 'on_time'),
            ('Karachi (KHI)',    'Peshawar (PEW)',  '2h 20m', 7,  0, 'on_time'),
        ]

        flights = []
        for origin, dest, dur, days_ahead, hours_offset, status in flight_routes:
            dep = datetime.utcnow() + timedelta(days=days_ahead, hours=hours_offset)
            # assign a plane (cycle through available ones)
            plane_idx = len(flights) % len(planes)
            f = Flight(
                plane_id=planes[plane_idx].id,
                origin=origin,
                destination=dest,
                duration=dur,
                departure_time=dep,
                status=status,
            )
            db.session.add(f)
            flights.append(f)
        db.session.commit()
        flights = Flight.query.order_by(Flight.id).all()

        # ── 4. 60 Staff members ─────────────────────────────────────────────
        random.seed(42)   # reproducible data
        used_phones = set(['03001000001'])
        used_emails = set(['hussain@skystream.pk'])

        staff_users   = []
        staff_profiles = []

        for i in range(60):
            staff_num = i + 1
            staff_id  = f'SS-PAK-{staff_num:03d}'
            first     = FIRST_NAMES[i % len(FIRST_NAMES)]
            last      = LAST_NAMES[i % len(LAST_NAMES)]
            age       = random.randint(22, 55)
            sex       = 'Male' if first in [
                'Ahmed','Ali','Usman','Hassan','Bilal','Faisal','Tariq','Asad','Imran','Zain',
                'Hamza','Malik','Raza','Saad','Junaid','Fahad','Naveed','Waseem','Akbar','Zahid',
                'Kamran','Omer','Adnan','Sohail','Shahid','Rizwan','Nasir','Qaiser','Waqas','Arif',
                'Tahir','Kashif','Danish','Babar','Fawad','Salman','Irfan','Rehan','Zubair','Farhan',
            ] else 'Female'
            dob = datetime(1970 + age - 22, random.randint(1, 12), random.randint(1, 28))

            # unique phone
            while True:
                phone = f'03{random.randint(0,4):02d}{random.randint(1000000,9999999)}'
                if phone not in used_phones:
                    used_phones.add(phone)
                    break

            # unique email
            email_base = f'{first.lower()}.{last.lower()}{staff_num}'
            email = f'{email_base}@skystream.pk'
            while email in used_emails:
                email = f'{email_base}_{random.randint(10,99)}@skystream.pk'
            used_emails.add(email)

            # truncate phone to 11 chars just in case
            phone = phone[:11]

            user = User(
                first_name=first,
                last_name=last,
                phone_number=phone,
                email=email,
                age=age,
                password=bcrypt.generate_password_hash('password123').decode('utf-8'),
                role='staff',
                staff_id=staff_id,
            )
            db.session.add(user)
            staff_users.append((user, dob, sex))

        db.session.commit()

        # ── 5. Staff Profiles + Rosters ────────────────────────────────────
        profile_objs = []
        for idx, (user, dob, sex) in enumerate(staff_users):
            role = ROLES[idx % len(ROLES)]
            profile = StaffProfile(
                user_id=user.id,
                role=role,
                salary=round(random.uniform(40000, 150000), 2),
                completed_duties=random.randint(5, 80),
                feedback_rating=round(random.uniform(3.5, 5.0), 1),
                reward_points=random.randint(100, 5000),
            )
            db.session.add(profile)
            profile_objs.append(profile)
        db.session.commit()

        # Assign each staff member to one flight (cycle)
        for idx, profile in enumerate(profile_objs):
            flight = flights[idx % len(flights)]
            roster = StaffRoster(
                staff_profile_id=profile.id,
                flight_id=flight.id,
                hotel=f'Hotel {["Pearl Continental", "Serena", "Marriott", "Avari", "Ramada", "Best Western"][idx % 6]} — {flight.destination}',
                travel_id=f'TRV-PAK-{idx + 1001:04d}',
            )
            db.session.add(roster)
        db.session.commit()

        # ── Done ─────────────────────────────────────────────────────────────
        print('✅  SkyStream Pakistan seeded!')
        print('─' * 55)
        print('  Super Admin  → Username: Hussain | PW: hussain9887')
        print('  Staff login  → ID: SS-PAK-001 to SS-PAK-060 | PW: password123')
        print(f'  Flights: {len(flights)}  |  Planes: {len(planes)}  |  Staff: 60')
        print('─' * 55)


if __name__ == '__main__':
    seed_pakistan()
