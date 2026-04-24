import os
from flask import (
    render_template, url_for, flash, redirect,
    request, jsonify, abort, send_from_directory
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

from models import User, Flight, Seat, Plane, Booking, StaffProfile

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
        login_type = form.login_type.data

        if login_type == 'staff':
            user = User.query.filter_by(staff_id=form.staff_id.data, role='staff').first()
        elif login_type == 'admin':
            # admin enters email (copied into email field by JS)
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

# ── HEALTH ──
@app.route('/health')
def health():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "ok", "db": "connected"})
    except Exception as e:
        return jsonify({"status": "error", "db": str(e)})

# ── DB STATUS (row counts per table) ──
@app.route('/db-status')
def db_status():
    try:
        from models import User, Flight, Plane, Booking, StaffProfile, Seat, Roster, Passenger, Ticket
        return jsonify({
            "status": "ok",
            "tables": {
                "users":          User.query.count(),
                "flights":        Flight.query.count(),
                "planes":         Plane.query.count(),
                "bookings":       Booking.query.count(),
                "staff_profiles": StaffProfile.query.count(),
                "seats":          Seat.query.count(),
                "rosters":        Roster.query.count(),
                "passengers":     Passenger.query.count(),
                "tickets":        Ticket.query.count(),
            },
            "admins":  [{"id": u.id, "name": f"{u.first_name} {u.last_name}", "email": u.email}
                        for u in User.query.filter_by(role='admin').all()],
            "staff_count":    User.query.filter_by(role='staff').count(),
            "customer_count": User.query.filter_by(role='customer').count(),
        })
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500

# ── FLIGHTS ──
@app.route('/flights/search', methods=['GET', 'POST'])
def search_flights():
    from flask import session
    form = FlightSearchForm()
    flights = []
    return_flights = []
    searched = False
    trip_type = 'one_way'
    return_date_str = None

    if request.method == 'POST':
        searched = True
        # Use raw form data as fallback in case WTForms validation is strict
        origin      = request.form.get('origin', '').strip()
        destination = request.form.get('destination', '').strip()
        date_str    = request.form.get('date', '').strip()
        trip_type   = request.form.get('trip_type', 'one_way').strip()
        return_date_str = request.form.get('return_date', '').strip()

        # Store in session for later use
        session['search_origin'] = origin
        session['search_destination'] = destination
        session['trip_type'] = trip_type
        session['return_date'] = return_date_str if trip_type == 'return' else None

        # Search outbound flights
        query = Flight.query
        if origin:
            query = query.filter(Flight.origin.ilike(f"%{origin}%"))
        if destination:
            query = query.filter(Flight.destination.ilike(f"%{destination}%"))
        if date_str:
            try:
                from datetime import date as date_type
                search_date = date_type.fromisoformat(date_str)
                query = query.filter(db.func.date(Flight.departure_time) == search_date)
            except ValueError:
                pass  # ignore invalid date format
        flights = query.all()

        # Search return flights if return trip
        if trip_type == 'return' and return_date_str and origin and destination:
            try:
                from datetime import date as date_type
                return_search_date = date_type.fromisoformat(return_date_str)
                return_query = Flight.query
                # Swap origin and destination for return
                return_query = return_query.filter(Flight.origin.ilike(f"%{destination}%"))
                return_query = return_query.filter(Flight.destination.ilike(f"%{origin}%"))
                return_query = return_query.filter(db.func.date(Flight.departure_time) == return_search_date)
                return_flights = return_query.all()
            except ValueError:
                pass

    elif request.method == 'GET':
        source      = request.args.get('source', '').strip()
        destination = request.args.get('destination', '').strip()
        date_str    = request.args.get('date', '').strip()
        if source or destination or date_str:
            searched = True
            query = Flight.query
            if source:
                query = query.filter(Flight.origin.ilike(f"%{source}%"))
            if destination:
                query = query.filter(Flight.destination.ilike(f"%{destination}%"))
            if date_str:
                try:
                    from datetime import date as date_type
                    search_date = date_type.fromisoformat(date_str)
                    query = query.filter(db.func.date(Flight.departure_time) == search_date)
                except ValueError:
                    pass
            flights = query.all()

    # Attach available seat count to each flight
    flight_data = []
    for f in flights:
        Seat.generate_for_flight(f.id)
        taken = Seat.query.filter_by(flight_id=f.id, is_available=False).count()
        total = Seat.query.filter_by(flight_id=f.id).count()
        available = total - taken
        flight_data.append({'flight': f, 'available': available, 'total': total, 'sold_out': available == 0})

    return_flight_data = []
    for f in return_flights:
        Seat.generate_for_flight(f.id)
        taken = Seat.query.filter_by(flight_id=f.id, is_available=False).count()
        total = Seat.query.filter_by(flight_id=f.id).count()
        available = total - taken
        return_flight_data.append({'flight': f, 'available': available, 'total': total, 'sold_out': available == 0})

    return render_template("search.html", flights=flight_data, return_flights=return_flight_data,
                           form=form, searched=searched, trip_type=trip_type, return_date=return_date_str,
                           now_date=utc_now().date().isoformat())

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

# ── STORE RETURN FLIGHT API ──
@app.route('/api/store-return-flight', methods=['POST'])
@login_required
def store_return_flight():
    from flask import session
    data = request.get_json()
    return_flight_id = data.get('return_flight_id')
    if return_flight_id:
        session['return_flight_id'] = return_flight_id
        return jsonify({'success': True})
    return jsonify({'success': False}), 400


# ── MY BOOKINGS ──
@app.route('/my-bookings')
@login_required
def my_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return render_template('my_bookings.html', bookings=bookings)

# ── STAFF DASHBOARD ──
@app.route('/staff/dashboard')
@login_required
def staff_dashboard():
    if current_user.role != 'staff':
        return redirect(url_for('home'))
    profile = current_user.staff_profile
    rosters = profile.rosters if profile else []
    return render_template('staff_dashboard.html', profile=profile, rosters=rosters)

# ── ADMIN DASHBOARD ──
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    planes        = Plane.query.all()
    staff_members = User.query.filter_by(role='staff').all()
    admin_users   = User.query.filter_by(role='admin').all()
    flights       = Flight.query.all()

    # Build enriched customer list with booking stats (what the template expects)
    raw_customers = User.query.filter_by(role='customer').all()
    customers = []
    for u in raw_customers:
        spent = sum(b.total_price for b in u.bookings)
        count = len(u.bookings)
        if spent >= 100000:
            loyalty = 'Gold'
        elif spent >= 40000:
            loyalty = 'Silver'
        else:
            loyalty = 'Bronze'
        customers.append({
            'user':          u,
            'booking_count': count,
            'total_spent':   spent,
            'loyalty':       loyalty,
        })

    in_flight   = sum(1 for p in planes if p.status == 'in_flight')
    on_ground   = sum(1 for p in planes if p.status == 'on_ground')
    maintenance = sum(1 for p in planes if p.status == 'maintenance')
    total_revenue = sum(b.total_price for b in Booking.query.all())

    kpis = {
        'planes':        len(planes),
        'in_flight':     in_flight,
        'on_ground':     on_ground,
        'maintenance':   maintenance,
        'flights':       len(flights),
        'staff':         len(staff_members),
        'customers':     len(raw_customers),
        'total_revenue': total_revenue,
    }

    # Use naive UTC now so it compares correctly with naive departure_time in DB
    now = datetime.utcnow()

    return render_template(
        'admin_dashboard.html',
        planes=planes,
        staff_members=staff_members,
        customers=customers,
        admin_users=admin_users,
        flights=flights,
        kpis=kpis,
        now=now,
    )

# ── ADMIN ADD FLIGHT ──
@app.route('/admin/flights/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_flight():
    planes = Plane.query.all()
    if request.method == 'POST':
        origin       = request.form.get('origin')
        destination  = request.form.get('destination')
        duration     = request.form.get('duration')
        departure    = request.form.get('departure_time')
        plane_id     = request.form.get('plane_id')

        try:
            dep_dt = datetime.strptime(departure, '%Y-%m-%dT%H:%M')
        except (ValueError, TypeError):
            flash("Invalid departure time format.", "danger")
            return render_template('admin_add_flight.html', planes=planes)

        flight = Flight(
            origin=origin,
            destination=destination,
            duration=duration,
            departure_time=dep_dt,
            plane_id=int(plane_id) if plane_id else None,
        )
        db.session.add(flight)
        db.session.commit()
        flash("Flight added successfully.", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template('admin_add_flight.html', planes=planes)

# ── ADMIN ASSIGN STAFF TO FLIGHT ──
@app.route('/admin/staff/<int:user_id>/assign', methods=['POST'])
@login_required
@admin_required
def admin_assign_flight(user_id):
    from models import Roster, StaffProfile
    staff_user = User.query.get_or_404(user_id)
    flight_id  = request.form.get('flight_id', type=int)
    hotel      = request.form.get('hotel', '').strip() or None
    travel_id  = request.form.get('travel_id', '').strip() or None

    if not flight_id:
        flash('Please select a flight.', 'danger')
        return redirect(url_for('admin_dashboard'))

    flight = Flight.query.get_or_404(flight_id)

    profile = staff_user.staff_profile
    if not profile:
        profile = StaffProfile(user_id=staff_user.id, role='Cabin Crew', salary=0)
        db.session.add(profile)
        db.session.flush()

    # Remove existing roster for this staff on this flight if duplicate
    existing = Roster.query.filter_by(
        staff_profile_id=profile.id, flight_id=flight_id
    ).first()
    if existing:
        flash(f'{staff_user.first_name} is already assigned to that flight.', 'warning')
        return redirect(url_for('admin_dashboard'))

    roster = Roster(
        staff_profile_id=profile.id,
        flight_id=flight_id,
        hotel=hotel or f'Hotel — {flight.destination.split("(")[0].strip()}',
        travel_id=travel_id or f'TRV-{profile.id:04d}',
    )
    db.session.add(roster)
    db.session.commit()
    flash(f'{staff_user.first_name} {staff_user.last_name} assigned to Flight #{flight_id} successfully.', 'success')
    return redirect(url_for('admin_dashboard'))


# ── ADMIN UNASSIGN STAFF FROM FLIGHT ──
@app.route('/admin/roster/<int:roster_id>/remove', methods=['POST'])
@login_required
@admin_required
def admin_remove_roster(roster_id):
    from models import Roster
    roster = Roster.query.get_or_404(roster_id)
    db.session.delete(roster)
    db.session.commit()
    flash('Roster assignment removed.', 'success')
    return redirect(url_for('admin_dashboard'))
@app.route('/admin/staff/<int:user_id>')
@login_required
@admin_required
def admin_staff_detail(user_id):
    staff_user = User.query.get_or_404(user_id)
    profile = staff_user.staff_profile
    rosters = profile.rosters if profile else []
    return render_template('admin_staff_detail.html', staff_user=staff_user, profile=profile, rosters=rosters)

# ── ADMIN CREATE USER (staff or admin) ──
@app.route('/admin/users/create', methods=['POST'])
@login_required
@admin_required
def admin_create_user():
    role       = request.form.get('role', 'staff')
    first_name = request.form.get('first_name', '').strip()
    last_name  = request.form.get('last_name', '').strip()
    email      = request.form.get('email', '').strip()
    phone      = request.form.get('phone', '').strip()
    staff_id   = request.form.get('staff_id', '').strip() or None
    password   = request.form.get('password', 'changeme123').strip()
    age        = int(request.form.get('age') or 30)
    job_role   = request.form.get('job_role', 'Cabin Crew')
    salary     = float(request.form.get('salary') or 0)

    if not first_name or not last_name or not email or not phone:
        flash('Please fill in all required fields.', 'danger')
        return redirect(url_for('admin_dashboard'))

    if len(phone) != 11 or not phone.isdigit():
        flash('Phone number must be exactly 11 digits.', 'danger')
        return redirect(url_for('admin_dashboard'))

    if User.query.filter_by(email=email).first():
        flash(f'Email {email} is already registered.', 'danger')
        return redirect(url_for('admin_dashboard'))

    if User.query.filter_by(phone_number=phone).first():
        flash(f'Phone number {phone} is already registered.', 'danger')
        return redirect(url_for('admin_dashboard'))

    if role == 'staff' and staff_id and User.query.filter_by(staff_id=staff_id).first():
        flash(f'Staff ID {staff_id} is already taken.', 'danger')
        return redirect(url_for('admin_dashboard'))

    try:
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(
            first_name=first_name, last_name=last_name,
            email=email, phone_number=phone,
            age=age, password=hashed_pw,
            role=role,
            staff_id=staff_id if role == 'staff' else None,
        )
        db.session.add(user)
        db.session.flush()

        if role == 'staff':
            from models import StaffProfile
            profile = StaffProfile(user_id=user.id, role=job_role, salary=salary)
            db.session.add(profile)

        db.session.commit()
        flash(f'{role.capitalize()} account for {first_name} {last_name} created successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating account: {str(e)}', 'danger')

    return redirect(url_for('admin_dashboard'))

# ── ADMIN DELETE USER ──
@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    if user_id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin_dashboard'))
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'Account for {user.first_name} {user.last_name} deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

# ── VIEW TICKET ──
@app.route('/ticket/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    from models import Ticket
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.booking.user_id != current_user.id and current_user.role not in ('admin', 'staff'):
        abort(403)
    return render_template('ticket.html', ticket=ticket, booking=ticket.booking)

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

# ── FAVICON ──
@app.route('/favicon.ico')
@app.route('/favicon.png')
def favicon():
    return send_from_directory(
        app.static_folder, 'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

# ── BOOKING FLOW ──
from forms import PackageSelectionForm, PassengerDetailsForm
from models import Booking, Passenger, Ticket

@app.route('/flights/<int:flight_id>/package', methods=['GET', 'POST'])
@login_required
def select_package(flight_id):
    from flask import session
    flight = Flight.query.get_or_404(flight_id)

    # Block if fully booked
    Seat.generate_for_flight(flight_id)
    available = Seat.query.filter_by(flight_id=flight_id, is_available=True).count()
    if available == 0:
        flash('Sorry, this flight is fully booked.', 'danger')
        return redirect(url_for('search_flights'))

    # Get trip type and return info from session
    trip_type = session.get('trip_type', 'one_way')
    return_date = session.get('return_date')
    return_flight_id = session.get('return_flight_id')

    form = PackageSelectionForm()
    if form.validate_on_submit():
        # Store package tier in session
        session['package_tier'] = form.package_tier.data
        return redirect(url_for('passenger_details', flight_id=flight_id, tier=form.package_tier.data))
    
    return render_template('packages.html', flight=flight, form=form, 
                         trip_type=trip_type, return_date=return_date)


@app.route('/flights/<int:flight_id>/passengers', methods=['GET', 'POST'])
@login_required
def passenger_details(flight_id):
    from flask import session
    flight = Flight.query.get_or_404(flight_id)
    tier = request.args.get('tier', 'Economy')
    form = PassengerDetailsForm()
    
    # Get trip type and return flight from session
    trip_type = session.get('trip_type', 'one_way')
    return_flight_id = session.get('return_flight_id')
    return_flight = None
    return_seat_rows = []
    
    if trip_type == 'return' and return_flight_id:
        return_flight = Flight.query.get(return_flight_id)

    if request.method == 'POST':
        # validate CSRF token
        form.validate()  # runs CSRF check; ignore other field errors
        passengers_count = int(request.form.get('passengers_count', 1))
        
        # Outbound passengers
        passengers = []
        for i in range(passengers_count):
            passengers.append({
                'first_name':      request.form.get(f'first_name_{i}', f'Passenger {i+1}'),
                'last_name':       request.form.get(f'last_name_{i}', ''),
                'seat_number':     request.form.get(f'seat_number_{i}', ''),
                'meal_preference': request.form.get(f'meal_preference_{i}', 'None'),
            })
        
        # Return passengers (if return trip)
        return_passengers = []
        if trip_type == 'return' and return_flight_id:
            for i in range(passengers_count):
                return_passengers.append({
                    'first_name':      request.form.get(f'first_name_{i}', f'Passenger {i+1}'),  # Same names
                    'last_name':       request.form.get(f'last_name_{i}', ''),
                    'seat_number':     request.form.get(f'return_seat_number_{i}', ''),  # Different seats
                    'meal_preference': request.form.get(f'return_meal_preference_{i}', 'None'),
                })
        
        # Store in session
        session['booking_passengers'] = passengers
        session['return_passengers'] = return_passengers
        session['booking_tier'] = tier
        return redirect(url_for('checkout', flight_id=flight_id, tier=tier))

    # Build seat rows for OUTBOUND flight
    Seat.generate_for_flight(flight_id)
    seats = Seat.query.filter_by(flight_id=flight_id).order_by(Seat.seat_number).all()

    # Mark seats already taken by confirmed bookings on this flight
    taken_seats = set(
        p.seat_number
        for b in Booking.query.filter_by(flight_id=flight_id).all()
        for p in b.passengers
        if p.seat_number
    )
    for s in seats:
        if s.seat_number in taken_seats:
            s.is_available = False

    from collections import defaultdict
    rows = defaultdict(list)
    for s in seats:
        row_num = int(''.join(filter(str.isdigit, s.seat_number)))
        s.col = ''.join(filter(str.isalpha, s.seat_number))
        s.number = s.seat_number
        rows[row_num].append(s)

    seat_rows = sorted(rows.items())
    
    # Build seat rows for RETURN flight (if applicable)
    if trip_type == 'return' and return_flight_id:
        Seat.generate_for_flight(return_flight_id)
        return_seats = Seat.query.filter_by(flight_id=return_flight_id).order_by(Seat.seat_number).all()
        
        # Mark taken seats for return flight
        return_taken_seats = set(
            p.seat_number
            for b in Booking.query.filter_by(flight_id=return_flight_id).all()
            for p in b.passengers
            if p.seat_number
        )
        for s in return_seats:
            if s.seat_number in return_taken_seats:
                s.is_available = False
        
        return_rows = defaultdict(list)
        for s in return_seats:
            row_num = int(''.join(filter(str.isdigit, s.seat_number)))
            s.col = ''.join(filter(str.isalpha, s.seat_number))
            s.number = s.seat_number
            return_rows[row_num].append(s)
        
        return_seat_rows = sorted(return_rows.items())

    return render_template(
        'passengers.html',
        flight=flight,
        return_flight=return_flight,
        form=form,
        package_tier=tier,
        seat_rows=seat_rows,
        return_seat_rows=return_seat_rows,
        trip_type=trip_type,
    )


PACKAGE_PRICES = {'Basic': 19000, 'Economy': 24000, 'Premium': 30000}

@app.route('/flights/<int:flight_id>/checkout', methods=['GET', 'POST'])
@login_required
def checkout(flight_id):
    from flask import session
    flight = Flight.query.get_or_404(flight_id)
    tier = request.args.get('tier', session.get('booking_tier', 'Economy'))
    passengers = session.get('booking_passengers', [])
    
    # Get trip type and return flight from session
    trip_type = session.get('trip_type', 'one_way')
    return_flight_id = session.get('return_flight_id')
    return_passengers = session.get('return_passengers', [])

    payment_method_choices = {
        'card': 'Credit / Debit Card',
        'easypaisa': 'EasyPaisa',
        'jazzcash': 'JazzCash',
        'bank_transfer': 'Bank Transfer',
    }

    if request.method == 'POST':
        payment_method = request.form.get('payment_method', 'card')
        
        price_per_pax = PACKAGE_PRICES.get(tier, 24000)
        
        # Calculate total based on trip type
        if trip_type == 'return' and return_flight_id:
            # For return trips: price per passenger * 2 (outbound + return)
            total = price_per_pax * len(passengers) * 2
        else:
            total = price_per_pax * len(passengers)

        # Create outbound booking
        booking = Booking(
            user_id=current_user.id,
            flight_id=flight_id,
            package_tier=tier,
            trip_type=trip_type,
            payment_method=payment_method,
            status='confirmed',
            total_price=price_per_pax * len(passengers),
        )
        db.session.add(booking)
        db.session.flush()

        # Add passengers for outbound flight
        for p in passengers:
            db.session.add(Passenger(
                booking_id=booking.id,
                first_name=p['first_name'],
                last_name=p['last_name'],
                seat_number=p['seat_number'],
            ))
            # Mark seat as taken
            if p['seat_number']:
                seat = Seat.query.filter_by(
                    flight_id=flight_id,
                    seat_number=p['seat_number']
                ).first()
                if seat:
                    seat.is_available = False

        # Create outbound ticket
        ticket = Ticket(booking_id=booking.id)
        db.session.add(ticket)
        
        # If return trip, create return booking
        return_ticket = None
        if trip_type == 'return' and return_flight_id:
            return_booking = Booking(
                user_id=current_user.id,
                flight_id=return_flight_id,
                package_tier=tier,
                trip_type='return',
                payment_method=payment_method,
                status='confirmed',
                total_price=price_per_pax * len(passengers),
            )
            db.session.add(return_booking)
            db.session.flush()

            # Add same passengers for return flight
            for p in return_passengers if return_passengers else passengers:
                db.session.add(Passenger(
                    booking_id=return_booking.id,
                    first_name=p['first_name'],
                    last_name=p['last_name'],
                    seat_number=p.get('seat_number', ''),
                ))
                # Mark return seat as taken
                if p.get('seat_number'):
                    seat = Seat.query.filter_by(
                        flight_id=return_flight_id,
                        seat_number=p['seat_number']
                    ).first()
                    if seat:
                        seat.is_available = False

            # Create return ticket
            return_ticket = Ticket(booking_id=return_booking.id)
            db.session.add(return_ticket)

        db.session.commit()

        # Clear session
        session.pop('booking_passengers', None)
        session.pop('booking_tier', None)
        session.pop('return_passengers', None)
        session.pop('return_flight_id', None)

        if trip_type == 'return' and return_ticket:
            flash(f"Booking confirmed! Your tickets have been issued (Outbound + Return).", "success")
        else:
            flash("Booking confirmed! Your ticket has been issued.", "success")
        
        return redirect(url_for('view_ticket', ticket_id=ticket.id))

    # Build passenger preview objects
    class PaxPreview:
        def __init__(self, d):
            self.first_name = d.get('first_name', '')
            self.last_name = d.get('last_name', '')
            self.seat_number = d.get('seat_number', '')
            self.meal_preference = d.get('meal_preference', 'None')

    pax_preview = [PaxPreview(p) for p in passengers]
    return_pax_preview = [PaxPreview(p) for p in return_passengers] if return_passengers else []
    price_per_pax = PACKAGE_PRICES.get(tier, 24000)
    
    # Calculate total price
    if trip_type == 'return':
        total_price = price_per_pax * max(len(pax_preview), 1) * 2
    else:
        total_price = price_per_pax * max(len(pax_preview), 1)
    
    # Get return flight if applicable
    return_flight = None
    if trip_type == 'return' and return_flight_id:
        return_flight = Flight.query.get(return_flight_id)

    return render_template(
        'checkout.html',
        flight=flight,
        return_flight=return_flight,
        package_tier=tier,
        passengers=pax_preview,
        return_passengers=return_pax_preview,
        trip_type=trip_type,
        return_date=session.get('return_date'),
        total_price=total_price,
        selected_payment_method='card',
        payment_method_choices=payment_method_choices,
    )

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
