"""
Assigns existing staff members to flights in the DB.
Run: python3 seed_rosters.py  (from backend/)
"""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

from app import app, db
from models import User, Flight, StaffProfile, Roster

HOTELS = ['Pearl Continental', 'Serena Hotel', 'Marriott', 'Avari Towers', 'Ramada', 'Best Western']

with app.app_context():
    flights = Flight.query.order_by(Flight.id).all()
    if not flights:
        print('❌ No flights found. Add flights first.')
        sys.exit(1)

    staff_users = User.query.filter_by(role='staff').all()
    if not staff_users:
        print('❌ No staff found.')
        sys.exit(1)

    added = 0
    for idx, user in enumerate(staff_users):
        profile = user.staff_profile
        if not profile:
            profile = StaffProfile(user_id=user.id, role='Cabin Crew', salary=60000)
            db.session.add(profile)
            db.session.flush()

        # Skip if already has a roster
        if profile.rosters:
            continue

        flight = flights[idx % len(flights)]
        hotel  = f'{HOTELS[idx % len(HOTELS)]} — {flight.destination.split("(")[0].strip()}'
        roster = Roster(
            staff_profile_id=profile.id,
            flight_id=flight.id,
            hotel=hotel,
            travel_id=f'TRV-{1001 + idx:04d}',
        )
        db.session.add(roster)
        added += 1

    db.session.commit()
    print(f'✅ Assigned {added} staff member(s) to flights.')
    for u in staff_users:
        p = u.staff_profile
        r = p.rosters[0] if p and p.rosters else None
        print(f'  {u.staff_id or u.email} → Flight #{r.flight_id if r else "NONE"} ({r.flight.origin[:3] if r else ""}→{r.flight.destination[:3] if r else ""})')
