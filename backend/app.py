import os
import sys

# ── PATH: make sure backend/ is resolvable ──
_backend_dir = os.path.abspath(os.path.dirname(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# ── Load .env for local development ──
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
    # Use SQLite database for local development
    database_url = "sqlite:///skystream.db"

# Fix legacy 'postgres://' scheme (Heroku/older services)
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Strip channel_binding parameter — psycopg2-binary does not support it
import re
database_url = re.sub(r'[&?]channel_binding=[^&]*', '', database_url)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Database configuration
if "sqlite" not in database_url:
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "connect_args": {
            "sslmode": "require",
            "connect_timeout": 10,
        },
    }
else:
    # SQLite configuration
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
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
    
    # Database initialization
    try:
        db.create_all()
    except Exception as e:
        print(f"Database initialization warning: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
