"""
services/donor_ranking.py

Priority ranking of food donors for an NGO request.
Mirrors the frontend JS priority formula.
"""

from __future__ import annotations
from typing import List, Dict, Any


# Seed donor profiles so the NGO tab always has data even before real donors sign up.
_SEED_DONORS: List[Dict[str, Any]] = [
    {"id": 1, "name": "Green Leaf Restaurant",  "distance_km": 1.4, "avg_meals": 38, "today_meals": 44, "urgency": 72},
    {"id": 2, "name": "Sri Devi Wedding Hall",  "distance_km": 2.1, "avg_meals": 130, "today_meals": 150, "urgency": 94},
    {"id": 3, "name": "City Hostel Mess",       "distance_km": 3.2, "avg_meals": 55, "today_meals": 49, "urgency": 64},
    {"id": 4, "name": "FreshMart Supermarket",  "distance_km": 4.7, "avg_meals": 28, "today_meals": 32, "urgency": 48},
]


def rank_donors(
    radius_km: float,
    donor_profiles: List[Dict[str, Any]] | None = None,
) -> List[Dict[str, Any]]:
    """
    Rank donors for an NGO food request.

    Parameters
    ----------
    radius_km      : maximum search radius in km
    donor_profiles : list of donor dicts (uses seed data if None / empty)

    Returns
    -------
    List of donor dicts within radius, sorted descending by priority_score,
    each augmented with a ``priority_score`` field.
    """
    profiles = donor_profiles if donor_profiles else _SEED_DONORS

    in_range = [d for d in profiles if d.get("distance_km", d.get("distance", 0)) <= radius_km]

    ranked: List[Dict[str, Any]] = []
    for donor in in_range:
        today = donor.get("today_meals", donor.get("today", 0))
        avg   = donor.get("avg_meals",   donor.get("avg",   0))
        urg   = donor.get("urgency", 50)
        dist  = donor.get("distance_km", donor.get("distance", 1))
        priority = int(round(today * 0.45 + avg * 0.35 + urg * 0.2 - dist * 3))
        ranked.append({**donor, "priority_score": priority})

    ranked.sort(key=lambda x: x["priority_score"], reverse=True)
    return ranked
