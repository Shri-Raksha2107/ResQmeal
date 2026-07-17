"""
config.py – Application configuration for ResQmeal backend.
All values are read from environment variables (or .env via python-dotenv).
Swap DATABASE_URL in here when PostgreSQL is ready.
"""

import os
from datetime import timedelta

class Config:
    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-please-change")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-please-change")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)

    # ── Storage ───────────────────────────────────────────────────────────────
    # PostgreSQL Database
    SQLALCHEMY_DATABASE_URI: str = os.getenv("DATABASE_URL", "sqlite:///app.db")
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Gemini API
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # File upload directory
    UPLOAD_FOLDER: str = os.path.join(os.path.dirname(__file__), "static", "uploads")
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16 MB

    # ── OTP ───────────────────────────────────────────────────────────────────
    OTP_DEV_MODE: bool = os.getenv("OTP_DEV_MODE", "true").lower() == "true"
    OTP_EXPIRY_SECONDS: int = 300  # 5 minutes

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Allow the HTML file opened directly from disk (file://) and localhost
    CORS_ORIGINS: list = ["*"]
