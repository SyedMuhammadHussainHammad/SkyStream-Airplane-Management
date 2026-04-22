import os
from dotenv import load_dotenv
from pathlib import Path
import sys

# ── ENV ──
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR.parent / ".env"
load_dotenv(dotenv_path=env_path)

# ── PATH ──
_backend_dir = os.path.abspath(os.path.dirname(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from flask import Flask, jsonify
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

# ── EXTENSIONS (IMPORTANT: real objects only) ──
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

# ── CONFIG ──
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-key")

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL missing")

if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ── INIT EXTENSIONS ──
db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)

login_manager.login_view = "login"

# ── CRITICAL FIX: IMPORT SAFETY ──
sys.modules["app"] = sys.modules[__name__]

# ── IMPORT INSIDE CONTEXT (VERY IMPORTANT FIX) ──
with app.app_context():
    import models
    import routes

    db.create_all()

# ── ENTRYPOINT ──
application = app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
