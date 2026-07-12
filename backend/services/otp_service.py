"""
services/otp_service.py

OTP generation, storage and verification.

In OTP_DEV_MODE=true (default) the raw OTP is returned in the API response
so the frontend can display it exactly like the current demo.
When OTP_DEV_MODE=false, the OTP would be sent via SMS (Twilio stub below).
"""

from __future__ import annotations

import random
import string
from datetime import datetime, timedelta

from config import Config
from db_store import load_db, save_db, next_id, now_iso


# ── Helpers ───────────────────────────────────────────────────────────────────

def _generate_code(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def _expiry_iso() -> str:
    expiry = datetime.utcnow() + timedelta(seconds=Config.OTP_EXPIRY_SECONDS)
    return expiry.isoformat() + "Z"


def _is_expired(otp_record: dict) -> bool:
    try:
        expires_at = datetime.fromisoformat(otp_record["expires_at"].replace("Z", ""))
    except (KeyError, ValueError):
        return True
    return datetime.utcnow() > expires_at


# ── Public API ────────────────────────────────────────────────────────────────

def create_otp(phone: str) -> dict:
    """
    Generate a new 6-digit OTP for the given phone number.

    - Invalidates any previous unused OTPs for this phone.
    - Returns a dict with ``otp_code`` (in dev mode) and ``expires_in`` seconds.
    """
    db = load_db()
    code = _generate_code()
    expiry = _expiry_iso()

    # Invalidate old OTPs for this phone
    for record in db["otps"]:
        if record["phone"] == phone and not record.get("used"):
            record["used"] = True

    new_record = {
        "id": next_id(db["otps"]),
        "phone": phone,
        "otp_code": code,
        "expires_at": expiry,
        "used": False,
        "created_at": now_iso(),
    }
    db["otps"].append(new_record)
    save_db(db)

    # Simulate sending SMS here (Twilio integration point)
    # if not Config.OTP_DEV_MODE:
    #     send_sms(phone, f"Your ResQmeal OTP is {code}. Valid for 5 minutes.")

    result: dict = {"expires_in": Config.OTP_EXPIRY_SECONDS}
    if Config.OTP_DEV_MODE:
        result["otp_code"] = code  # Show in response for demo
    return result


def verify_otp(phone: str, code: str) -> bool:
    """
    Verify that `code` is the most recent valid OTP for `phone`.
    Marks the OTP as used on success.
    """
    db = load_db()
    # Find the latest valid OTP for this phone
    matching = [
        r for r in db["otps"]
        if r["phone"] == phone
        and r["otp_code"] == code
        and not r.get("used")
        and not _is_expired(r)
    ]
    if not matching:
        return False

    # Mark as used
    otp_id = matching[-1]["id"]
    for record in db["otps"]:
        if record["id"] == otp_id:
            record["used"] = True
            break

    save_db(db)
    return True
