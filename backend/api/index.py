import sys
import os
import traceback

# ── Ensure backend/ is on the path ──
_api_dir    = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.abspath(os.path.join(_api_dir, ".."))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from flask import Flask, jsonify

_init_error     = None
_init_traceback = None

try:
    from app import app          # noqa: E402
    application = app
except Exception as _e:
    _init_error     = _e
    _init_traceback = traceback.format_exc()

    application = Flask(__name__)

    @application.route('/', defaults={'path': ''})
    @application.route('/<path:path>')
    def _fallback(path=''):
        return jsonify({
            'status':    'startup_error',
            'error':     str(_init_error),
            'traceback': _init_traceback,
            'env': {
                'DATABASE_URL_set': bool(os.environ.get('DATABASE_URL')),
                'SECRET_KEY_set':   bool(os.environ.get('SECRET_KEY')),
                'sys_path':         sys.path[:4],
                'cwd':              os.getcwd(),
            }
        }), 500

# Vercel looks for 'app' or 'application' at module level
app = application
