import sys
import os
from dotenv import load_dotenv

# ── Load .env only if it exists (safe for Vercel + local)
if os.path.exists(".env"):
    load_dotenv()

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

database_url = os.environ.get('DATABASE_URL', '')

# Neon/Heroku/Render use postgres:// — SQLAlchemy needs postgresql://
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# STRICT: must exist in production
if not database_url:
    raise ValueError("DATABASE_URL is missing. Set it in environment variables.")

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

# ── SAFE TABLE CREATION (FIXED VERSION) ──
_tables_created = False

def init_db():
    """Create tables once safely"""
    global _tables_created
    if not _tables_created:
        try:
            with app.app_context():
                db.create_all()
            _tables_created = True
        except Exception as e:
            app.logger.error(f"DB init error: {e}")

# Call once at startup (safe for Vercel + local)
init_db()

@app.route('/health')
def health():
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', 'not set')
    db_type = 'postgresql' if 'postgresql' in db_url else 'sqlite' if 'sqlite' in db_url else 'unknown'

    try:
        db.session.execute(db.text('SELECT 1'))
        db_status = 'connected'
    except Exception as ex:
        db_status = f'error: {ex}'

    return jsonify({
        'status': 'running',
        'db_type': db_type,
        'db_status': db_status,
        'tables_created': _tables_created,
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
