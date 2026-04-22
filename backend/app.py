import sys
import os
import json
import time

# Ensure the backend directory is on sys.path so sibling modules
# (models, routes, forms) can be imported with plain absolute names
# regardless of how Vercel or Python resolves the entry-point.
_backend_dir = os.path.abspath(os.path.dirname(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

load_dotenv()

# Templates and static live at the project root (parent of backend/)
# This works both locally and on Vercel
_project_root = os.path.abspath(os.path.join(_backend_dir, os.pardir))
_templates_dir = os.path.join(_project_root, "templates")
_static_dir    = os.path.join(_project_root, "static")

def debug_log(*, run_id: str, hypothesis_id: str, location: str, message: str, data: dict):
    """No-op debug logger for local dev. Override by setting DEBUG_LOG_PATH env var."""
    try:
        log_path = os.environ.get('DEBUG_LOG_PATH')
        if not log_path:
            return
        payload = {
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass

app = Flask(
    __name__,
    template_folder=_templates_dir,
    static_folder=_static_dir,
    static_url_path="/static",
)
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

# 2. CONFIGURATION
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'skystream-secret-key-123')
database_url = os.environ.get('DATABASE_URL', '')

# Render/Neon/Heroku use postgres:// — SQLAlchemy needs postgresql://
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Fall back to SQLite for local dev only
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

# 3. INITIALIZE EXTENSIONS WITH APP
db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)

login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# 4. IMPORT MODELS & ROUTES
# Register this module as 'app' in sys.modules BEFORE importing models/routes.
# This ensures that when models.py does `from app import db, login_manager`,
# it finds the already-initialized db and login_manager objects even though
# app.py hasn't finished executing yet.
import sys as _sys
_sys.modules['app'] = _sys.modules[__name__]

import models  # noqa: E402 — registers user_loader and ORM classes
import routes  # noqa: E402 — registers all @app.route decorators

# 5. AUTO-CREATE TABLES on first run (safe — skips existing tables)
with app.app_context():
    db.create_all()

@app.route('/health')
def health():
    return "SkyStream running 🚀"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)