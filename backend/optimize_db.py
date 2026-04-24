#!/usr/bin/env python3
"""
Database Optimization Script
===========================
Adds indexes for better performance on common queries.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text

def optimize_database():
    """Add database indexes for better performance."""
    print("🚀 Optimizing database performance...")
    
    with app.app_context():
        # Add indexes for common queries
        try:
            # Index on flight departure_time for faster date filtering
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_flight_departure_time ON flight(departure_time);'))
            
            # Index on flight status for faster status filtering
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_flight_status ON flight(status);'))
            
            # Index on user role for faster role-based queries
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_user_role ON "user"(role);'))
            
            # Index on booking payment_status for revenue calculations
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_booking_payment_status ON booking(payment_status);'))
            
            # Index on plane status for fleet management
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_plane_status ON plane(status);'))
            
            db.session.commit()
            
            print("✅ Database indexes created successfully!")
            print("   • Flight departure_time index")
            print("   • Flight status index") 
            print("   • User role index")
            print("   • Booking payment_status index")
            print("   • Plane status index")
            
        except Exception as e:
            print(f"⚠️  Some indexes may already exist: {e}")
            
        print("\n🎯 Performance optimizations complete!")

if __name__ == '__main__':
    optimize_database()