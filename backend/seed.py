"""
seed.py – Populate db.json with realistic sample data.

Run once:
    python seed.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from werkzeug.security import generate_password_hash
from db_store import load_db, save_db, now_iso

def seed():
    db = load_db()

    # ── Users ──────────────────────────────────────────────────────────────────
    if not db["users"]:
        db["users"] = [
            {
                "id": 1,
                "full_name": "Sri Devi Wedding Hall",
                "username": "sridevi",
                "phone": "+919876543210",
                "email": "sridevi@foodrescue.org",
                "password_hash": generate_password_hash("donor123"),
                "role": "donor",
                "is_verified": True,
                "created_at": now_iso(),
            },
            {
                "id": 2,
                "full_name": "Hope Shelter NGO",
                "username": "hopeshelter",
                "phone": "+919876543211",
                "email": "hope@shelter.org",
                "password_hash": generate_password_hash("ngo123"),
                "role": "ngo",
                "is_verified": True,
                "created_at": now_iso(),
            },
            {
                "id": 3,
                "full_name": "Green Leaf Restaurant",
                "username": "greenleaf",
                "phone": "+919876543212",
                "email": "greenleaf@meals.com",
                "password_hash": generate_password_hash("donor123"),
                "role": "donor",
                "is_verified": True,
                "created_at": now_iso(),
            },
        ]
        print("[OK] Seeded users")

    # ── Sample donations ───────────────────────────────────────────────────────
    if not db["donations"]:
        db["donations"] = [
            {
                "id": 1,
                "donor_id": 1,
                "donor_type": "Wedding hall",
                "food_name": "Vegetable biryani and curd rice",
                "meals": 120,
                "hours": 4,
                "temperature": "room",
                "packaging": "sealed",
                "location": "Anna Nagar Function Hall",
                "photo_path": None,
                "safety_score": 82,
                "status": "active",
                "created_at": now_iso(),
            },
            {
                "id": 2,
                "donor_id": 3,
                "donor_type": "Restaurant",
                "food_name": "Idli, sambar and lemon rice",
                "meals": 45,
                "hours": 1,
                "temperature": "room",
                "packaging": "covered",
                "location": "Velachery Restaurant",
                "photo_path": None,
                "safety_score": 61,
                "status": "delivered",
                "created_at": now_iso(),
            },
        ]
        print("[OK] Seeded donations")

    # ── Sample NGO requests ────────────────────────────────────────────────────
    if not db["ngo_requests"]:
        db["ngo_requests"] = [
            {
                "id": 1,
                "ngo_id": 2,
                "ngo_name": "Hope Shelter",
                "people_needed": 85,
                "required_meals": 107,
                "radius_km": 5,
                "storage_type": "Can serve immediately",
                "notes": "Dinner requirement for shelter residents by 8:30 PM.",
                "status": "open",
                "created_at": now_iso(),
            },
        ]
        print("[OK] Seeded NGO requests")

    # ── Impact stats (already have defaults from db_store, just log) ──────────
    print("[OK] Impact stats already seeded with defaults")

    save_db(db)
    print("\n[OK] Seed complete. Run 'python run.py' to start the server.")

if __name__ == "__main__":
    seed()
