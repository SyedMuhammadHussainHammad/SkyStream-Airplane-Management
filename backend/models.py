from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager

# ── LOGIN LOADER ──
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ── USER ──
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)

    phone_number = db.Column(db.String(11), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    age = db.Column(db.Integer, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    role = db.Column(db.String(20), default="customer")
    staff_id = db.Column(db.String(20), unique=True, nullable=True)

    staff_profile = db.relationship("StaffProfile", backref="user", uselist=False, cascade="all, delete-orphan")
    bookings = db.relationship("Booking", backref="customer", cascade="all, delete-orphan")


class Flight(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    origin = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)

    duration = db.Column(db.String(50), nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False)

    status = db.Column(db.String(20), default="on_time")
    plane_id = db.Column(db.Integer, db.ForeignKey("plane.id"), nullable=True)

    bookings = db.relationship("Booking", backref="flight")


class Seat(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    flight_id = db.Column(db.Integer, db.ForeignKey("flight.id"))
    seat_number = db.Column(db.String(5))
    class_type = db.Column(db.String(20))
    is_available = db.Column(db.Boolean, default=True)

    @staticmethod
    def generate_for_flight(flight_id):
        if Seat.query.filter_by(flight_id=flight_id).first():
            return

        seats = []
        for row in range(1, 31):
            for col in "ABCDEF":
                seats.append(
                    Seat(
                        flight_id=flight_id,
                        seat_number=f"{row}{col}",
                        class_type="Business" if row <= 5 else "Economy",
                    )
                )

        db.session.bulk_save_objects(seats)
        db.session.commit()


# ── PLANE ──
class Plane(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plane_id = db.Column(db.String(20), unique=True, nullable=False)
    model = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default="on_ground")  # on_ground, in_flight, maintenance
    current_airport = db.Column(db.String(100))

    flights = db.relationship("Flight", backref="plane", lazy=True)


# ── BOOKING ──
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    flight_id = db.Column(db.Integer, db.ForeignKey("flight.id"), nullable=False)

    package_tier = db.Column(db.String(20), default="Economy")  # Economy, Basic, Premium
    trip_type = db.Column(db.String(10), default="one_way")     # one_way, return
    return_date = db.Column(db.String(50))
    payment_method = db.Column(db.String(30), default="card")
    status = db.Column(db.String(20), default="confirmed")      # confirmed, pending, cancelled
    total_price = db.Column(db.Float, default=0.0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    passengers = db.relationship("Passenger", backref="booking", lazy=True)
    ticket = db.relationship("Ticket", backref="booking", uselist=False)


# ── PASSENGER ──
class Passenger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("booking.id"), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    seat_number = db.Column(db.String(5))
    meal_preference = db.Column(db.String(30), default='None')


# ── TICKET ──
class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("booking.id"), nullable=False)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)


# ── STAFF PROFILE ──
class StaffProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    role = db.Column(db.String(50))                  # Pilot, Co-Pilot, Engineer, Purser, etc.
    salary = db.Column(db.Float, default=0.0)
    completed_duties = db.Column(db.Integer, default=0)
    feedback_rating = db.Column(db.Float, default=0.0)
    reward_points = db.Column(db.Integer, default=0)

    rosters = db.relationship("Roster", backref="staff_profile", lazy=True)


# ── ROSTER ──
class Roster(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_profile_id = db.Column(db.Integer, db.ForeignKey("staff_profile.id"), nullable=False)
    flight_id = db.Column(db.Integer, db.ForeignKey("flight.id"), nullable=False)
    hotel = db.Column(db.String(100))
    travel_id = db.Column(db.String(50))

    flight = db.relationship("Flight", backref="rosters")
