"""routes/ngo.py – NGO food request endpoints."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import NGORequest, User
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

    ngo_request = NGORequest(
        ngo_id=user_id,
        ngo_name=body.get("ngo_name", ""),
        people_needed=people,
        required_meals=required_meals,
        radius_km=radius,
        storage_type=body.get("storage_type", ""),
        notes=body.get("notes", ""),
        status="open"
    )
    db.session.add(ngo_request)
    db.session.commit()

    donors = rank_donors(radius)

    req_dict = {
        "id": ngo_request.id,
        "ngo_id": ngo_request.ngo_id,
        "ngo_name": ngo_request.ngo_name,
        "people_needed": ngo_request.people_needed,
        "required_meals": ngo_request.required_meals,
        "radius_km": ngo_request.radius_km,
        "storage_type": ngo_request.storage_type,
        "notes": ngo_request.notes,
        "status": ngo_request.status,
        "created_at": ngo_request.created_at.isoformat() + "Z" if ngo_request.created_at else None
    }

    return jsonify({
        "request": req_dict,
        "required_meals": required_meals,
        "ranked_donors": donors,
    }), 201


# ── GET /api/ngo/requests ─────────────────────────────────────────────────────

@ngo_bp.route("/requests", methods=["GET"])
@jwt_required()
def list_requests():
    """List NGO requests for the current user."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    role = user.role if user else "ngo"

    if role == "ngo":
        requests = NGORequest.query.filter_by(ngo_id=user_id).all()
    else:
        requests = NGORequest.query.all()

    result = []
    for r in requests:
        result.append({
            "id": r.id,
            "ngo_id": r.ngo_id,
            "ngo_name": r.ngo_name,
            "people_needed": r.people_needed,
            "required_meals": r.required_meals,
            "radius_km": r.radius_km,
            "storage_type": r.storage_type,
            "notes": r.notes,
            "status": r.status,
            "created_at": r.created_at.isoformat() + "Z" if r.created_at else None
        })

    return jsonify(result), 200


# ── GET /api/ngo/requests/<id> ────────────────────────────────────────────────

@ngo_bp.route("/requests/<int:request_id>", methods=["GET"])
@jwt_required()
def get_request(request_id: int):
    """Get a single NGO request with ranked donors."""
    ngo_req = db.session.get(NGORequest, request_id)
    if not ngo_req:
        return jsonify({"error": "Request not found."}), 404

    donors = rank_donors(ngo_req.radius_km)
    
    req_dict = {
        "id": ngo_req.id,
        "ngo_id": ngo_req.ngo_id,
        "ngo_name": ngo_req.ngo_name,
        "people_needed": ngo_req.people_needed,
        "required_meals": ngo_req.required_meals,
        "radius_km": ngo_req.radius_km,
        "storage_type": ngo_req.storage_type,
        "notes": ngo_req.notes,
        "status": ngo_req.status,
        "created_at": ngo_req.created_at.isoformat() + "Z" if ngo_req.created_at else None
    }
    
    return jsonify({"request": req_dict, "ranked_donors": donors}), 200
