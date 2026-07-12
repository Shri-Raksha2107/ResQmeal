"""routes/ngo.py – NGO food request endpoints."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from db_store import load_db, save_db, next_id, now_iso
from services.donor_ranking import rank_donors

ngo_bp = Blueprint("ngo", __name__, url_prefix="/api/ngo")


# ── POST /api/ngo/requests ────────────────────────────────────────────────────

@ngo_bp.route("/requests", methods=["POST"])
@jwt_required()
def create_request():
    """
    Post a food request and return a ranked list of nearby donors.

    Body (JSON):
        ngo_name, people_needed, radius_km, storage_type, notes
    """
    user_id = int(get_jwt_identity())
    body = request.get_json(silent=True) or {}

    try:
        people = int(body.get("people_needed", 0))
        radius = float(body.get("radius_km", 5))
    except (TypeError, ValueError):
        return jsonify({"error": "'people_needed' and 'radius_km' must be numbers."}), 400

    required_meals = int(people * 1.25)  # 25% buffer

    db = load_db()
    ngo_request = {
        "id": next_id(db["ngo_requests"]),
        "ngo_id": user_id,
        "ngo_name": body.get("ngo_name", ""),
        "people_needed": people,
        "required_meals": required_meals,
        "radius_km": radius,
        "storage_type": body.get("storage_type", ""),
        "notes": body.get("notes", ""),
        "status": "open",
        "created_at": now_iso(),
    }
    db["ngo_requests"].append(ngo_request)
    save_db(db)

    donors = rank_donors(radius)

    return jsonify({
        "request": ngo_request,
        "required_meals": required_meals,
        "ranked_donors": donors,
    }), 201


# ── GET /api/ngo/requests ─────────────────────────────────────────────────────

@ngo_bp.route("/requests", methods=["GET"])
@jwt_required()
def list_requests():
    """List NGO requests for the current user."""
    user_id = int(get_jwt_identity())
    db = load_db()
    user = next((u for u in db["users"] if u["id"] == user_id), {})
    role = user.get("role", "ngo")

    if role == "ngo":
        result = [r for r in db["ngo_requests"] if r["ngo_id"] == user_id]
    else:
        result = db["ngo_requests"]

    return jsonify(result), 200


# ── GET /api/ngo/requests/<id> ────────────────────────────────────────────────

@ngo_bp.route("/requests/<int:request_id>", methods=["GET"])
@jwt_required()
def get_request(request_id: int):
    """Get a single NGO request with ranked donors."""
    db = load_db()
    ngo_req = next((r for r in db["ngo_requests"] if r["id"] == request_id), None)
    if not ngo_req:
        return jsonify({"error": "Request not found."}), 404

    donors = rank_donors(ngo_req["radius_km"])
    return jsonify({"request": ngo_req, "ranked_donors": donors}), 200
