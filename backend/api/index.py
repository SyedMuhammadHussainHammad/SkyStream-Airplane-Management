import sys
import os

# ── Ensure backend/ is on the path so 'app', 'routes', 'models' etc. resolve ──
_api_dir = os.path.dirname(os.path.abspath(__file__))          # .../backend/api
_backend_dir = os.path.abspath(os.path.join(_api_dir, ".."))   # .../backend
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from flask import Flask, jsonify

# Fallback app shown if the real app fails to initialize
application = Flask(__name__)

@application.route('/')
@application.route('/<path:path>')
def error_handler(path=''):
    return jsonify({
        'error': 'Application failed to initialize',
        'hint': 'Check that DATABASE_URL is set in Vercel Environment Variables'
    }), 500

try:
    from app import app  # noqa: E402
    application = app
except Exception as e:
    import traceback
    _err = traceback.format_exc()

    @application.route('/_error')
    def show_error():
        return jsonify({
            'error': 'Application failed to initialize',
            'detail': str(e),
            'traceback': _err,
        }), 500

app = application
