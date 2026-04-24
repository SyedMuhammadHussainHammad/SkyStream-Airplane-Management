"""
Safe migration script — adds new columns and tables introduced in the
real-world constraints update. Uses IF NOT EXISTS / exception guards so
it can be run multiple times without error.

Run with:
    python migrate_db.py
"""
from app import app, db
from sqlalchemy import text

MIGRATIONS = [
    # ── booking: new columns ──
    "ALTER TABLE booking ADD COLUMN IF NOT EXISTS payment_status VARCHAR(20) DEFAULT 'pending'",
    "ALTER TABLE booking ADD COLUMN IF NOT EXISTS hold_expires_at TIMESTAMP",

    # ── passenger: meal_preference ──
    "ALTER TABLE passenger ADD COLUMN IF NOT EXISTS meal_preference VARCHAR(50) DEFAULT 'None'",

    # ── ticket: ticket_number + status ──
    "ALTER TABLE ticket ADD COLUMN IF NOT EXISTS ticket_number VARCHAR(20)",
    "ALTER TABLE ticket ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'issued'",

    # ── backfill: existing confirmed bookings should have payment_status = 'confirmed' ──
    "UPDATE booking SET payment_status = 'confirmed' WHERE status = 'confirmed' AND payment_status = 'pending'",

    # ── backfill: existing issued tickets ──
    "UPDATE ticket SET status = 'issued' WHERE status IS NULL",
]

CREATE_SEAT_LOCK = """
CREATE TABLE IF NOT EXISTS seat_lock (
    id          SERIAL PRIMARY KEY,
    flight_id   INTEGER NOT NULL REFERENCES flight(id),
    seat_number VARCHAR(5) NOT NULL,
    user_id     INTEGER NOT NULL REFERENCES "user"(id),
    locked_at   TIMESTAMP DEFAULT NOW(),
    expires_at  TIMESTAMP NOT NULL,
    CONSTRAINT uq_seat_lock UNIQUE (flight_id, seat_number)
)
"""

CREATE_PAYMENT_TRANSACTION = """
CREATE TABLE IF NOT EXISTS payment_transaction (
    id              SERIAL PRIMARY KEY,
    booking_id      INTEGER NOT NULL REFERENCES booking(id),
    amount          FLOAT NOT NULL,
    method          VARCHAR(30) NOT NULL,
    status          VARCHAR(20) DEFAULT 'pending',
    gateway_ref     VARCHAR(50),
    failure_reason  VARCHAR(200),
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
)
"""

with app.app_context():
    conn = db.engine.connect()
    try:
        # 1. Column migrations
        for sql in MIGRATIONS:
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"  ✅  {sql[:70]}...")
            except Exception as e:
                conn.rollback()
                print(f"  ⚠️  Skipped (already applied?): {e}")

        # 2. New tables
        for name, ddl in [('seat_lock', CREATE_SEAT_LOCK),
                           ('payment_transaction', CREATE_PAYMENT_TRANSACTION)]:
            try:
                conn.execute(text(ddl))
                conn.commit()
                print(f"  ✅  Table '{name}' ready.")
            except Exception as e:
                conn.rollback()
                print(f"  ⚠️  Table '{name}': {e}")

        print("\n✅  Migration complete.")
    finally:
        conn.close()
