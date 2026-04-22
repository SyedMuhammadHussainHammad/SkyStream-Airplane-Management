import os
import re
from flask import render_template, url_for, flash, redirect, request, session, jsonify, abort
from functools import wraps
from sqlalchemy import text

from app import app, db, bcrypt
from forms import CustomerRegistrationForm, LoginForm, FlightSearchForm, PackageSelectionForm, PassengerDetailsForm
from models import (
    User, StaffProfile, Flight, StaffRoster,
    Booking, Passenger, Ticket, Plane, Seat
)
from flask_login import login_user, current_user, logout_user, login_required
from urllib.parse import urlparse
from datetime import datetime, timedelta, timezone


# ---------------------------------------------------------------------------
# Constants — override via env vars in production
# ---------------------------------------------------------------------------
SUPER_ADMIN_USER = os.environ.get('SUPER_ADMIN_USER', 'Hussain')
SUPER_ADMIN_PASS = os.environ.get('SUPER_ADMIN_PASS', 'hussain9887')

PACKAGE_PRICES = {
    'Economy': 24000,
    'Basic':   19000,
    'Premium': 30000,
}
PACKAGE_LUGGAGE = {
    'Economy': 10,
    'Basic':   23,
    'Premium': 56,
}
PACKAGE_COLOR = {
    'Economy': 'green',
    'Basic':   'blue',
    'Premium': 'gold',
}
PAYMENT_METHODS = {
    'card': 'Credit / Debit Card',
    'jazzcash': 'JazzCash',
}
LOYALTY_TIERS = [
    (1500, 'Gold'),
    (500,  'Silver'),
    (0,    'Bronze'),
]


# ---------------------------------------------------------------------------
# FIXED: timezone-safe datetime
# ---------------------------------------------------------------------------
def utc_now():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Unauthorized access.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated


def customer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'customer':
            flash('Only customers can access this page.', 'warning')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _parse_duration(duration_str):
    hours = minutes = 0
    h_match = re.search(r'(\d+)h', duration_str or '')
    m_match = re.search(r'(\d+)m', duration_str or '')
    if h_match:
        hours = int(h_match.group(1))
    if m_match:
        minutes = int(m_match.group(1))
    return timedelta(hours=hours, minutes=minutes)


def _sync_plane_locations():
    now = utc_now()

    planes = Plane.query.all()
    changed = False

    for plane in planes:
        if plane.status == 'maintenance':
            continue

        past_flights = [f for f in plane.flights if f.departure_time <= now]
        if not past_flights:
            if plane.status != 'on_ground':
                plane.status = 'on_ground'
                changed = True
            continue

        latest = max(past_flights, key=lambda f: f.departure_time)
        flight_duration = _parse_duration(latest.duration)
        landing_time = latest.departure_time + flight_duration

        if now < landing_time:
            if plane.status != 'in_flight':
                plane.status = 'in_flight'
                plane.current_airport = latest.destination
                changed = True
        else:
            if plane.current_airport != latest.destination or plane.status != 'on_ground':
                plane.current_airport = latest.destination
                plane.status = 'on_ground'
                latest.status = 'landed'
                changed = True

    if changed:
        db.session.commit()


def _get_loyalty(total_spent):
    for threshold, tier in LOYALTY_TIERS:
        if total_spent >= threshold:
            return tier
    return 'Bronze'


def _safe_next(next_url):
    if next_url and urlparse(next_url).netloc == '':
        return next_url
    return url_for('home')


# ---------------------------------------------------------------------------
# DB init route
# ---------------------------------------------------------------------------
@app.route('/init-db')
def init_db():
    try:
        db.create_all()
        return jsonify({"status": "ok", "message": "All tables created."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ---------------------------------------------------------------------------
# Public routes
# ---------------------------------------------------------------------------
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/privacy')
def privacy():
    return render_template('privacy.html')


@app.route('/terms')
def terms():
    return render_template('terms.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.route('/health')
def health():
    try:
        db.session.execute(text('SELECT 1'))
        db_status = 'connected'
    except Exception as ex:
        db_status = f'error: {ex}'

    return jsonify({
        'status': 'running',
        'db_status': db_status,
    })


# ---------------------------------------------------------------------------
# FIXED: Flight search route (resolved BuildError)
# ---------------------------------------------------------------------------
@app.route('/flights/search', endpoint='search_flights')
def search_flights():
    try:
        form = FlightSearchForm()

        source = request.args.get('source')
        destination = request.args.get('destination')

        flights = Flight.query

        if source:
            flights = flights.filter(Flight.source.ilike(f"%{source}%"))
        if destination:
            flights = flights.filter(Flight.destination.ilike(f"%{destination}%"))

        flights = flights.all()

        return render_template(
            'flights.html',
            form=form,
            flights=flights
        )
    except Exception as e:
        return f"Error: {str(e)}", 500


# ---------------------------------------------------------------------------
# API — Seats
# ---------------------------------------------------------------------------
@app.route('/api/flights/<int:flight_id>/seats')
def api_flight_seats(flight_id):
    try:
        Flight.query.get_or_404(flight_id)
        Seat.generate_for_flight(flight_id)

        seats = Seat.query.filter_by(flight_id=flight_id).all()

        return jsonify([
            {
                'seat_number': s.seat_number,
                'class_type': s.class_type,
                'is_available': s.is_available,
            } for s in seats
        ])
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
