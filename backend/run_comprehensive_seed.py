#!/usr/bin/env python3
"""
Quick runner for the comprehensive database seeding
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comprehensive_seed import comprehensive_seed

if __name__ == '__main__':
    print("🚀 Running comprehensive database seeding...")
    comprehensive_seed()
    print("✅ Seeding completed successfully!")