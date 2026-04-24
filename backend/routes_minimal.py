import os
from flask import render_template, url_for, flash, redirect, request, jsonify, abort
from functools import wraps
from datetime import datetime, timezone, timedelta, date

from flask_login import login_user, current_user, login_required, logout_user

from app import app, db, bcrypt
from forms import CustomerRegistrationForm, LoginForm, FlightSearchForm
from models import User, Flight, Seat, Plane, Booking, StaffProfile, SeatLock, PaymentTransaction

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

# ── HEALTH ──
@app.route('/health')
def health():
    return jsonify({"status": "ok", "message": "Application is running"})

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
        login_type = form.login_type.data
        if login_type == 'staff':
            user = User.query.filter_by(staff_id=form.staff_id.data, role='staff').first()
        elif login_type == 'admin':
            user = User.query.filter_by(email=form.email.data, role='admin').first()
        else:
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

# ── FLIGHTS SEARCH ──
@app.route('/flights/search', methods=['GET', 'POST'])
def search_flights():
    form = FlightSearchForm()
    outbound_flights = []
    return_flights = []
    searched = False
    trip_type = 'one_way'

    if request.method == 'POST':
        searched = True
        origin = request.form.get('origin', '').strip()
        destination = request.form.get('destination', '').strip()
        trip_type = request.form.get('trip_type', 'one_way').strip()
        
        # Simple flight search
        if origin and destination:
            outbound_flights = Flight.query.filter(
                Flight.origin.contains(origin),
                Flight.destination.contains(destination)
            ).limit(10).all()
            
            if trip_type == 'return':
                return_flights = Flight.query.filter(
                    Flight.origin.contains(destination),
                    Flight.destination.contains(origin)
                ).limit(10).all()

    # Process flights with simple data
    outbound_flight_data = []
    for f in outbound_flights:
        outbound_flight_data.append({
            'flight': f, 
            'available': 150, 
            'total': 180, 
            'sold_out': False
        })

    return_flight_data = []
    for f in return_flights:
        return_flight_data.append({
            'flight': f, 
            'available': 150, 
            'total': 180, 
            'sold_out': False
        })

    return render_template("search.html", 
                         outbound_flights=outbound_flight_data,
                         return_flights=return_flight_data,
                         form=form, 
                         searched=searched,
                         trip_type=trip_type,
                         now_date=utc_now().date().isoformat())

# ── STATIC PAGES ──
@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# ── ERROR HANDLERS ──
@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500