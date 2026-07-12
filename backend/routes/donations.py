"""routes/donations.py – Donor donation endpoints."""

import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from config import Config
from db_store import load_db, save_db, next_id, now_iso
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
        safe_name = f"{now_iso().replace(':', '-')}_{photo.filename}"
        full_path = os.path.join(Config.UPLOAD_FOLDER, safe_name)
        photo.save(full_path)
        photo_path = f"/static/uploads/{safe_name}"

    # Score
    score = compute_safety_score(meals, hours, temperature, packaging)
    label = score_label(score, hours, packaging)

    db = load_db()
    donation = {
        "id": next_id(db["donations"]),
        "donor_id": user_id,
        "donor_type": data.get("donor_type", ""),
        "food_name": data.get("food_name", ""),
        "meals": meals,
        "hours": hours,
        "temperature": temperature,
        "packaging": packaging,
        "location": data.get("location", ""),
        "photo_path": photo_path,
        "safety_score": score,
        "status": "active",
        "created_at": now_iso(),
    }
    db["donations"].append(donation)

    # Update aggregate impact stats
    db["impact"]["meals_saved"] += meals

    save_db(db)

    # Rank NGOs
    matches = rank_ngos(score, meals, hours)

    return jsonify({
        "donation": donation,
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
    db = load_db()
    user = next((u for u in db["users"] if u["id"] == user_id), {})
    role = user.get("role", "donor")

    if role == "donor":
        result = [d for d in db["donations"] if d["donor_id"] == user_id]
    else:
        result = db["donations"]

    return jsonify(result), 200


# ── GET /api/donations/<id> ───────────────────────────────────────────────────

@donations_bp.route("/<int:donation_id>", methods=["GET"])
@jwt_required()
def get_donation(donation_id: int):
    """Get a single donation with its ranked NGO matches."""
    db = load_db()
    donation = next((d for d in db["donations"] if d["id"] == donation_id), None)
    if not donation:
        return jsonify({"error": "Donation not found."}), 404

    matches = rank_ngos(
        donation["safety_score"],
        donation["meals"],
        donation["hours"],
    )
    return jsonify({"donation": donation, "ngo_matches": matches}), 200


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

    db = load_db()
    for donation in db["donations"]:
        if donation["id"] == donation_id:
            donation["status"] = new_status
            save_db(db)
            return jsonify(donation), 200

    return jsonify({"error": "Donation not found."}), 404


# ── POST /api/donations/<id>/analyze ─────────────────────────────────────────

@donations_bp.route("/<int:donation_id>/analyze", methods=["POST"])
@jwt_required()
def analyze_donation(donation_id: int):
    """Re-run AI scoring and return updated NGO matches."""
    db = load_db()
    donation = next((d for d in db["donations"] if d["id"] == donation_id), None)
    if not donation:
        return jsonify({"error": "Donation not found."}), 404

    score = compute_safety_score(
        donation["meals"], donation["hours"],
        donation["temperature"], donation["packaging"]
    )
    label = score_label(score, donation["hours"], donation["packaging"])
    matches = rank_ngos(score, donation["meals"], donation["hours"])

    return jsonify({
        "safety_score": score,
        "safety_label": label,
        "ngo_matches": matches,
    }), 200
