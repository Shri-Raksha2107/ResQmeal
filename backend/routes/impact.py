"""routes/impact.py – Impact dashboard endpoints."""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from extensions import db
from models import Donation, User

impact_bp = Blueprint("impact", __name__, url_prefix="/api/impact")


# ── GET /api/impact/stats ────────────────────────────────────────────────────

@impact_bp.route("/stats", methods=["GET"])
@jwt_required()
def stats():
    """Return top-level impact aggregates calculated from the database."""
    donations = Donation.query.all()
    
    meals_saved = sum(d.meals for d in donations)
    
    # 0.37 kg CO2 prevented per meal
    co2_kg = int(meals_saved * 0.37)
    
    # 27 INR saved per meal
    money_saved_inr = int(meals_saved * 27)
    
    # Simple metric: % of donations rescued within 2 hours
    fast = sum(1 for d in donations if d.hours <= 2)
    total = len(donations)
    fast_rescues_pct = int((fast / total * 100)) if total > 0 else 0

    return jsonify({
        "meals_saved": meals_saved,
        "co2_kg": co2_kg,
        "money_saved_inr": money_saved_inr,
        "fast_rescues_pct": fast_rescues_pct,
    }), 200


# ── GET /api/impact/chart ────────────────────────────────────────────────────

@impact_bp.route("/chart", methods=["GET"])
@jwt_required()
def chart():
    """Return weekly leftover prediction chart data."""
    # Group donations by day of the week based on created_at
    donations = Donation.query.all()
    
    days_map = {"Mon": 0, "Tue": 0, "Wed": 0, "Thu": 0, "Fri": 0, "Sat": 0, "Sun": 0}
    days_list = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    for d in donations:
        if d.created_at:
            day_name = days_list[d.created_at.weekday()]
            days_map[day_name] += d.meals
            
    weekly_chart = [{"day": k, "meals": v} for k, v in days_map.items()]

    return jsonify(weekly_chart), 200


# ── GET /api/impact/leaderboard ──────────────────────────────────────────────

@impact_bp.route("/leaderboard", methods=["GET"])
@jwt_required()
def leaderboard():
    """Return top donors / NGOs / volunteers leaderboard based on DB stats."""
    donations = Donation.query.all()
    
    donor_meals = {}
    for d in donations:
        donor_meals[d.donor_id] = donor_meals.get(d.donor_id, 0) + d.meals
        
    leaderboard = []
    for donor_id, meals in donor_meals.items():
        user = db.session.get(User, donor_id)
        if user:
            leaderboard.append({
                "name": user.full_name,
                "type": "donor",
                "meals": meals
            })
            
    # Sort by meals descending
    leaderboard.sort(key=lambda x: x["meals"], reverse=True)

    return jsonify(leaderboard), 200
