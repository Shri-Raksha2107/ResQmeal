"""
services/matching.py

NGO matching service.
Ranks the registered NGOs (or those supplied as seed data) against a donation
and returns a sorted list with match percentages.
"""

from __future__ import annotations
from typing import List, Dict, Any


# Seed NGO profiles used when no NGOs are found in the database.
_SEED_NGOS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "name": "Hope Shelter",
        "distance_km": 1.8,
        "need": 110,
        "vehicle": "van",
        "storage": "serve now",
        "verified": True,
    },
    {
        "id": 2,
        "name": "Anbu Old Age Home",
        "distance_km": 2.6,
        "need": 70,
        "vehicle": "auto",
        "storage": "hot meals",
        "verified": True,
    },
    {
        "id": 3,
        "name": "Little Hands Home",
        "distance_km": 4.3,
        "need": 95,
        "vehicle": "bike + car",
        "storage": "sealed only",
        "verified": True,
    },
]


def rank_ngos(
    safety_score: int,
    meals: int,
    hours: int,
    ngo_profiles: List[Dict[str, Any]] | None = None,
) -> List[Dict[str, Any]]:
    """
    Rank NGOs for a given donation.

    Parameters
    ----------
    safety_score  : pre-computed safety score (0–100)
    meals         : number of meal portions in the donation
    hours         : hours remaining before expiry
    ngo_profiles  : list of NGO dicts (uses seed data if None / empty)

    Returns
    -------
    List of NGO dicts sorted descending by match_score, each augmented with
    a ``match_score`` field (0–99).
    """
    profiles = ngo_profiles if ngo_profiles else _SEED_NGOS

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
