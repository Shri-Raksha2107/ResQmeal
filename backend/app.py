"""
app.py – ResQmeal Flask application factory.

Usage:
    python run.py          # development server
    flask run              # alternative
"""

import os
from flask import Flask, send_from_directory
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

from config import Config
from routes.auth import auth_bp
from routes.donations import donations_bp
from routes.ngo import ngo_bp
from routes.routes_tracking import routes_bp
from routes.impact import impact_bp
from routes.chat import chat_bp


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder="static")
    app.config.from_object(Config)

    # ── Extensions ────────────────────────────────────────────────────────────
    CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)
    JWTManager(app)

    # ── Blueprints ────────────────────────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(donations_bp)
    app.register_blueprint(ngo_bp)
    app.register_blueprint(routes_bp)
    app.register_blueprint(impact_bp)
    app.register_blueprint(chat_bp)

    # ── Serve uploaded photos ─────────────────────────────────────────────────
    @app.route("/static/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(Config.UPLOAD_FOLDER, filename)

    # ── Health check ──────────────────────────────────────────────────────────
    @app.route("/api/health")
    def health():
        from flask import jsonify
        return jsonify({"status": "ok", "service": "ResQmeal API"}), 200

    # ── Ensure upload folder exists ───────────────────────────────────────────
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

    return app
