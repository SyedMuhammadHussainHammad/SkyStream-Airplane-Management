import sys
import os
from dotenv import load_dotenv
from pathlib import Path

# ── Load .env safely (FIXED + ALWAYS LOAD FIRST) ──
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR.parent / ".env"

load_dotenv(dotenv_path=env_path)

_backend_dir = os.path.abspath(os.path.dirname(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

_project_root = os.path.abspath(os.path.join(_backend_dir, os.pardir))
_templates_dir = os.path.join(_project_root, "templates")
_static_dir = os.path.join(_project_root, "static")

app = Flask(
    __name__,
    template_folder=_templates_dir,
    static_folder=_static_dir,
    static_url_path="/static",
)

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

# ── Configuration ──
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'skystream-secret-key-dev')

database_url = os.environ.get('DATABASE_URL')

if not database_url:
    raise ValueError(
        f"DATABASE_URL is missing.\n"
        f"Checked path: {env_path}\n"
        f"Make sure .env exists in project root."
    )

if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# ── Init extensions ──
db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)

login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# ── IMPORTANT FIX: ensure app is import-safe for routes (prevents BuildError in Vercel) ──
import sys as _sys
_sys.modules['app'] = _sys.modules[__name__]

# ── Register models & routes ──
import models  # noqa
import routes  # noqa

# ── SAFE TABLE CREATION ──
_tables_created = False

def init_db():
    global _tables_created
    if not _tables_created:
        try:
            with app.app_context():
                db.create_all()
            _tables_created = True
        except Exception as e:
            app.logger.error(f"DB init error: {e}")

init_db()

# ── VERCEL COMPATIBILITY FIX (IMPORTANT) ──
application = app

# ── ENTRY POINT ──
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
