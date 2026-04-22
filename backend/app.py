import sys
import os

_backend_dir = os.path.abspath(os.path.dirname(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

load_dotenv()

_project_root = os.path.abspath(os.path.join(_backend_dir, os.pardir))
_templates_dir = os.path.join(_project_root, "templates")
_static_dir    = os.path.join(_project_root, "static")

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

database_url = os.environ.get('DATABASE_URL', '')

# Neon/Heroku/Render use postgres:// — SQLAlchemy needs postgresql://
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# On Vercel there is NO writable filesystem — must use external DB
# Locally fall back to SQLite
if not database_url:
    _instance_dir = os.path.join(_backend_dir, 'instance')
    os.makedirs(_instance_dir, exist_ok=True)
    database_url = 'sqlite:///' + os.path.join(_instance_dir, 'skystream.db')

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

# ── Register models & routes ──
import sys as _sys
_sys.modules['app'] = _sys.modules[__name__]

import models  # noqa
import routes  # noqa

# ── Create tables lazily (safe on serverless) ──
@app.before_request
def _create_tables():
    # Only runs once per cold start — idempotent
    db.create_all()
    # Remove itself after first call so it doesn't run on every request
    app.before_request_funcs[None].remove(_create_tables)

@app.route('/health')
def health():
    return "SkyStream running 🚀"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)