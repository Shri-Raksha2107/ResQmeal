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
from extensions import db
from models import OTP


# ── Helpers ───────────────────────────────────────────────────────────────────

def _generate_code(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def _expiry_iso() -> datetime:
    return datetime.utcnow() + timedelta(seconds=Config.OTP_EXPIRY_SECONDS)


def _is_expired(otp_record: OTP) -> bool:
    if not otp_record.expires_at:
        return True
    return datetime.utcnow() > otp_record.expires_at


# ── Public API ────────────────────────────────────────────────────────────────

def create_otp(phone: str) -> dict:
    """
    Generate a new 6-digit OTP for the given phone number.

    - Invalidates any previous unused OTPs for this phone.
    - Returns a dict with ``otp_code`` (in dev mode) and ``expires_in`` seconds.
    """
    code = _generate_code()
    expiry = _expiry_iso()

    # Invalidate old OTPs for this phone
    OTP.query.filter_by(phone=phone, used=False).update({"used": True})

    new_record = OTP(
        phone=phone,
        otp_code=code,
        expires_at=expiry,
        used=False,
    )
    db.session.add(new_record)
    db.session.commit()

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
    # Find the latest valid OTP for this phone
    record = OTP.query.filter_by(
        phone=phone,
        otp_code=code,
        used=False
    ).order_by(OTP.id.desc()).first()

    if not record or _is_expired(record):
        return False

    # Mark as used
    record.used = True
    db.session.commit()
    return True
