"""
Run this script to delete all booking-related data from the database.
Usage:  cd backend && python clear_bookings.py
"""
from app import app, db
from models import Booking, Passenger, Ticket, Roster

with app.app_context():
    try:
        deleted_rosters   = Roster.query.delete()
        deleted_tickets   = Ticket.query.delete()
        deleted_passengers = Passenger.query.delete()
        deleted_bookings  = Booking.query.delete()
        db.session.commit()
        print(f"✅ Cleared:")
        print(f"   {deleted_bookings}  bookings")
        print(f"   {deleted_passengers}  passengers")
        print(f"   {deleted_tickets}  tickets")
        print(f"   {deleted_rosters}  rosters")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error: {e}")
