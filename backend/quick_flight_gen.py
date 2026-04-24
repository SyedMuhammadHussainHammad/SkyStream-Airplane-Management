#!/usr/bin/env python3
"""
Quick flight generator for testing - creates a few flights for immediate use
"""
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Flight, Plane
from datetime import datetime, timedelta

def create_test_flights():
    """Create a few test flights for immediate use"""
    with app.app_context():
        print("🚀 Creating test flights...")
        
        # Create a test plane if none exists
        if Plane.query.count() == 0:
            plane = Plane(
                plane_id="PK-001",
                model="Boeing 737",
                capacity=180,
                status="on_ground",
                current_airport="Karachi (KHI)"
            )
            db.session.add(plane)
            db.session.commit()
            print("✅ Created test plane: PK-001")
        
        plane = Plane.query.first()
        
        # Create test flights for today and tomorrow
        routes = [
            ("Karachi (KHI)", "Lahore (LHE)", "1h 30m"),
            ("Lahore (LHE)", "Karachi (KHI)", "1h 30m"),
            ("Karachi (KHI)", "Islamabad (ISB)", "2h 15m"),
            ("Islamabad (ISB)", "Karachi (KHI)", "2h 15m"),
        ]
        
        base_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        
        flights_created = 0
        for day_offset in range(3):  # Create for next 3 days
            for hour_offset, (origin, dest, duration) in enumerate(routes):
                departure_time = base_time + timedelta(days=day_offset, hours=hour_offset * 3)
                
                # Check if flight already exists
                existing = Flight.query.filter_by(
                    origin=origin,
                    destination=dest,
                    departure_time=departure_time
                ).first()
                
                if not existing:
                    flight = Flight(
                        origin=origin,
                        destination=dest,
                        duration=duration,
                        departure_time=departure_time,
                        plane_id=plane.id,
                        status='on_time'
                    )
                    db.session.add(flight)
                    flights_created += 1
        
        db.session.commit()
        print(f"✅ Created {flights_created} test flights")
        print("🎉 Test flights ready! You can now search for flights.")

if __name__ == "__main__":
    create_test_flights()