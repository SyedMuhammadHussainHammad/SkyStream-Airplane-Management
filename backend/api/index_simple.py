from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# Simple HTML template
HOME_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>SkyStream Airlines</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f0f8ff; }
        .container { max-width: 800px; margin: 0 auto; text-align: center; }
        .logo { font-size: 2.5em; color: #1e40af; margin-bottom: 20px; }
        .message { font-size: 1.2em; color: #374151; margin-bottom: 30px; }
        .button { 
            display: inline-block; padding: 12px 24px; 
            background: #1e40af; color: white; text-decoration: none; 
            border-radius: 8px; margin: 10px;
        }
        .status { background: #10b981; color: white; padding: 10px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">✈️ SkyStream Airlines</div>
        <div class="status">✅ Application is running successfully!</div>
        <div class="message">
            Welcome to SkyStream Airlines - Your premium flight booking experience.
        </div>
        <p>The application is now working on Vercel. You can now add back the full functionality.</p>
        <a href="/health" class="button">Check Health Status</a>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HOME_TEMPLATE)

@app.route('/health')
def health():
    return jsonify({
        "status": "ok", 
        "message": "SkyStream is running successfully on Vercel",
        "version": "minimal-1.0"
    })

@app.route('/test')
def test():
    return jsonify({
        "test": "passed",
        "message": "Basic Flask functionality is working",
        "routes": ["/", "/health", "/test"]
    })

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Page not found", "status": 404}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error", "status": 500}), 500

# Vercel entry point
application = app

if __name__ == "__main__":
    app.run(debug=True)