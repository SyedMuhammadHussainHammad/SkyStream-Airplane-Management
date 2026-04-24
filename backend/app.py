import os
import sys

# ── PATH: make sure backend/ is resolvable ──
_backend_dir = os.path.abspath(os.path.dirname(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# ── Load .env only in local development (Vercel uses dashboard env vars) ──
try:
    from dotenv import load_dotenv
    from pathlib import Path
    # Look for .env in backend/ first, then project root
    for _env_path in [
        Path(_backend_dir) / ".env",
        Path(_backend_dir).parent / ".env",
    ]:
        if _env_path.exists():
            load_dotenv(dotenv_path=_env_path)
            break
except ImportError:
    pass  # python-dotenv not available, rely on environment variables

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

# ── APP ──
_project_root = os.path.abspath(os.path.join(_backend_dir, os.pardir))

app = Flask(
    __name__,
    template_folder=os.path.join(_project_root, "templates"),
    static_folder=os.path.join(_project_root, "static"),
    static_url_path="/static",
)

# ── EXTENSIONS ──
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

# ── CONFIG ──
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Add it in your Vercel project settings → Environment Variables."
    )

# Fix legacy 'postgres://' scheme (Heroku/older services)
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Strip channel_binding parameter — psycopg2-binary does not support it
import re
database_url = re.sub(r'[&?]channel_binding=[^&]*', '', database_url)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,          # test connection before use
    "pool_recycle": 300,            # recycle connections every 5 min
    "connect_args": {
        "sslmode": "require",       # Neon requires SSL
        "connect_timeout": 10,
    },
}

from flask_wtf.csrf import CSRFProtect

# ── INIT EXTENSIONS ──
db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)
CSRFProtect(app)  # makes csrf_token() available in all templates
login_manager.login_view = "login"

# ── Register 'app' module alias so sub-modules can do 'from app import ...' ──
sys.modules["app"] = sys.modules[__name__]

# ── Import models & routes inside app context ──
with app.app_context():
    import models   # noqa
    import routes   # noqa
    db.create_all()

    # ── Auto-migrate: add new columns/tables if they don't exist yet ──
    from sqlalchemy import text as _text
    _MIGRATIONS = [
        "ALTER TABLE booking ADD COLUMN IF NOT EXISTS payment_status VARCHAR(20) DEFAULT 'pending'",
        "ALTER TABLE booking ADD COLUMN IF NOT EXISTS hold_expires_at TIMESTAMP",
        "ALTER TABLE passenger ADD COLUMN IF NOT EXISTS meal_preference VARCHAR(50) DEFAULT 'None'",
        "ALTER TABLE ticket ADD COLUMN IF NOT EXISTS ticket_number VARCHAR(20)",
        "ALTER TABLE ticket ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'issued'",
        # Backfill existing confirmed bookings
        "UPDATE booking SET payment_status = 'confirmed' WHERE status = 'confirmed' AND payment_status = 'pending'",
        "UPDATE ticket SET status = 'issued' WHERE status IS NULL",
    ]
    _CREATE_SEAT_LOCK = """
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
    _CREATE_PAYMENT_TXN = """
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
    try:
        with db.engine.connect() as _conn:
            for _sql in _MIGRATIONS:
                try:
                    _conn.execute(_text(_sql))
                    _conn.commit()
                except Exception:
                    _conn.rollback()
            for _ddl in [_CREATE_SEAT_LOCK, _CREATE_PAYMENT_TXN]:
                try:
                    _conn.execute(_text(_ddl))
                    _conn.commit()
                except Exception:
                    _conn.rollback()
    except Exception:
        pass  # non-fatal — app still starts

# ── WSGI entry point ──
application = app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
