import os
from flask import (
    render_template, url_for, flash, redirect,
    request, jsonify, abort, send_from_directory
)
from functools import wraps
from sqlalchemy import text
from datetime import datetime, timezone, timedelta

from flask_login import login_user, current_user, login_required, logout_user

from app import app, db, bcrypt

from forms import (
    CustomerRegistrationForm,
    LoginForm,
    FlightSearchForm
)

from models import User, Flight, Seat, Plane, Booking, StaffProfile, SeatLock, PaymentTransaction

# ── UTILS ──
def utc_now():
    return datetime.now(timezone.utc)

# ── ROLLING 30-DAY FLIGHT SCHEDULE ──
_last_schedule_refresh = None

def ensure_30_day_schedule():
    """
    Rolling 30-day flight schedule.
    - Marks past flights as 'landed'
    - For each route, ensures daily flights exist for the next 30 days
    """
    global _last_schedule_refresh
    now = datetime.utcnow()

    # Throttle: run at most once per hour
    if _last_schedule_refresh and (now - _last_schedule_refresh).total_seconds() < 3600:
        return 0

    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 1) Mark past on_time flights as 'landed'
    Flight.query.filter(
        Flight.departure_time < now,
        Flight.status == 'on_time'
    ).update({'status': 'landed'}, synchronize_session=False)
    db.session.flush()

    # 2) Collect route templates from existing flights
    #    Group by (origin, destination) → pick up to 2 daily time-slots
    all_flights = Flight.query.all()
    route_map = {}  # (origin, dest) -> set of (hour, minute, duration, plane_id)

    for f in all_flights:
        key = (f.origin, f.destination)
        tmpl = (f.departure_time.hour, f.departure_time.minute, f.duration, f.plane_id)
        route_map.setdefault(key, set()).add(tmpl)

    # 3) For each route keep max 2 unique departure hours, fill 30 days
    created = 0
    for (origin, dest), templates in route_map.items():
        # Deduplicate by hour, keep first 2
        seen_hours = {}
        for h, m, dur, pid in sorted(templates):
            if h not in seen_hours and len(seen_hours) < 2:
                seen_hours[h] = (m, dur, pid)

        for hour, (minute, duration, plane_id) in seen_hours.items():
            for day_offset in range(31):
                dep = today + timedelta(days=day_offset, hours=hour, minutes=minute)
                if dep <= now:
                    continue  # don't create flights in the past

                exists = db.session.query(Flight.id).filter_by(
                    origin=origin,
                    destination=dest,
                    departure_time=dep,
                ).first()

                if not exists:
                    db.session.add(Flight(
                        origin=origin,
                        destination=dest,
                        duration=duration,
                        departure_time=dep,
                        plane_id=plane_id,
                        status='on_time',
                    ))
                    created += 1

    db.session.commit()
    _last_schedule_refresh = now
    return created

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
        from models import User, Flight, Plane, Booking, StaffProfile, Seat, Roster, Passenger, Ticket, SeatLock, PaymentTransaction
        return jsonify({
            "status": "ok",
            "tables": {
                "users":                User.query.count(),
                "flights":              Flight.query.count(),
                "planes":               Plane.query.count(),
                "bookings":             Booking.query.count(),
                "bookings_confirmed":   Booking.query.filter_by(payment_status='confirmed').count(),
                "bookings_pending":     Booking.query.filter_by(payment_status='pending').count(),
                "bookings_failed":      Booking.query.filter_by(payment_status='failed').count(),
                "staff_profiles":       StaffProfile.query.count(),
                "seats":                Seat.query.count(),
                "seat_locks_active":    SeatLock.query.filter(SeatLock.expires_at > datetime.utcnow()).count(),
                "payment_transactions": PaymentTransaction.query.count(),
                "rosters":              Roster.query.count(),
                "passengers":           Passenger.query.count(),
                "tickets":              Ticket.query.count(),
            },
            "admins":  [{"id": u.id, "name": f"{u.first_name} {u.last_name}", "email": u.email}
                        for u in User.query.filter_by(role='admin').all()],
            "staff_count":    User.query.filter_by(role='staff').count(),
            "customer_count": User.query.filter_by(role='customer').count(),
        })
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500

@app.route('/airplane-3d')
def airplane_3d():
    """3D Airplane Experience Page"""
    return render_template('airplane_3d_integrated.html')

@app.route('/airplane-3d/<int:flight_id>')
def airplane_3d_flight(flight_id):
    """3D Airplane Experience for specific flight"""
    flight = Flight.query.get_or_404(flight_id)
    
    # Get seat availability for this flight
    seats = Seat.query.filter_by(flight_id=flight_id).all()
    seat_data = []
    for seat in seats:
        seat_data.append({
            'seat_number': seat.seat_number,
            'class_type': seat.class_type,
            'is_available': seat.is_available
        })
    
    return render_template('airplane_3d_integrated.html', flight=flight, seats=seat_data)

# ── FLIGHTS ──
@app.route('/flights/search', methods=['GET', 'POST'])
def search_flights():
    form = FlightSearchForm()
    outbound_flights = []
    return_flights = []
    searched = False
    trip_type = 'one_way'  # Default

    if request.method == 'POST':
        searched = True
        # Get form data
        origin = request.form.get('origin', '').strip()
        destination = request.form.get('destination', '').strip()
        date_str = request.form.get('date', '').strip()
        trip_type = request.form.get('trip_type', 'one_way').strip()
        return_date_str = request.form.get('return_date', '').strip()

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
                pass
        outbound_flights = query.all()

        # Search return flights if round trip
        if trip_type == 'return' and return_date_str and origin and destination:
            return_query = Flight.query
            # Swap origin and destination for return flights
            return_query = return_query.filter(Flight.origin.ilike(f"%{destination}%"))
            return_query = return_query.filter(Flight.destination.ilike(f"%{origin}%"))
            try:
                return_search_date = date_type.fromisoformat(return_date_str)
                return_query = return_query.filter(db.func.date(Flight.departure_time) == return_search_date)
                return_flights = return_query.all()
            except ValueError:
                pass

    elif request.method == 'GET':
        source = request.args.get('source', '').strip()
        destination = request.args.get('destination', '').strip()
        date_str = request.args.get('date', '').strip()
        trip_type = request.args.get('trip_type', 'one_way').strip()
        return_date_str = request.args.get('return_date', '').strip()
        
        if source or destination or date_str:
            searched = True
            
            # Search outbound flights
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
            outbound_flights = query.all()

            # Search return flights if round trip
            if trip_type == 'return' and return_date_str and source and destination:
                return_query = Flight.query
                return_query = return_query.filter(Flight.origin.ilike(f"%{destination}%"))
                return_query = return_query.filter(Flight.destination.ilike(f"%{source}%"))
                try:
                    return_search_date = date_type.fromisoformat(return_date_str)
                    return_query = return_query.filter(db.func.date(Flight.departure_time) == return_search_date)
                    return_flights = return_query.all()
                except ValueError:
                    pass

    # Process outbound flights
    outbound_flight_data = []
    for f in outbound_flights:
        Seat.generate_for_flight(f.id)
        taken = Seat.query.filter_by(flight_id=f.id, is_available=False).count()
        total = Seat.query.filter_by(flight_id=f.id).count()
        available = total - taken
        outbound_flight_data.append({
            'flight': f, 
            'available': available, 
            'total': total, 
            'sold_out': available == 0
        })

    # Process return flights
    return_flight_data = []
    for f in return_flights:
        Seat.generate_for_flight(f.id)
        taken = Seat.query.filter_by(flight_id=f.id, is_available=False).count()
        total = Seat.query.filter_by(flight_id=f.id).count()
        available = total - taken
        return_flight_data.append({
            'flight': f, 
            'available': available, 
            'total': total, 
            'sold_out': available == 0
        })

    return render_template("search.html", 
                         outbound_flights=outbound_flight_data,
                         return_flights=return_flight_data,
                         form=form, 
                         searched=searched,
                         trip_type=trip_type,
                         now_date=utc_now().date().isoformat())

# ── SEATS API ──
@app.route('/api/flights/<int:flight_id>/seats')
def api_seats(flight_id):
    Flight.query.get_or_404(flight_id)
    Seat.generate_for_flight(flight_id)

    # Clean up expired locks first
    SeatLock.cleanup_expired()
    db.session.commit()

    seats = Seat.query.filter_by(flight_id=flight_id).all()

    # Seats locked by others (not current user)
    exclude_uid = current_user.id if current_user.is_authenticated else None
    now = datetime.utcnow()
    locked_by_others = set(
        sl.seat_number for sl in SeatLock.query.filter_by(flight_id=flight_id).filter(
            SeatLock.expires_at > now,
            SeatLock.user_id != exclude_uid if exclude_uid else True
        ).all()
    )

    return jsonify([
        {
            "seat_number": s.seat_number,
            "class_type": s.class_type,
            "is_available": s.is_available and s.seat_number not in locked_by_others,
            "locked": s.seat_number in locked_by_others,
        }
        for s in seats
    ])


# ── SEAT LOCK API ──
@app.route('/api/flights/<int:flight_id>/seats/lock', methods=['POST'])
@login_required
def api_lock_seats(flight_id):
    """Lock seats for the current user for LOCK_MINUTES minutes."""
    from models import SeatLock
    Flight.query.get_or_404(flight_id)
    data = request.get_json(force=True)
    seat_numbers = data.get('seats', [])

    if not seat_numbers:
        return jsonify({'ok': False, 'error': 'No seats provided'}), 400

    SeatLock.cleanup_expired()

    now = datetime.utcnow()
    expires = now + timedelta(minutes=SeatLock.LOCK_MINUTES)
    conflicts = []

    for sn in seat_numbers:
        # Check if permanently booked
        seat = Seat.query.filter_by(flight_id=flight_id, seat_number=sn).first()
        if not seat or not seat.is_available:
            conflicts.append(sn)
            continue
        # Check if locked by someone else
        existing = SeatLock.query.filter_by(flight_id=flight_id, seat_number=sn).filter(
            SeatLock.expires_at > now,
            SeatLock.user_id != current_user.id
        ).first()
        if existing:
            conflicts.append(sn)

    if conflicts:
        return jsonify({'ok': False, 'conflicts': conflicts,
                        'error': f'Seats {", ".join(conflicts)} are no longer available'}), 409

    # Remove any existing locks by this user on this flight
    SeatLock.query.filter_by(flight_id=flight_id, user_id=current_user.id).delete()

    for sn in seat_numbers:
        db.session.add(SeatLock(
            flight_id=flight_id,
            seat_number=sn,
            user_id=current_user.id,
            locked_at=now,
            expires_at=expires,
        ))

    db.session.commit()
    return jsonify({'ok': True, 'expires_at': expires.isoformat(), 'lock_minutes': SeatLock.LOCK_MINUTES})


# ── SEAT UNLOCK API ──
@app.route('/api/flights/<int:flight_id>/seats/unlock', methods=['POST'])
@login_required
def api_unlock_seats(flight_id):
    """Release seat locks held by the current user."""
    SeatLock.query.filter_by(flight_id=flight_id, user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({'ok': True})


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
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Show 20 flights per page
    
    # Use efficient queries with minimal data loading
    now = datetime.utcnow()
    
    # Get counts efficiently with separate simple queries
    total_flights = Flight.query.count()
    upcoming_flights = Flight.query.filter(Flight.departure_time >= now).count()
    staff_count = User.query.filter_by(role='staff').count()
    customer_count = User.query.filter_by(role='customer').count()
    plane_count = Plane.query.count()
    
    # Get revenue efficiently
    total_revenue = db.session.query(
        db.func.coalesce(db.func.sum(Booking.total_price), 0)
    ).filter_by(payment_status='confirmed').scalar() or 0
    
    # Get plane status counts efficiently
    plane_status_counts = dict(db.session.query(
        Plane.status, db.func.count(Plane.id)
    ).group_by(Plane.status).all())
    
    # Paginate flights efficiently - only get what we need
    flights_pagination = Flight.query.filter(
        Flight.departure_time >= now
    ).order_by(Flight.departure_time.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    flights = flights_pagination.items
    
    # Get limited data for dropdowns and displays
    planes = Plane.query.limit(20).all()  # Limit for performance
    staff_members = User.query.filter_by(role='staff').limit(20).all()
    admin_users = User.query.filter_by(role='admin').all()
    
    # Get upcoming flights for assignment modal (limit to next 50)
    all_upcoming_flights = Flight.query.filter(
        Flight.departure_time >= now
    ).order_by(Flight.departure_time.asc()).limit(50).all()

    # Build limited customer list for display (simplified)
    raw_customers = User.query.filter_by(role='customer').limit(10).all()
    customers = []
    for u in raw_customers:
        # Simple approach - just show basic info without complex calculations
        customers.append({
            'user': u,
            'booking_count': 0,  # Skip expensive calculation for now
            'total_spent': 0,    # Skip expensive calculation for now
            'loyalty': 'Bronze',
        })

    kpis = {
        'planes': plane_count,
        'in_flight': plane_status_counts.get('in_flight', 0),
        'on_ground': plane_status_counts.get('on_ground', 0),
        'maintenance': plane_status_counts.get('maintenance', 0),
        'flights': total_flights,
        'upcoming_flights': upcoming_flights,
        'staff': staff_count,
        'customers': customer_count,
        'total_revenue': float(total_revenue),
    }

    return render_template(
        'admin_dashboard.html',
        planes=planes,
        staff_members=staff_members,
        customers=customers,
        admin_users=admin_users,
        flights=flights,
        all_flights=all_upcoming_flights,
        flights_pagination=flights_pagination,
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
    name = f'{user.first_name} {user.last_name}'
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'Account for {name} deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Could not delete {name}: {str(e)}', 'danger')
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


# ── CANCEL BOOKING ──
@app.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id and current_user.role != 'admin':
        abort(403)
    if booking.status == 'cancelled':
        flash('This booking is already cancelled.', 'warning')
        return redirect(url_for('my_bookings'))
    if booking.status == 'confirmed':
        # Release seats
        for p in booking.passengers:
            if p.seat_number:
                seat = Seat.query.filter_by(
                    flight_id=booking.flight_id, seat_number=p.seat_number
                ).first()
                if seat:
                    seat.is_available = True
        # Cancel ticket
        if booking.ticket:
            booking.ticket.status = 'cancelled'
    booking.status = 'cancelled'
    booking.payment_status = 'failed'
    db.session.commit()
    flash('Your booking has been cancelled and seats released.', 'success')
    return redirect(url_for('my_bookings'))

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
    flight = Flight.query.get_or_404(flight_id)

    # Block if fully booked
    Seat.generate_for_flight(flight_id)
    available = Seat.query.filter_by(flight_id=flight_id, is_available=True).count()
    if available == 0:
        flash('Sorry, this flight is fully booked.', 'danger')
        return redirect(url_for('search_flights'))

    # Handle direct package selection via query parameter (from button clicks)
    tier = request.args.get('tier')
    if tier and tier in ['Basic', 'Economy', 'Premium']:
        # Store tier in session and redirect directly to passenger details (seat selection)
        from flask import session
        session['booking_tier'] = tier
        return redirect(url_for('passenger_details', flight_id=flight_id, tier=tier))

    form = PackageSelectionForm()
    if form.validate_on_submit():
        return redirect(url_for('passenger_details', flight_id=flight_id, tier=form.package_tier.data))
    return render_template('packages.html', flight=flight, form=form)


@app.route('/flights/<int:flight_id>/passengers', methods=['GET', 'POST'])
@login_required
def passenger_details(flight_id):
    flight = Flight.query.get_or_404(flight_id)
    tier = request.args.get('tier', 'Economy')
    form = PassengerDetailsForm()

    if request.method == 'POST':
        # validate CSRF token
        form.validate()  # runs CSRF check; ignore other field errors
        passengers_count = int(request.form.get('passengers_count', 1))
        passengers = []
        seat_numbers = []
        for i in range(passengers_count):
            sn = request.form.get(f'seat_number_{i}', '')
            passengers.append({
                'first_name':      request.form.get(f'first_name_{i}', f'Passenger {i+1}'),
                'last_name':       request.form.get(f'last_name_{i}', ''),
                'seat_number':     sn,
                'meal_preference': request.form.get(f'meal_preference_{i}', 'None'),
            })
            if sn:
                seat_numbers.append(sn)

        # ── Server-side seat validation ──
        if tier != 'Basic' and seat_numbers:
            SeatLock.cleanup_expired()
            now = datetime.utcnow()
            for sn in seat_numbers:
                seat = Seat.query.filter_by(flight_id=flight_id, seat_number=sn).first()
                if not seat or not seat.is_available:
                    flash(f'Seat {sn} is no longer available. Please choose another.', 'danger')
                    return redirect(url_for('passenger_details', flight_id=flight_id, tier=tier))
                locked_by_other = SeatLock.query.filter_by(
                    flight_id=flight_id, seat_number=sn
                ).filter(
                    SeatLock.expires_at > now,
                    SeatLock.user_id != current_user.id
                ).first()
                if locked_by_other:
                    flash(f'Seat {sn} was just taken by another passenger. Please choose another.', 'danger')
                    return redirect(url_for('passenger_details', flight_id=flight_id, tier=tier))

        # Store in session so checkout can read it
        from flask import session
        session['booking_passengers'] = passengers
        session['booking_tier'] = tier
        return redirect(url_for('checkout', flight_id=flight_id, tier=tier))

    # Build seat rows for the cabin map
    Seat.generate_for_flight(flight_id)
    SeatLock.cleanup_expired()
    db.session.commit()

    seats = Seat.query.filter_by(flight_id=flight_id).order_by(Seat.seat_number).all()

    # Seats locked by others
    now = datetime.utcnow()
    locked_by_others = set(
        sl.seat_number for sl in SeatLock.query.filter_by(flight_id=flight_id).filter(
            SeatLock.expires_at > now,
            SeatLock.user_id != current_user.id
        ).all()
    )

    # Mark seats already taken by confirmed bookings on this flight
    taken_seats = set(
        p.seat_number
        for b in Booking.query.filter_by(flight_id=flight_id).filter(
            Booking.payment_status == 'confirmed'
        ).all()
        for p in b.passengers
        if p.seat_number
    )
    for s in seats:
        if s.seat_number in taken_seats or s.seat_number in locked_by_others:
            s.is_available = False

    from collections import defaultdict
    rows = defaultdict(list)
    for s in seats:
        row_num = int(''.join(filter(str.isdigit, s.seat_number)))
        s.col = ''.join(filter(str.isalpha, s.seat_number))
        s.number = s.seat_number
        rows[row_num].append(s)

    seat_rows = sorted(rows.items())

    return render_template(
        'passengers.html',
        flight=flight,
        form=form,
        package_tier=tier,
        seat_rows=seat_rows,
        lock_minutes=SeatLock.LOCK_MINUTES,
    )


PACKAGE_PRICES = {'Basic': 19000, 'Economy': 24000, 'Premium': 30000}

# ── PAYMENT SIMULATION ──
import random
import string

def _simulate_payment(method: str, amount: float):
    """
    Fake payment gateway.
    Returns (status, failure_reason).
    - card:          95% success
    - jazzcash:      90% success
    - easypaisa:     90% success
    - bank_transfer: always pending (manual review)
    """
    if method == 'bank_transfer':
        return 'pending', None

    success_rates = {'card': 0.95, 'jazzcash': 0.90, 'easypaisa': 0.90}
    rate = success_rates.get(method, 0.90)

    if random.random() < rate:
        return 'confirmed', None
    else:
        reasons = [
            'Insufficient funds',
            'Card declined by issuing bank',
            'Transaction limit exceeded',
            'Network timeout — please retry',
        ]
        return 'failed', random.choice(reasons)

def _generate_gateway_ref():
    return 'GW-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def _generate_ticket_number(booking_id: int) -> str:
    return f'SS{booking_id:06d}-{"".join(random.choices(string.digits, k=4))}'


@app.route('/flights/<int:flight_id>/checkout', methods=['GET', 'POST'])
@login_required
def checkout(flight_id):
    from flask import session
    flight = Flight.query.get_or_404(flight_id)
    tier = request.args.get('tier', session.get('booking_tier', 'Economy'))
    passengers = session.get('booking_passengers', [])

    if not passengers:
        flash('Session expired. Please re-enter passenger details.', 'warning')
        return redirect(url_for('passenger_details', flight_id=flight_id, tier=tier))

    payment_method_choices = {
        'card': 'Credit / Debit Card',
        'easypaisa': 'EasyPaisa',
        'jazzcash': 'JazzCash',
        'bank_transfer': 'Bank Transfer',
    }

    if request.method == 'POST':
        payment_method = request.form.get('payment_method', 'card')
        trip_type = request.form.get('trip_type', 'one_way')
        return_date = request.form.get('return_date')

        price_per_pax = PACKAGE_PRICES.get(tier, 24000)
        multiplier = 2 if trip_type == 'return' else 1
        total = price_per_pax * len(passengers) * multiplier

        # ── Duplicate booking guard ──
        existing = Booking.query.filter_by(
            user_id=current_user.id,
            flight_id=flight_id,
            payment_status='confirmed',
        ).first()
        if existing:
            flash('You already have a confirmed booking on this flight.', 'warning')
            return redirect(url_for('my_bookings'))

        # ── Re-validate seat availability + locks ──
        seat_numbers = [p['seat_number'] for p in passengers if p.get('seat_number')]
        if tier != 'Basic' and seat_numbers:
            SeatLock.cleanup_expired()
            now = datetime.utcnow()
            for sn in seat_numbers:
                seat = Seat.query.filter_by(flight_id=flight_id, seat_number=sn).first()
                if not seat or not seat.is_available:
                    flash(f'Seat {sn} was booked by someone else. Please go back and choose a different seat.', 'danger')
                    return redirect(url_for('passenger_details', flight_id=flight_id, tier=tier))
                locked_by_other = SeatLock.query.filter_by(
                    flight_id=flight_id, seat_number=sn
                ).filter(
                    SeatLock.expires_at > now,
                    SeatLock.user_id != current_user.id
                ).first()
                if locked_by_other:
                    flash(f'Seat {sn} was just locked by another passenger. Please go back and choose a different seat.', 'danger')
                    return redirect(url_for('passenger_details', flight_id=flight_id, tier=tier))

        # ── Create booking in pending state ──
        try:
            now = datetime.utcnow()
            booking = Booking(
                user_id=current_user.id,
                flight_id=flight_id,
                package_tier=tier,
                trip_type=trip_type,
                return_date=return_date,
                payment_method=payment_method,
                status='pending',
                payment_status='pending',
                total_price=total,
                hold_expires_at=now + timedelta(minutes=10),
            )
            db.session.add(booking)
            db.session.flush()  # get booking.id

            for p in passengers:
                db.session.add(Passenger(
                    booking_id=booking.id,
                    first_name=p['first_name'],
                    last_name=p['last_name'],
                    seat_number=p.get('seat_number', ''),
                    meal_preference=p.get('meal_preference', 'None'),
                ))

            # ── Simulate payment ──
            pay_status, fail_reason = _simulate_payment(payment_method, total)
            gateway_ref = _generate_gateway_ref()

            txn = PaymentTransaction(
                booking_id=booking.id,
                amount=total,
                method=payment_method,
                status=pay_status,
                gateway_ref=gateway_ref,
                failure_reason=fail_reason,
            )
            db.session.add(txn)

            if pay_status == 'confirmed':
                booking.status = 'confirmed'
                booking.payment_status = 'confirmed'
                # Mark seats as permanently taken
                for p in passengers:
                    sn = p.get('seat_number', '')
                    if sn:
                        seat = Seat.query.filter_by(flight_id=flight_id, seat_number=sn).first()
                        if seat:
                            seat.is_available = False
                # Issue ticket
                ticket = Ticket(
                    booking_id=booking.id,
                    ticket_number=_generate_ticket_number(booking.id),
                    status='issued',
                )
                db.session.add(ticket)
                # Release seat locks
                SeatLock.query.filter_by(flight_id=flight_id, user_id=current_user.id).delete()
                db.session.commit()
                session.pop('booking_passengers', None)
                session.pop('booking_tier', None)
                flash('Payment confirmed! Your ticket has been issued.', 'success')
                return redirect(url_for('view_ticket', ticket_id=ticket.id))

            elif pay_status == 'pending':
                # Bank transfer — hold seats, await manual confirmation
                for p in passengers:
                    sn = p.get('seat_number', '')
                    if sn:
                        seat = Seat.query.filter_by(flight_id=flight_id, seat_number=sn).first()
                        if seat:
                            seat.is_available = False
                db.session.commit()
                session.pop('booking_passengers', None)
                session.pop('booking_tier', None)
                flash('Your booking is pending payment confirmation. We will notify you once verified.', 'info')
                return redirect(url_for('my_bookings'))

            else:  # failed
                # Rollback — release locks, do NOT mark seats taken
                SeatLock.query.filter_by(flight_id=flight_id, user_id=current_user.id).delete()
                booking.status = 'cancelled'
                booking.payment_status = 'failed'
                db.session.commit()
                session.pop('booking_passengers', None)
                session.pop('booking_tier', None)
                flash(f'Payment failed: {fail_reason}. Please try again with a different payment method.', 'danger')
                return redirect(url_for('checkout', flight_id=flight_id, tier=tier))

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while processing your booking. Please try again.', 'danger')
            app.logger.error(f'Checkout error for user {current_user.id}, flight {flight_id}: {e}')
            return redirect(url_for('checkout', flight_id=flight_id, tier=tier))

    # ── GET: render checkout preview ──
    class PaxPreview:
        def __init__(self, d):
            self.first_name = d['first_name']
            self.last_name = d['last_name']
            self.seat_number = d.get('seat_number', '')
            self.meal_preference = d.get('meal_preference', 'None')

    pax_preview = [PaxPreview(p) for p in passengers]
    price_per_pax = PACKAGE_PRICES.get(tier, 24000)
    total_price = price_per_pax * max(len(pax_preview), 1)

    # Check if user's seat locks are still valid
    now = datetime.utcnow()
    user_locks = SeatLock.query.filter_by(flight_id=flight_id, user_id=current_user.id).filter(
        SeatLock.expires_at > now
    ).all()
    lock_expires_at = min((l.expires_at for l in user_locks), default=None) if user_locks else None

    return render_template(
        'checkout.html',
        flight=flight,
        package_tier=tier,
        passengers=pax_preview,
        trip_type='one_way',
        return_date=None,
        total_price=total_price,
        selected_payment_method='card',
        payment_method_choices=payment_method_choices,
        lock_expires_at=lock_expires_at,
        lock_minutes=SeatLock.LOCK_MINUTES,
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
