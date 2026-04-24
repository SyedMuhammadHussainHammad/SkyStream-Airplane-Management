#!/bin/bash

echo "=================================================="
echo "SkyStream Flight Booking System"
echo "=================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

echo "Starting SkyStream application..."
echo "🌐 Access at: http://localhost:5000"
echo "🔑 Admin login: admin@skystream.com / admin123"
echo "Press Ctrl+C to stop"
echo "--------------------------------------------------"

cd backend
python app.py