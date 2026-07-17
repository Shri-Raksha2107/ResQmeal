"""
services/donor_ranking.py

Donor ranking and filtering for NGOs.
Ranks potential donors based on their donation history and current active donations.
"""

from typing import List, Dict, Any

from extensions import db
from models import User, Donation

def rank_donors(radius_km: float = 5.0) -> List[Dict[str, Any]]:
    """
    Rank donors dynamically based on their actual donation history.

    Parameters
    ----------
    radius_km : The search radius requested by the NGO.

    Returns
    -------
    List of donor dictionaries sorted by urgency and average meals.
    """
    donors_query = User.query.filter_by(role="donor").all()
    ranked_donors = []

    for donor in donors_query:
        # Get all donations for this donor
        donations = Donation.query.filter_by(donor_id=donor.id).all()
        
        total_meals = sum(d.meals for d in donations)
        avg_meals = int(total_meals / len(donations)) if donations else 0
        
        # Calculate active urgency based on any currently active donations
        active = [d for d in donations if d.status == "active"]
        if active:
            avg_hours = sum(d.hours for d in active) / len(active)
            if avg_hours <= 2:
                urgency = "high"
            elif avg_hours <= 5:
                urgency = "medium"
            else:
                urgency = "low"
        else:
            urgency = "none"

        # Mock distance for demonstration as we don't have geo-coords
        distance = 2.0  

        ranked_donors.append({
            "id": donor.id,
            "name": donor.full_name,
            "type": "restaurant" if "restaurant" in donor.full_name.lower() else "event",
            "distance_km": distance,
            "avg_meals": avg_meals,
            "today_meals": sum(d.meals for d in active),
            "reliability": 98 if donor.is_verified else 85,
            "urgency": urgency,
            "verified": donor.is_verified,
        })

    # Sort primarily by urgency, then reliability
    urgency_val = {"high": 3, "medium": 2, "low": 1, "none": 0}
    ranked_donors.sort(
        key=lambda x: (urgency_val.get(x["urgency"], 0), x["reliability"]),
        reverse=True
    )

    return ranked_donors
