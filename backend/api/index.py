import sys
import os

# ── Ensure backend/ is on the path so 'app', 'routes', 'models' etc. resolve ──
_api_dir = os.path.dirname(os.path.abspath(__file__))          # .../backend/api
_backend_dir = os.path.abspath(os.path.join(_api_dir, ".."))   # .../backend
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

try:
    from app import app  # noqa: E402  (import after path fix)
    application = app
except Exception as e:
    # If app fails to initialize, create a minimal Flask app to show the error
    from flask import Flask, jsonify
    application = Flask(__name__)
    
    @application.route('/')
    @application.route('/<path:path>')
    def error_handler(path=''):
        return jsonify({
            'error': 'Application failed to initialize',
            'detail': str(e),
            'type': type(e).__name__,
            'hint': 'Check that DATABASE_URL is set in Vercel Environment Variables'
        }), 500
