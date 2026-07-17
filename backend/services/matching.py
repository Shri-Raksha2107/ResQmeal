"""
services/matching.py

NGO matching service.
Ranks the registered NGOs against a donation and returns a sorted list with match percentages.
"""

from __future__ import annotations
from typing import List, Dict, Any

from extensions import db
from models import User, NGORequest

def rank_ngos(
    safety_score: int,
    meals: int,
    hours: int,
    ngo_profiles: List[Dict[str, Any]] | None = None,
) -> List[Dict[str, Any]]:
    """
    Rank NGOs for a given donation based on active requests in the database.
    """
    if ngo_profiles is not None:
        profiles = ngo_profiles
    else:
        profiles = []
        # Query active NGO requests from the DB
        open_requests = NGORequest.query.filter_by(status="open").all()
        for req in open_requests:
            ngo_user = db.session.get(User, req.ngo_id)
            if not ngo_user:
                continue
            profiles.append({
                "id": ngo_user.id,
                "name": req.ngo_name or ngo_user.full_name,
                "distance_km": req.radius_km, # Mocking distance by using radius
                "need": req.required_meals,
                "vehicle": "auto" if req.required_meals < 50 else "van",
                "storage": req.storage_type or "serve now",
                "verified": ngo_user.is_verified,
            })
            
    # Fallback to a single generic NGO if database is completely empty
    if not profiles:
        profiles = [{
            "id": 0, "name": "General Local Shelter", "distance_km": 5.0,
            "need": 100, "vehicle": "van", "storage": "serve now", "verified": True
        }]

    ranked: List[Dict[str, Any]] = []
    for ngo in profiles:
        need = ngo.get("need", 100)
        distance = ngo.get("distance_km", ngo.get("distance", 1))
        verified = ngo.get("verified", False)

        quantity_fit = 100 - abs(need - meals) / max(need, meals, 1) * 45
        urgency_boost = (18 / distance) if hours <= 1 else (8 / distance)
        match_score = int(
            min(
                99,
                safety_score * 0.35
                + quantity_fit * 0.38
                + urgency_boost
                + (7 if verified else 0),
            )
        )
        ranked.append({**ngo, "match_score": match_score})

    ranked.sort(key=lambda x: x["match_score"], reverse=True)
    return ranked
