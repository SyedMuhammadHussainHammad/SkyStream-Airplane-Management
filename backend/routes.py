import os
from flask import (
    render_template, url_for, flash, redirect,
    request, jsonify, abort
)
from functools import wraps
from sqlalchemy import text
from datetime import datetime, timezone

from flask_login import login_user, current_user, login_required, logout_user

from app import app, db, bcrypt

from forms import (
    CustomerRegistrationForm,
    LoginForm,
    FlightSearchForm
)

from models import User, Flight, Seat

# ── UTILS ──
def utc_now():
    return datetime.now(timezone.utc)

# ── DECORATORS ──
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return wrapper

# ── HOME ──
@app.route('/')
def home():
    return render_template('home.html')

# ── REGISTER ──
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = CustomerRegistrationForm()

    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone_number=form.phone_number.data,
            age=form.age.data,
            password=hashed_pw,
            role='customer'
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully", "success")
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

# ── LOGIN ──
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('home'))

        flash("Invalid credentials", "danger")

    return render_template('login.html', form=form)

# ── LOGOUT ──
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# ── HEALTH ──
@app.route('/health')
def health():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "ok", "db": "connected"})
    except Exception as e:
        return jsonify({"status": "error", "db": str(e)})

# ── FLIGHTS ──
@app.route('/flights/search')
def search_flights():
    source = request.args.get('source')
    destination = request.args.get('destination')

    query = Flight.query

    if source:
        query = query.filter(Flight.origin.ilike(f"%{source}%"))
    if destination:
        query = query.filter(Flight.destination.ilike(f"%{destination}%"))

    flights = query.all()

    return render_template("flights.html", flights=flights)

# ── SEATS API ──
@app.route('/api/flights/<int:flight_id>/seats')
def api_seats(flight_id):
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
