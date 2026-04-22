import sys
import os
from dotenv import load_dotenv
from pathlib import Path

# ── LOAD ENV ──
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

# ── PATHS ──
_project_root = os.path.abspath(os.path.join(_backend_dir, os.pardir))
_templates_dir = os.path.join(_project_root, "templates")
_static_dir = os.path.join(_project_root, "static")

# ── APP ──
app = Flask(
    __name__,
    template_folder=_templates_dir,
    static_folder=_static_dir,
    static_url_path="/static",
)

# ── EXTENSIONS ──
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

# ── CONFIG ──
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'skystream-secret-key-dev')

database_url = os.environ.get('DATABASE_URL')

if not database_url:
    raise ValueError("DATABASE_URL is missing")

if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ── INIT ──
db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)

login_manager.login_view = 'login'

# ── IMPORT SAFETY (Vercel fix) ──
sys.modules.setdefault('app', sys.modules[__name__])

# ── IMPORT ROUTES ONLY ONCE ──
with app.app_context():
    import models
    import routes

# ── DB INIT SAFE ──
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print("DB init error:", e)

# ── VERCEL ENTRYPOINT ──
application = app

# ── LOCAL RUN ──
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
