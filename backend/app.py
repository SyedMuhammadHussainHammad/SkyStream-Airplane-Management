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
from flask_wtf.csrf import CSRFProtect

# ── APP ──
_project_root = os.path.abspath(os.path.join(_backend_dir, os.pardir))

# For Vercel serverless, check if templates exist at expected location
_template_folder = os.path.join(_project_root, "templates")
if not os.path.exists(_template_folder):
    # Fallback for Vercel deployment structure
    _template_folder = os.path.join("/var/task", "templates")
    if not os.path.exists(_template_folder):
        # Last resort - check current directory
        _template_folder = os.path.abspath("templates")

app = Flask(
    __name__,
    template_folder=_template_folder,
    static_folder=os.path.join(_project_root, "static"),
    static_url_path="/static",
)

# ── EXTENSIONS ──
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

# ── CONFIG ──
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

# Get DATABASE_URL from environment
database_url = os.environ.get("DATABASE_URL")

if not database_url:
    # In development, this will show a helpful error
    # In production (Vercel), this means env vars aren't configured
    import sys
    print("ERROR: DATABASE_URL environment variable is not set", file=sys.stderr)
    print("Please add DATABASE_URL in Vercel Environment Variables", file=sys.stderr)
    # Don't raise error immediately - let the app start so we can show error page
    database_url = "postgresql://localhost/placeholder"  # Placeholder to prevent crash

# Fix legacy 'postgres://' scheme (Heroku/older services)
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "connect_args": {
        "sslmode": "require",
        "connect_timeout": 10,
    },
}

# ── INIT EXTENSIONS ──
db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)
CSRFProtect(app)
login_manager.login_view = "login"

# ── Register 'app' module alias so sub-modules can do 'from app import ...' ──
sys.modules["app"] = sys.modules[__name__]

# ── Import models & routes inside app context ──
with app.app_context():
    import models   # noqa
    import routes   # noqa
    try:
        db.create_all()
    except Exception as e:
        print(f"Warning: Could not create tables: {e}")

# ── WSGI entry point ──
application = app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
