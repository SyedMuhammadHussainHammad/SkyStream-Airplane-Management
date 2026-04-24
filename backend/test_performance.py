#!/usr/bin/env python3
"""
Performance Test Script
======================
Tests the performance of admin dashboard queries.
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Flight, User, Plane, Booking
from datetime import datetime

def test_performance():
    """Test query performance."""
    print("⚡ Testing Admin Dashboard Performance")
    print("=" * 50)
    
    with app.app_context():
        # Test 1: Flight queries
        start_time = time.time()
        now = datetime.utcnow()
        upcoming_flights = Flight.query.filter(Flight.departure_time >= now).count()
        flight_query_time = time.time() - start_time
        
        # Test 2: User queries
        start_time = time.time()
        staff_count = User.query.filter_by(role='staff').count()
        customer_count = User.query.filter_by(role='customer').count()
        user_query_time = time.time() - start_time
        
        # Test 3: Plane status aggregation
        start_time = time.time()
        plane_status_counts = db.session.query(
            Plane.status, db.func.count(Plane.id)
        ).group_by(Plane.status).all()
        plane_query_time = time.time() - start_time
        
        # Test 4: Revenue calculation
        start_time = time.time()
        total_revenue = db.session.query(
            db.func.sum(Booking.total_price)
        ).filter_by(payment_status='confirmed').scalar() or 0
        revenue_query_time = time.time() - start_time
        
        # Test 5: Paginated flight query
        start_time = time.time()
        flights_page = Flight.query.filter(
            Flight.departure_time >= now
        ).order_by(Flight.departure_time.asc()).limit(20).all()
        pagination_query_time = time.time() - start_time
        
        print(f"📊 PERFORMANCE RESULTS:")
        print(f"   🗓️  Upcoming flights count: {upcoming_flights} ({flight_query_time:.3f}s)")
        print(f"   👥  Staff count: {staff_count}, Customers: {customer_count} ({user_query_time:.3f}s)")
        print(f"   ✈️  Plane status aggregation: {len(plane_status_counts)} groups ({plane_query_time:.3f}s)")
        print(f"   💰  Revenue calculation: ${total_revenue:,.2f} ({revenue_query_time:.3f}s)")
        print(f"   📄  Paginated flights (20): {len(flights_page)} flights ({pagination_query_time:.3f}s)")
        
        total_time = flight_query_time + user_query_time + plane_query_time + revenue_query_time + pagination_query_time
        print(f"\n⚡ TOTAL DASHBOARD LOAD TIME: {total_time:.3f}s")
        
        if total_time < 0.5:
            print("🚀 EXCELLENT: Dashboard should load very fast!")
        elif total_time < 1.0:
            print("✅ GOOD: Dashboard should load reasonably fast")
        elif total_time < 2.0:
            print("⚠️  MODERATE: Dashboard may feel a bit slow")
        else:
            print("🐌 SLOW: Dashboard needs further optimization")
        
        print("\n" + "=" * 50)

if __name__ == '__main__':
    test_performance()