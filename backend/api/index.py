import sys
import os

# ── Ensure backend/ is on the path so 'app', 'routes', 'models' etc. resolve ──
_api_dir = os.path.dirname(os.path.abspath(__file__))          # .../backend/api
_backend_dir = os.path.abspath(os.path.join(_api_dir, ".."))   # .../backend
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from app import app  # noqa: E402  (import after path fix)

# Vercel looks for a callable named 'app'
application = app
