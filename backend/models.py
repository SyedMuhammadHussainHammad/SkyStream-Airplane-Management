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

    staff_profile = db.relationship("StaffProfile", backref="user", uselist=False)
    bookings = db.relationship("Booking", backref="customer")


class Flight(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    origin = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)

    duration = db.Column(db.String(50), nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False)

    status = db.Column(db.String(20), default="on_time")

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
