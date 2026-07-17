"""
models.py – SQLAlchemy database models.
"""

from datetime import datetime
from extensions import db

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(128), nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email = db.Column(db.String(128), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="donor")
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    donations = db.relationship("Donation", backref="donor", lazy="dynamic")
    requests = db.relationship("NGORequest", backref="ngo", lazy="dynamic")


class OTP(db.Model):
    __tablename__ = "otps"
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), nullable=False, index=True)
    otp_code = db.Column(db.String(10), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Donation(db.Model):
    __tablename__ = "donations"
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    donor_type = db.Column(db.String(64), nullable=True)
    food_name = db.Column(db.String(128), nullable=False)
    meals = db.Column(db.Integer, nullable=False)
    hours = db.Column(db.Integer, nullable=False)
    temperature = db.Column(db.String(32), nullable=True)
    packaging = db.Column(db.String(32), nullable=True)
    location = db.Column(db.String(256), nullable=True)
    photo_path = db.Column(db.String(256), nullable=True)
    safety_score = db.Column(db.Integer, nullable=True)
    ai_safety_analysis = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), default="active")  # active, matched, delivered
    pickup_confirmed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class NGORequest(db.Model):
    __tablename__ = "ngo_requests"
    id = db.Column(db.Integer, primary_key=True)
    ngo_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    ngo_name = db.Column(db.String(128), nullable=True)
    people_needed = db.Column(db.Integer, nullable=False)
    required_meals = db.Column(db.Integer, nullable=False)
    radius_km = db.Column(db.Float, nullable=False, default=5.0)
    storage_type = db.Column(db.String(64), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), default="open")  # open, fulfilled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
