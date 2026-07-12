"""
db_store.py – Flat JSON file persistence layer.

All data is kept in a single db.json file.  Every route calls load_db() at the
start and save_db() after mutation.  Thread-safety is provided by a simple
file-level lock so concurrent dev-server requests don't corrupt data.

When PostgreSQL support is added later, replace this module's implementation
while keeping the same public interface: load_db() / save_db() / next_id().
"""

import json
import os
import threading
from datetime import datetime
from config import Config

_lock = threading.Lock()

_DEFAULT_DB: dict = {
    "users": [],
    "otps": [],
    "donations": [],
    "ngo_requests": [],
    "matches": [],
    "impact": {
        "meals_saved": 18420,
        "co2_kg": 6800,
        "money_saved_inr": 490000,
        "fast_rescues_pct": 91,
        "weekly_chart": [
            {"day": "Mon", "meals": 22},
            {"day": "Tue", "meals": 28},
            {"day": "Wed", "meals": 31},
            {"day": "Thu", "meals": 26},
            {"day": "Fri", "meals": 52},
            {"day": "Sat", "meals": 46},
            {"day": "Sun", "meals": 35},
        ],
        "leaderboard": [
            {"name": "Sri Devi Wedding Hall", "type": "donor", "meals": 2940},
            {"name": "Green Leaf Restaurant",  "type": "donor", "meals": 1880},
            {"name": "Volunteer Kavya",         "type": "volunteer", "meals": 126},
            {"name": "City Hostel Mess",        "type": "donor", "meals": 1105},
        ],
    },
}


def _ensure_file() -> None:
    """Create db.json with defaults if it does not exist yet."""
    if not os.path.exists(Config.DB_FILE):
        os.makedirs(os.path.dirname(Config.DB_FILE), exist_ok=True)
        with open(Config.DB_FILE, "w", encoding="utf-8") as fh:
            json.dump(_DEFAULT_DB, fh, indent=2, default=str)


def load_db() -> dict:
    """Return the entire database as a Python dict."""
    _ensure_file()
    with _lock:
        with open(Config.DB_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)


def save_db(data: dict) -> None:
    """Write the entire database back to disk."""
    _ensure_file()
    with _lock:
        with open(Config.DB_FILE, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, default=str)


def next_id(collection: list) -> int:
    """Return a simple auto-increment ID for the given collection list."""
    if not collection:
        return 1
    return max(item.get("id", 0) for item in collection) + 1


def now_iso() -> str:
    """Current UTC timestamp as ISO-8601 string."""
    return datetime.utcnow().isoformat() + "Z"
