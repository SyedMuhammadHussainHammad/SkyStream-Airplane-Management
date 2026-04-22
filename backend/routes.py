import os
import re
from flask import (
    render_template, url_for, flash, redirect,
    request, session, jsonify, abort
)
from functools import wraps
from sqlalchemy import text
from urllib.parse import urlparse
from datetime import datetime, timedelta, timezone

from app import app, db, bcrypt
from flask_login import login_user, current_user, login_required, logout_user

from forms import (
    CustomerRegistrationForm,
    LoginForm,
    FlightSearchForm,
    PackageSelectionForm,
    PassengerDetailsForm
)

from models import (
    User, StaffProfile, Flight, StaffRoster,
    Booking, Passenger, Ticket, Plane, Seat
)

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
SUPER_ADMIN_USER = os.environ.get('SUPER_ADMIN_USER', 'Hussain')
SUPER_ADMIN_PASS = os.environ.get('SUPER_ADMIN_PASS', 'hussain9887')

LOYALTY_TIERS = [
    (1500, 'Gold'),
    (500, 'Silver'),
    (0, 'Bronze'),
]

# ---------------------------------------------------------------------------
# TIME UTILITY
# ---------------------------------------------------------------------------
def utc_now():
    return datetime.now(timezone.utc)

# ---------------------------------------------------------------------------
# DECORATORS
# ---------------------------------------------------------------------------
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash("Unauthorized access", "danger")
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return wrapper


def customer_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'customer':
            flash("Customers only area", "warning")
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# HOME
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
# AUTH FIX (REGISTER ADDED → FIXES YOUR BUILD ERROR)
# ---------------------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = CustomerRegistrationForm()

    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_pw,
            role='customer'
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully", "success")
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


# ---------------------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials", "danger")

    return render_template('login.html', form=form)


# ---------------------------------------------------------------------------
# LOGOUT (PREVENT TEMPLATE CRASH)
# ---------------------------------------------------------------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "info")
    return redirect(url_for('home'))


# ---------------------------------------------------------------------------
# STAFF DASHBOARD
# ---------------------------------------------------------------------------
@app.route('/staff/dashboard')
@login_required
def staff_dashboard():
    if current_user.role != 'admin':
        abort(403)

    return render_template('staff_dashboard.html')


# ---------------------------------------------------------------------------
# HEALTH CHECK (SAFE)
# ---------------------------------------------------------------------------
@app.route('/health')
def health():
    try:
        db.session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return jsonify({
        "status": "running",
        "db_status": db_status
    })


# ---------------------------------------------------------------------------
# FLIGHT SEARCH
# ---------------------------------------------------------------------------
@app.route('/flights/search')
def search_flights():
    form = FlightSearchForm()

    source = request.args.get('source')
    destination = request.args.get('destination')

    query = Flight.query

    if source:
        query = query.filter(Flight.source.ilike(f"%{source}%"))
    if destination:
        query = query.filter(Flight.destination.ilike(f"%{destination}%"))

    flights = query.all()

    return render_template(
        'flights.html',
        form=form,
        flights=flights
    )


# ---------------------------------------------------------------------------
# DB INIT
# ---------------------------------------------------------------------------
@app.route('/init-db')
def init_db():
    try:
        db.create_all()
        return jsonify({"status": "ok", "message": "Database created"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ---------------------------------------------------------------------------
# API: SEATS
# ---------------------------------------------------------------------------
@app.route('/api/flights/<int:flight_id>/seats')
def api_flight_seats(flight_id):
    try:
        Flight.query.get_or_404(flight_id)
        Seat.generate_for_flight(flight_id)

        seats = Seat.query.filter_by(flight_id=flight_id).all()

        return jsonify([
            {
                "seat_number": s.seat_number,
                "class_type": s.class_type,
                "is_available": s.is_available
            }
            for s in seats
        ])

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
