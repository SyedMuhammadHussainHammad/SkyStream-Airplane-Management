#!/usr/bin/env python3
"""
Initialize database tables and seed with data
Run this after deploying to create all tables
"""

from app import app, db
from models import User, Flight, Plane, Seat, Booking, Passenger, Ticket, StaffProfile, Roster
import sys

def init_database():
    """Create all database tables"""
    with app.app_context():
        try:
            print("Creating database tables...")
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Check if data exists
            flight_count = Flight.query.count()
            user_count = User.query.count()
            
            print(f"\nCurrent data:")
            print(f"  Flights: {flight_count}")
            print(f"  Users: {user_count}")
            
            if flight_count == 0:
                print("\n⚠️  No flights found. Run seed_comprehensive.py to add flight data.")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating tables: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
