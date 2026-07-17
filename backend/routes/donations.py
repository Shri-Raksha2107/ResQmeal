"""routes/donations.py – Donor donation endpoints."""

import os
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from config import Config
from extensions import db
from models import Donation, User
from services.safety_score import compute_safety_score, score_label
from services.matching import rank_ngos

donations_bp = Blueprint("donations", __name__, url_prefix="/api/donations")


# ── POST /api/donations ───────────────────────────────────────────────────────

@donations_bp.route("", methods=["POST"])
@jwt_required()
def create_donation():
    """
    Create a donation, compute safety score, and return ranked NGO matches.

    Form-data fields (multipart or JSON):
        donor_type, food_name, meals, hours, temperature, packaging, location
    Optional:
        photo  (file upload)
    """
    user_id = int(get_jwt_identity())

    # Support both JSON and multipart form data
    if request.content_type and "multipart" in request.content_type:
        data = request.form
        photo = request.files.get("photo")
    else:
        data = request.get_json(silent=True) or {}
        photo = None

    try:
        meals = int(data.get("meals", 0))
        hours = int(data.get("hours", 4))
    except (TypeError, ValueError):
        return jsonify({"error": "'meals' and 'hours' must be integers."}), 400

    temperature = data.get("temperature", "room")
    packaging = data.get("packaging", "sealed")

    # Save photo
    photo_path = None
    if photo and photo.filename:
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        safe_name = f"{datetime.utcnow().isoformat().replace(':', '-')}_{photo.filename}"
        full_path = os.path.join(Config.UPLOAD_FOLDER, safe_name)
        photo.save(full_path)
        photo_path = f"/static/uploads/{safe_name}"

    # Score
    from services.safety_score import analyze_food_safety_ai, score_details
    score = compute_safety_score(meals, hours, temperature, packaging)
    label = score_details(score, hours, packaging)
    ai_analysis = analyze_food_safety_ai(data.get("food_name", ""), hours, temperature, packaging)

    donation = Donation(
        donor_id=user_id,
        donor_type=data.get("donor_type", ""),
        food_name=data.get("food_name", ""),
        meals=meals,
        hours=hours,
        temperature=temperature,
        packaging=packaging,
        location=data.get("location", ""),
        photo_path=photo_path,
        safety_score=score,
        ai_safety_analysis=ai_analysis,
        status="active"
    )
    db.session.add(donation)
    db.session.commit()

    # Rank NGOs
    matches = rank_ngos(score, meals, hours)

    donation_dict = {
        "id": donation.id,
        "donor_id": donation.donor_id,
        "donor_type": donation.donor_type,
        "food_name": donation.food_name,
        "meals": donation.meals,
        "hours": donation.hours,
        "temperature": donation.temperature,
        "packaging": donation.packaging,
        "location": donation.location,
        "photo_path": donation.photo_path,
        "safety_score": donation.safety_score,
        "ai_safety_analysis": donation.ai_safety_analysis,
        "status": donation.status,
        "created_at": donation.created_at.isoformat() + "Z" if donation.created_at else None
    }

    return jsonify({
        "donation": donation_dict,
        "safety_score": score,
        "safety_label": label,
        "ngo_matches": matches,
    }), 201


# ── GET /api/donations ────────────────────────────────────────────────────────

@donations_bp.route("", methods=["GET"])
@jwt_required()
def list_donations():
    """List donations.  Donors see their own; future admin role sees all."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    role = user.role if user else "donor"

    if role == "donor":
        donations = Donation.query.filter_by(donor_id=user_id).all()
    else:
        donations = Donation.query.all()

    result = []
    for d in donations:
        result.append({
            "id": d.id,
            "donor_id": d.donor_id,
            "donor_type": d.donor_type,
            "food_name": d.food_name,
            "meals": d.meals,
            "hours": d.hours,
            "temperature": d.temperature,
            "packaging": d.packaging,
            "location": d.location,
            "photo_path": d.photo_path,
            "safety_score": d.safety_score,
            "ai_safety_analysis": d.ai_safety_analysis,
            "status": d.status,
            "created_at": d.created_at.isoformat() + "Z" if d.created_at else None
        })

    return jsonify(result), 200


# ── GET /api/donations/<id> ───────────────────────────────────────────────────

@donations_bp.route("/<int:donation_id>", methods=["GET"])
@jwt_required()
def get_donation(donation_id: int):
    """Get a single donation with its ranked NGO matches."""
    donation = db.session.get(Donation, donation_id)
    if not donation:
        return jsonify({"error": "Donation not found."}), 404

    matches = rank_ngos(
        donation.safety_score,
        donation.meals,
        donation.hours,
    )
    
    donation_dict = {
        "id": donation.id,
        "donor_id": donation.donor_id,
        "donor_type": donation.donor_type,
        "food_name": donation.food_name,
        "meals": donation.meals,
        "hours": donation.hours,
        "temperature": donation.temperature,
        "packaging": donation.packaging,
        "location": donation.location,
        "photo_path": donation.photo_path,
        "safety_score": donation.safety_score,
        "ai_safety_analysis": donation.ai_safety_analysis,
        "status": donation.status,
        "created_at": donation.created_at.isoformat() + "Z" if donation.created_at else None
    }
    
    return jsonify({"donation": donation_dict, "ngo_matches": matches}), 200


# ── PATCH /api/donations/<id>/status ─────────────────────────────────────────

@donations_bp.route("/<int:donation_id>/status", methods=["PATCH"])
@jwt_required()
def update_status(donation_id: int):
    """Update donation status (active → matched → delivered)."""
    body = request.get_json(silent=True) or {}
    new_status = body.get("status", "")
    allowed = {"pending", "active", "matched", "delivered"}
    if new_status not in allowed:
        return jsonify({"error": f"status must be one of {allowed}"}), 400

    donation = db.session.get(Donation, donation_id)
    if not donation:
        return jsonify({"error": "Donation not found."}), 404
        
    donation.status = new_status
    db.session.commit()
    
    donation_dict = {
        "id": donation.id,
        "status": donation.status
    }
    return jsonify(donation_dict), 200


# ── POST /api/donations/<id>/analyze ─────────────────────────────────────────

@donations_bp.route("/<int:donation_id>/analyze", methods=["POST"])
@jwt_required()
def analyze_donation(donation_id: int):
    """Re-run AI scoring and return updated NGO matches."""
    donation = db.session.get(Donation, donation_id)
    if not donation:
        return jsonify({"error": "Donation not found."}), 404

    from services.safety_score import analyze_food_safety_ai, score_details
    score = compute_safety_score(
        donation.meals, donation.hours,
        donation.temperature, donation.packaging
    )
    label = score_details(score, donation.hours, donation.packaging)
    ai_analysis = analyze_food_safety_ai(donation.food_name, donation.hours, donation.temperature, donation.packaging)
    
    donation.safety_score = score
    donation.ai_safety_analysis = ai_analysis
    db.session.commit()

    matches = rank_ngos(score, donation.meals, donation.hours)

    return jsonify({
        "safety_score": score,
        "safety_label": label,
        "ai_safety_analysis": ai_analysis,
        "ngo_matches": matches,
    }), 200
