#!/usr/bin/env python3
"""
Simple test to check if basic Flask functionality works
"""
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello World - SkyStream is working!"

@app.route('/health')
def health():
    return jsonify({"status": "ok", "message": "Simple test working"})

if __name__ == "__main__":
    app.run(debug=True)