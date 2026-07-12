"""routes/impact.py – Impact dashboard endpoints."""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from db_store import load_db

impact_bp = Blueprint("impact", __name__, url_prefix="/api/impact")


# ── GET /api/impact/stats ────────────────────────────────────────────────────

@impact_bp.route("/stats", methods=["GET"])
@jwt_required()
def stats():
    """Return top-level impact aggregates."""
    db = load_db()
    imp = db.get("impact", {})
    return jsonify({
        "meals_saved": imp.get("meals_saved", 0),
        "co2_kg": imp.get("co2_kg", 0),
        "money_saved_inr": imp.get("money_saved_inr", 0),
        "fast_rescues_pct": imp.get("fast_rescues_pct", 0),
    }), 200


# ── GET /api/impact/chart ────────────────────────────────────────────────────

@impact_bp.route("/chart", methods=["GET"])
@jwt_required()
def chart():
    """Return weekly leftover prediction chart data."""
    db = load_db()
    imp = db.get("impact", {})
    return jsonify(imp.get("weekly_chart", [])), 200


# ── GET /api/impact/leaderboard ──────────────────────────────────────────────

@impact_bp.route("/leaderboard", methods=["GET"])
@jwt_required()
def leaderboard():
    """Return top donors / NGOs / volunteers leaderboard."""
    db = load_db()
    imp = db.get("impact", {})
    return jsonify(imp.get("leaderboard", [])), 200
