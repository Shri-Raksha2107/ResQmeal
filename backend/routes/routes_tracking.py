"""routes/routes_tracking.py – Optimized route & tracking endpoints."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from db_store import load_db, save_db, now_iso

routes_bp = Blueprint("routes_tracking", __name__, url_prefix="/api/routes")

# Static seed route stops (used when no real donation is supplied)
_SEED_ROUTE = [
    {"stop_order": 1, "name": "Sri Devi Wedding Hall", "description": "120 meals", "time": "7:25 PM", "type": "pickup"},
    {"stop_order": 2, "name": "Green Leaf Restaurant",  "description": "44 meals",  "time": "7:45 PM", "type": "pickup"},
    {"stop_order": 3, "name": "Hope Shelter",           "description": "Delivery",  "time": "8:05 PM", "type": "delivery"},
]


# ── GET /api/routes ───────────────────────────────────────────────────────────

@routes_bp.route("", methods=["GET"])
@jwt_required()
def get_routes():
    """
    Return optimized route stops.

    Query params:
        donation_id  (optional) – if provided, builds route from that donation
    """
    donation_id = request.args.get("donation_id", type=int)
    db = load_db()

    if donation_id:
        donation = next((d for d in db["donations"] if d["id"] == donation_id), None)
        if not donation:
            return jsonify({"error": "Donation not found."}), 404

        # Find the best-matched NGO to build a simple 2-stop route
        from services.matching import rank_ngos
        matches = rank_ngos(donation["safety_score"], donation["meals"], donation["hours"])
        best_ngo = matches[0] if matches else {"name": "Nearest NGO"}

        stops = [
            {
                "stop_order": 1,
                "name": donation.get("location", "Pickup Location"),
                "description": f"{donation['meals']} meals",
                "time": "Soon",
                "type": "pickup",
            },
            {
                "stop_order": 2,
                "name": best_ngo["name"],
                "description": "Delivery",
                "time": "ETA ~30 min",
                "type": "delivery",
            },
        ]
        return jsonify({"stops": stops}), 200

    # Fall back to seed data
    return jsonify({"stops": _SEED_ROUTE}), 200


# ── POST /api/routes/<donation_id>/confirm-pickup ─────────────────────────────

@routes_bp.route("/<int:donation_id>/confirm-pickup", methods=["POST"])
@jwt_required()
def confirm_pickup(donation_id: int):
    """Mark a donation as matched (pickup confirmed)."""
    db = load_db()
    for donation in db["donations"]:
        if donation["id"] == donation_id:
            donation["status"] = "matched"
            donation["pickup_confirmed_at"] = now_iso()
            save_db(db)
            return jsonify({"message": "Pickup confirmed.", "donation": donation}), 200
    return jsonify({"error": "Donation not found."}), 404
