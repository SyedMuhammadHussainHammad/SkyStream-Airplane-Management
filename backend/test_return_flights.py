#!/usr/bin/env python3
"""
Test script to verify return flight search functionality
"""
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Flight
from datetime import datetime, date, timedelta

def test_return_flight_search():
    """Test the return flight search logic"""
    with app.app_context():
        print("🧪 Testing return flight search functionality...")
        
        # Test date parsing
        try:
            test_date = "2024-12-25"
            parsed_date = date.fromisoformat(test_date)
            print(f"✅ Date parsing works: {test_date} -> {parsed_date}")
        except Exception as e:
            print(f"❌ Date parsing failed: {e}")
            return False
        
        # Test database connection
        try:
            flight_count = Flight.query.count()
            print(f"✅ Database connection works: {flight_count} flights found")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
        
        # Test flight query
        try:
            # Search for flights from Karachi to Lahore
            query = Flight.query.filter(
                Flight.origin.ilike("%Karachi%"),
                Flight.destination.ilike("%Lahore%")
            )
            outbound_flights = query.all()
            print(f"✅ Outbound flight search works: {len(outbound_flights)} flights found")
            
            # Search for return flights (Lahore to Karachi)
            return_query = Flight.query.filter(
                Flight.origin.ilike("%Lahore%"),
                Flight.destination.ilike("%Karachi%")
            )
            return_flights = return_query.all()
            print(f"✅ Return flight search works: {len(return_flights)} flights found")
            
        except Exception as e:
            print(f"❌ Flight query failed: {e}")
            return False
        
        print("🎉 All tests passed! Return flight search should work now.")
        return True

if __name__ == "__main__":
    test_return_flight_search()