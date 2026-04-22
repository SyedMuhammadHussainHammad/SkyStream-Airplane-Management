from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# IMPORTANT:
# db is initialized in app.py (do NOT create a second instance here)

db = None


# ---------------------------------------------------------------------------
# USER LOADER (MOVED SAFELY OUTSIDE APP IMPORT CYCLE)
# ---------------------------------------------------------------------------
def init_login_manager(login_manager):
    from models import User  # local import prevents circular crash

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


# ---------------------------------------------------------------------------
# USER MODEL
# ---------------------------------------------------------------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)

    phone_number = db.Column(db.String(11), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    age = db.Column(db.Integer, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    role = db.Column(db.String(20), nullable=False, default='customer')
    staff_id = db.Column(db.String(20), unique=True, nullable=True)

    # Relationships
    staff_profile = db.relationship('StaffProfile', backref='user', uselist=False, lazy=True)
    bookings = db.relationship('Booking', backref='customer', lazy=True)


# ---------------------------------------------------------------------------
# STAFF PROFILE
# ---------------------------------------------------------------------------
class StaffProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    role = db.Column(db.String(50), nullable=True, default='Cabin Crew')
    salary = db.Column(db.Float, default=0.0)

    completed_duties = db.Column(db.Integer, default=0)
    feedback_rating = db.Column(db.Float, default=0.0)
    reward_points = db.Column(db.Integer, default=0)

    rosters = db.relationship('StaffRoster', backref='staff', lazy=True)


# ---------------------------------------------------------------------------
# PLANE
# ---------------------------------------------------------------------------
class Plane(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    plane_id = db.Column(db.String(20), unique=True, nullable=False)
    model = db.Column(db.String(100), nullable=False)

    capacity = db.Column(db.Integer, nullable=False, default=180)

    current_airport = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='on_ground')

    flights = db.relationship('Flight', backref='plane', lazy=True)


# ---------------------------------------------------------------------------
# FLIGHT
# ---------------------------------------------------------------------------
class Flight(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    plane_id = db.Column(db.Integer, db.ForeignKey('plane.id'), nullable=True)

    origin = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)

    duration = db.Column(db.String(50), nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False)

    status = db.Column(db.String(20), nullable=False, default='on_time')

    rosters = db.relationship('StaffRoster', backref='flight', lazy=True)
    bookings = db.relationship('Booking', backref='flight', lazy=True)


# ---------------------------------------------------------------------------
# STAFF ROSTER
# ---------------------------------------------------------------------------
class StaffRoster(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    staff_profile_id = db.Column(db.Integer, db.ForeignKey('staff_profile.id'), nullable=False)
    flight_id = db.Column(db.Integer, db.ForeignKey('flight.id'), nullable=False)

    hotel = db.Column(db.String(255), nullable=True)
    travel_id = db.Column(db.String(100), nullable=True)


# ---------------------------------------------------------------------------
# BOOKING
# ---------------------------------------------------------------------------
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    flight_id = db.Column(db.Integer, db.ForeignKey('flight.id'), nullable=False)

    package_tier = db.Column(db.String(20), nullable=False)

    total_price = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False, default='card')

    status = db.Column(db.String(20), nullable=False, default='pending')

    trip_type = db.Column(db.String(10), nullable=False, default='one_way')
    return_date = db.Column(db.String(20), nullable=True)

    passengers = db.relationship('Passenger', backref='booking', lazy=True)
    ticket = db.relationship('Ticket', backref='booking', uselist=False, lazy=True)


# ---------------------------------------------------------------------------
# PASSENGER
# ---------------------------------------------------------------------------
class Passenger(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)

    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)

    seat_number = db.Column(db.String(10), nullable=False)
    meal_preference = db.Column(db.String(50), nullable=True)

    luggage_allowance = db.Column(db.Integer, nullable=False)


# ---------------------------------------------------------------------------
# TICKET
# ---------------------------------------------------------------------------
class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)

    color_code = db.Column(db.String(20), nullable=False)
    issue_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# SEAT
# ---------------------------------------------------------------------------
class Seat(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    flight_id = db.Column(db.Integer, db.ForeignKey('flight.id'), nullable=False)

    seat_number = db.Column(db.String(5), nullable=False)
    class_type = db.Column(db.String(20), nullable=False)
    is_available = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        db.UniqueConstraint('flight_id', 'seat_number', name='uq_flight_seat'),
    )

    @staticmethod
    def generate_for_flight(flight_id):
        """Generate seats only if not already created"""
        if Seat.query.filter_by(flight_id=flight_id).first():
            return

        seats = []
        cols = list("ABCDEF")

        for row in range(1, 31):
            class_type = 'Business' if row <= 5 else 'Economy'

            for col in cols:
                seats.append(
                    Seat(
                        flight_id=flight_id,
                        seat_number=f"{row}{col}",
                        class_type=class_type,
                        is_available=True
                    )
                )

        db.session.bulk_save_objects(seats)
        db.session.commit()
