import os
import re
from flask import render_template, url_for, flash, redirect, request, session, jsonify, abort
from functools import wraps

from app import app, db, bcrypt
from forms import CustomerRegistrationForm, LoginForm, FlightSearchForm, PackageSelectionForm, PassengerDetailsForm
from models import User, StaffProfile, Flight, StaffRoster, Booking, Passenger, Ticket, Plane, Seat
from flask_login import login_user, current_user, logout_user, login_required
from urllib.parse import urlparse
from datetime import datetime, timedelta

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
# Decorators
# ---------------------------------------------------------------------------
def admin_required(f):
    """Restrict view to admin users only."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Unauthorized access.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated


def customer_required(f):
    """Restrict view to customer users only."""
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
    """Convert '7h 15m' → timedelta. Returns timedelta(0) on failure."""
    hours = minutes = 0
    h_match = re.search(r'(\d+)h', duration_str or '')
    m_match = re.search(r'(\d+)m', duration_str or '')
    if h_match:
        hours = int(h_match.group(1))
    if m_match:
        minutes = int(m_match.group(1))
    return timedelta(hours=hours, minutes=minutes)


def _sync_plane_locations():
    """
    Auto-update plane locations based on past flights.
    Skips planes in 'maintenance'.
    """
    now = datetime.utcnow()
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
    """Return next_url only if it's a relative path (prevents open-redirect)."""
    if next_url and urlparse(next_url).netloc == '':
        return next_url
    return url_for('home')


# ---------------------------------------------------------------------------
# DB initialisation (protected by secret)
# ---------------------------------------------------------------------------
@app.route('/init-db')
def init_db():
    # We are bypassing the os.environ check for local testing
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


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = CustomerRegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone_number=form.phone_number.data,
            email=form.email.data,
            age=form.age.data,
            password=hashed_password,
            role='customer',
        )
        db.session.add(user)
        db.session.commit()
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = None
        login_type = form.login_type.data

        if login_type == 'customer':
            user = User.query.filter_by(email=form.email.data, role='customer').first()

        elif login_type == 'staff':
            user = User.query.filter_by(staff_id=form.staff_id.data, role='staff').first()

        elif login_type == 'admin':
            username_input = (form.email.data or '').strip()
            password_input = form.password.data or ''

            # Super Admin hardcoded bypass — username: Hussain, password: hussain9887
            if (username_input.lower() == SUPER_ADMIN_USER.lower()
                    and password_input == SUPER_ADMIN_PASS):
                # Auto-create a DB admin record if none exists yet
                user = User.query.filter_by(role='admin').first()
                if not user:
                    hashed = bcrypt.generate_password_hash(SUPER_ADMIN_PASS).decode('utf-8')
                    user = User(
                        first_name='Hussain',
                        last_name='Admin',
                        phone_number='03000000000',
                        email='hussain@skystream.com',
                        age=30,
                        password=hashed,
                        role='admin',
                    )
                    db.session.add(user)
                    db.session.commit()
                login_user(user, remember=False)
                return redirect(url_for('admin_dashboard'))
            else:
                user = User.query.filter_by(email=username_input, role='admin').first()

        # Unified password check — covers customer, staff, and admin fallback
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=False)
            if login_type == 'admin':
                return redirect(url_for('admin_dashboard'))
            if login_type == 'staff':
                return redirect(url_for('staff_dashboard'))
            return redirect(_safe_next(request.args.get('next')))

        flash('Login unsuccessful. Please check your credentials.', 'danger')

    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


# ---------------------------------------------------------------------------
# Flight search (public)
# ---------------------------------------------------------------------------
@app.route('/search', methods=['GET', 'POST'])
def search_flights():
    form = FlightSearchForm()
    flights = []
    searched = False
    now_date = datetime.utcnow().strftime('%Y-%m-%d')

    if request.method == 'POST':
        # Read origin/destination directly from raw form data so a bad date
        # field never prevents us from running the search.
        origin = request.form.get('origin', '').strip()
        destination = request.form.get('destination', '').strip()
        trip_type = request.form.get('trip_type', 'one_way').strip()
        return_date_str = request.form.get('return_date', '').strip()

        # Store trip info in session for booking flow
        session['trip_type'] = trip_type
        session['return_date'] = return_date_str if trip_type == 'return' else None

        if origin and destination:
            searched = True
            try:
                q = Flight.query.filter(
                    Flight.origin.ilike(f'%{origin}%'),
                    Flight.destination.ilike(f'%{destination}%'),
                )
                # Only filter by date when the form parsed it successfully
                if form.date.data:
                    q = q.filter(db.func.date(Flight.departure_time) == form.date.data)
                flights = q.order_by(Flight.departure_time).all()
            except Exception:
                db.session.rollback()
                flights = []

            if not flights:
                flash('No flights found. Try different dates or cities.', 'info')
        else:
            flash('Please select both a departure and arrival city.', 'warning')

    return render_template('search.html', title='Search Flights', form=form,
                           flights=flights, searched=searched, now_date=now_date)


# ---------------------------------------------------------------------------
# Booking flow (customer only)
# ---------------------------------------------------------------------------
@app.route('/booking/<int:flight_id>/packages', methods=['GET', 'POST'])
@login_required
@customer_required
def select_package(flight_id):
    flight = Flight.query.get_or_404(flight_id)
    form = PackageSelectionForm()

    if form.validate_on_submit():
        session['booking_flight_id'] = flight.id
        session['booking_package'] = form.package_tier.data
        # Preserve trip type and return date from search
        return redirect(url_for('passenger_details', flight_id=flight.id))

    return render_template('packages.html', title='Select Package',
                           flight=flight, form=form, prices=PACKAGE_PRICES)


@app.route('/booking/<int:flight_id>/passengers', methods=['GET', 'POST'])
@login_required
@customer_required
def passenger_details(flight_id):
    if 'booking_package' not in session or session.get('booking_flight_id') != flight_id:
        flash('Please select a package first.', 'warning')
        return redirect(url_for('select_package', flight_id=flight_id))

    flight = Flight.query.get_or_404(flight_id)
    package_tier = session['booking_package']
    form = PassengerDetailsForm()

    # Generate seats for this flight on first visit
    Seat.generate_for_flight(flight_id)

    # Build seat map
    all_seats = Seat.query.filter_by(flight_id=flight_id).order_by(Seat.id).all()
    seat_rows = {}
    for s in all_seats:
        row_num = int(''.join(filter(str.isdigit, s.seat_number)))
        col = ''.join(filter(str.isalpha, s.seat_number))
        seat_rows.setdefault(row_num, []).append({
            'number': s.seat_number,
            'col': col,
            'class_type': s.class_type,
            'is_available': s.is_available,
        })
    seat_rows_sorted = [(r, seat_rows[r]) for r in sorted(seat_rows.keys())]

    if request.method == 'POST':
        count = int(request.form.get('passengers_count', 1))

        # Validate all required fields are present
        passengers_data = []
        errors = []
        selected_seats = []

        for i in range(count):
            fn = request.form.get(f'first_name_{i}', '').strip()
            ln = request.form.get(f'last_name_{i}', '').strip()
            seat = request.form.get(f'seat_number_{i}', '').strip()
            meal = request.form.get(f'meal_preference_{i}', 'None')

            if not fn or not ln:
                errors.append(f'Passenger {i+1}: first and last name are required.')
            if not seat:
                errors.append(f'Passenger {i+1}: please select a seat.')
            elif seat in selected_seats:
                errors.append(f'Seat {seat} selected more than once.')
            else:
                # Verify seat exists and is available
                seat_obj = Seat.query.filter_by(flight_id=flight_id, seat_number=seat).first()
                if not seat_obj or not seat_obj.is_available:
                    errors.append(f'Seat {seat} is not available.')
                else:
                    selected_seats.append(seat)

            passengers_data.append({
                'first_name': fn,
                'last_name': ln,
                'seat_number': seat,
                'meal_preference': meal,
            })

        if errors:
            for err in errors:
                flash(err, 'danger')
        else:
            session['booking_passengers'] = passengers_data
            session['passengers_count'] = count
            return redirect(url_for('checkout', flight_id=flight.id))

    return render_template(
        'passengers.html',
        title='Passenger Details',
        flight=flight,
        form=form,
        package_tier=package_tier,
        seat_rows=seat_rows_sorted,
    )


@app.route('/checkout/<int:flight_id>', methods=['GET', 'POST'])
@login_required
@customer_required
def checkout(flight_id):
    if 'booking_passengers' not in session:
        return redirect(url_for('passenger_details', flight_id=flight_id))

    flight = Flight.query.get_or_404(flight_id)
    package_tier = session.get('booking_package')

    # Guard against tampered/missing package
    if package_tier not in PACKAGE_PRICES:
        flash('Invalid package selection. Please start again.', 'danger')
        return redirect(url_for('select_package', flight_id=flight_id))

    passengers = session.get('booking_passengers', [])
    count = session.get('passengers_count', len(passengers))
    base_price = PACKAGE_PRICES[package_tier]
    trip_type = session.get('trip_type', 'one_way')
    return_date = session.get('return_date')
    # For return trips, double the price
    total_price = base_price * count * (2 if trip_type == 'return' else 1)

    if request.method == 'POST':
        payment_method = (request.form.get('payment_method') or '').strip()
        if payment_method not in PAYMENT_METHODS:
            flash('Please select a valid payment method to continue.', 'warning')
            return render_template(
                'checkout.html',
                title='Checkout',
                flight=flight,
                package_tier=package_tier,
                passengers=passengers,
                total_price=total_price,
                base_price=base_price,
                payment_method_choices=PAYMENT_METHODS,
                selected_payment_method=payment_method,
                trip_type=trip_type,
                return_date=return_date,
            )

        # Re-validate seat availability at commit time (race condition protection)
        seat_numbers = [p['seat_number'] for p in passengers]
        unavailable = (
            Seat.query
            .filter(
                Seat.flight_id == flight_id,
                Seat.seat_number.in_(seat_numbers),
                Seat.is_available == False,  # noqa: E712
            )
            .all()
        )
        if unavailable:
            taken = ', '.join(s.seat_number for s in unavailable)
            flash(f'Seats {taken} were just taken. Please re-select.', 'danger')
            session.pop('booking_passengers', None)
            return redirect(url_for('passenger_details', flight_id=flight_id))

        # Create booking
        booking = Booking(
            user_id=current_user.id,
            flight_id=flight.id,
            package_tier=package_tier,
            total_price=total_price,
            payment_method=payment_method,
            status='confirmed',
            trip_type=trip_type,
            return_date=return_date if trip_type == 'return' else None,
        )
        db.session.add(booking)
        db.session.flush()  # get booking.id without committing

        luggage = PACKAGE_LUGGAGE[package_tier]
        for p_data in passengers:
            db.session.add(Passenger(
                booking_id=booking.id,
                first_name=p_data['first_name'],
                last_name=p_data['last_name'],
                seat_number=p_data['seat_number'],
                meal_preference=p_data.get('meal_preference', 'None'),
                luggage_allowance=luggage,
            ))
            # Mark seat as taken
            seat_obj = Seat.query.filter_by(
                flight_id=flight_id,
                seat_number=p_data['seat_number'],
            ).first()
            if seat_obj:
                seat_obj.is_available = False

        ticket = Ticket(
            booking_id=booking.id,
            color_code=PACKAGE_COLOR[package_tier],
        )
        db.session.add(ticket)
        db.session.commit()

        # Clear booking session
        for key in ('booking_flight_id', 'booking_package', 'booking_passengers', 'passengers_count', 'trip_type', 'return_date'):
            session.pop(key, None)

        flash('Booking confirmed! Your ticket has been generated.', 'success')
        return redirect(url_for('view_ticket', ticket_id=ticket.id))

    return render_template(
        'checkout.html',
        title='Checkout',
        flight=flight,
        package_tier=package_tier,
        passengers=passengers,
        total_price=total_price,
        base_price=base_price,
        payment_method_choices=PAYMENT_METHODS,
        selected_payment_method='card',
        trip_type=trip_type,
        return_date=return_date,
    )


@app.route('/ticket/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    # Admin can view any ticket; customers only their own
    if current_user.role == 'customer' and ticket.booking.user_id != current_user.id:
        abort(403)
    return render_template('ticket.html', title='Your Ticket', ticket=ticket)


@app.route('/my-bookings')
@login_required
@customer_required
def my_bookings():
    bookings = (
        Booking.query
        .filter_by(user_id=current_user.id)
        .order_by(Booking.id.desc())
        .all()
    )
    return render_template('my_bookings.html', title='My Bookings', bookings=bookings)


# ---------------------------------------------------------------------------
# Staff dashboard
# ---------------------------------------------------------------------------
@app.route('/staff/dashboard')
@login_required
def staff_dashboard():
    if current_user.role != 'staff':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('home'))

    profile = StaffProfile.query.filter_by(user_id=current_user.id).first()
    rosters = StaffRoster.query.filter_by(staff_profile_id=profile.id).all() if profile else []

    return render_template('staff_dashboard.html', title='Staff Dashboard',
                           profile=profile, rosters=rosters)


# ---------------------------------------------------------------------------
# Admin dashboard
# ---------------------------------------------------------------------------
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    _sync_plane_locations()

    planes        = Plane.query.order_by(Plane.plane_id).all()
    staff_members = User.query.filter_by(role='staff').all()
    admin_users   = User.query.filter_by(role='admin').all()
    flights       = Flight.query.order_by(Flight.departure_time.desc()).all()

    raw_customers = User.query.filter_by(role='customer').all()
    customers = []
    for c in raw_customers:
        total_spent = sum(b.total_price for b in c.bookings if b.status == 'confirmed')
        customers.append({
            'user': c,
            'total_spent': total_spent,
            'booking_count': len(c.bookings),
            'loyalty': _get_loyalty(total_spent),
        })

    kpis = {
        'planes':      len(planes),
        'flights':     len(flights),
        'staff':       len(staff_members),
        'admins':      len(admin_users),
        'customers':   len(customers),
        'in_flight':   sum(1 for p in planes if p.status == 'in_flight'),
        'on_ground':   sum(1 for p in planes if p.status == 'on_ground'),
        'maintenance': sum(1 for p in planes if p.status == 'maintenance'),
        'total_revenue': sum(
            b.total_price
            for b in Booking.query.filter_by(status='confirmed').all()
        ),
    }

    return render_template(
        'admin_dashboard.html',
        title='Admin Dashboard',
        planes=planes,
        staff_members=staff_members,
        admin_users=admin_users,
        customers=customers,
        flights=flights,
        kpis=kpis,
        now=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# Admin — Flight management
# ---------------------------------------------------------------------------
@app.route('/admin/flights/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_flight():
    planes = Plane.query.filter_by(status='on_ground').all()
    if request.method == 'POST':
        try:
            plane_id = request.form.get('plane_id')
            origin = request.form.get('origin', '').strip()
            destination = request.form.get('destination', '').strip()
            duration = request.form.get('duration', '').strip()
            dep_str = request.form.get('departure_time', '').strip()

            if not all([plane_id, origin, destination, duration, dep_str]):
                flash('All fields are required.', 'danger')
                return render_template('admin_add_flight.html', planes=planes)

            departure_time = datetime.strptime(dep_str, '%Y-%m-%dT%H:%M')
            flight = Flight(
                plane_id=int(plane_id),
                origin=origin,
                destination=destination,
                duration=duration,
                departure_time=departure_time,
                status='on_time',
            )
            db.session.add(flight)
            db.session.commit()
            flash(f'Flight {origin} → {destination} added.', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding flight: {e}', 'danger')

    return render_template('admin_add_flight.html', title='Add Flight', planes=planes)


@app.route('/admin/flights/<int:flight_id>/status', methods=['POST'])
@login_required
@admin_required
def admin_update_flight_status(flight_id):
    flight = Flight.query.get_or_404(flight_id)
    new_status = request.form.get('status')
    allowed = {'on_time', 'delayed', 'landed', 'cancelled'}
    if new_status not in allowed:
        flash('Invalid status.', 'danger')
    else:
        flight.status = new_status
        db.session.commit()
        flash(f'Flight status updated to {new_status}.', 'success')
    return redirect(url_for('admin_dashboard'))


# ---------------------------------------------------------------------------
# Admin — Staff management
# ---------------------------------------------------------------------------
@app.route('/admin/staff/<int:staff_id>')
@login_required
@admin_required
def admin_view_staff(staff_id):
    staff_user = User.query.get_or_404(staff_id)
    if staff_user.role != 'staff':
        abort(404)
    profile = StaffProfile.query.filter_by(user_id=staff_user.id).first()
    rosters = StaffRoster.query.filter_by(staff_profile_id=profile.id).all() if profile else []
    return render_template('admin_staff_detail.html', staff_user=staff_user,
                           profile=profile, rosters=rosters)


# ---------------------------------------------------------------------------
# Admin — User management (create / delete admins and staff)
# ---------------------------------------------------------------------------

@app.route('/admin/users/create', methods=['POST'])
@login_required
@admin_required
def admin_create_user():
    """Create a new admin or staff/crew member."""
    role = request.form.get('role', '').strip()  # 'admin' or 'staff'
    first_name = request.form.get('first_name', '').strip()
    last_name  = request.form.get('last_name', '').strip()
    email      = request.form.get('email', '').strip()
    phone      = request.form.get('phone', '').strip()
    password   = request.form.get('password', '').strip()
    staff_id   = request.form.get('staff_id', '').strip() or None
    age        = request.form.get('age', '30').strip()
    job_role   = request.form.get('job_role', 'Cabin Crew').strip()  # Pilot / Cabin Crew / etc.
    salary     = request.form.get('salary', '0').strip()

    if role not in ('admin', 'staff'):
        flash('Invalid role specified.', 'danger')
        return redirect(url_for('admin_dashboard') + '#staff')

    if not all([first_name, last_name, email, phone, password]):
        flash('All required fields must be filled.', 'danger')
        return redirect(url_for('admin_dashboard') + '#staff')

    if User.query.filter_by(email=email).first():
        flash(f'Email {email} is already registered.', 'danger')
        return redirect(url_for('admin_dashboard') + '#staff')

    if role == 'staff' and staff_id and User.query.filter_by(staff_id=staff_id).first():
        flash(f'Staff ID {staff_id} is already in use.', 'danger')
        return redirect(url_for('admin_dashboard') + '#staff')

    try:
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            phone_number=phone,
            email=email,
            age=int(age) if age.isdigit() else 30,
            password=hashed,
            role=role,
            staff_id=staff_id if role == 'staff' else None,
        )
        db.session.add(new_user)
        db.session.flush()

        if role == 'staff':
            profile = StaffProfile(
                user_id=new_user.id,
                role=job_role,
                salary=float(salary) if salary else 0.0,
                completed_duties=0,
                feedback_rating=0.0,
                reward_points=0,
            )
            db.session.add(profile)

        db.session.commit()
        flash(f'{role.capitalize()} "{first_name} {last_name}" created successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating user: {e}', 'danger')

    return redirect(url_for('admin_dashboard') + ('#admins' if role == 'admin' else '#staff'))


@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    """Delete an admin or staff member. Cannot delete yourself."""
    target = User.query.get_or_404(user_id)

    if target.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin_dashboard'))

    if target.role not in ('admin', 'staff'):
        flash('Only admin or staff accounts can be deleted here.', 'danger')
        return redirect(url_for('admin_dashboard'))

    try:
        # Remove staff profile + rosters first
        if target.staff_profile:
            StaffRoster.query.filter_by(staff_profile_id=target.staff_profile.id).delete()
            db.session.delete(target.staff_profile)
        db.session.delete(target)
        db.session.commit()
        flash(f'{target.role.capitalize()} "{target.first_name} {target.last_name}" deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {e}', 'danger')

    return redirect(url_for('admin_dashboard'))


# ---------------------------------------------------------------------------
# API — Seat availability (AJAX)
# ---------------------------------------------------------------------------
@app.route('/api/flights/<int:flight_id>/seats')
def api_flight_seats(flight_id):
    Flight.query.get_or_404(flight_id)  # 404 if flight doesn't exist
    Seat.generate_for_flight(flight_id)
    seats = Seat.query.filter_by(flight_id=flight_id).order_by(Seat.seat_number).all()
    return jsonify([{
        'seat_number': s.seat_number,
        'class_type': s.class_type,
        'is_available': s.is_available,
    } for s in seats])


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(403)
def forbidden(e):
    if request.path.startswith('/api/'):
        return jsonify(error='forbidden'), 403
    return render_template('errors/403.html'), 403


@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify(error='not found'), 404
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(e):
    db.session.rollback()
    app.logger.error(f'Server error: {e}')
    if request.path.startswith('/api/'):
        return jsonify(error='server error'), 500
    return render_template('errors/500.html'), 500