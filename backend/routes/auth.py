"""routes/auth.py – Authentication endpoints."""

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from db_store import load_db, save_db, next_id, now_iso
from services.otp_service import create_otp, verify_otp

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# ── POST /api/auth/send-otp ──────────────────────────────────────────────────

@auth_bp.route("/send-otp", methods=["POST"])
def send_otp():
    """
    Validate signup fields (except OTP), generate an OTP and return it.

    Body (JSON):
        full_name, username, phone, email, password, role
    """
    body = request.get_json(silent=True) or {}
    required = ["full_name", "username", "phone", "email", "password", "role"]
    missing = [f for f in required if not body.get(f, "").strip()]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    phone = body["phone"].strip()
    username = body["username"].strip().lower()

    # Check uniqueness
    db = load_db()
    if any(u["username"].lower() == username for u in db["users"]):
        return jsonify({"error": "That username is already registered."}), 409
    if any(u["phone"] == phone for u in db["users"]):
        return jsonify({"error": "That phone number is already registered."}), 409

    otp_result = create_otp(phone)
    return jsonify({"message": "OTP sent.", **otp_result}), 200


# ── POST /api/auth/verify-otp ────────────────────────────────────────────────

@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp_and_register():
    """
    Verify OTP → create user → return JWT.

    Body (JSON):
        full_name, username, phone, email, password, role, otp_code
    """
    body = request.get_json(silent=True) or {}
    otp_code = body.get("otp_code", "").strip()
    phone = body.get("phone", "").strip()

    if not otp_code or not phone:
        return jsonify({"error": "phone and otp_code are required."}), 400

    if not verify_otp(phone, otp_code):
        return jsonify({"error": "Invalid or expired OTP. Please try again."}), 400

    # Create user
    db = load_db()
    new_user = {
        "id": next_id(db["users"]),
        "full_name": body.get("full_name", "").strip(),
        "username": body.get("username", "").strip().lower(),
        "phone": phone,
        "email": body.get("email", "").strip(),
        "password_hash": generate_password_hash(body.get("password", "")),
        "role": body.get("role", "donor"),
        "is_verified": True,
        "created_at": now_iso(),
    }
    db["users"].append(new_user)
    save_db(db)

    token = create_access_token(identity=str(new_user["id"]))
    return jsonify({
        "message": "Account created successfully.",
        "token": token,
        "user": _safe_user(new_user),
    }), 201


# ── POST /api/auth/login ──────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticate with username + password + role.

    Body (JSON):
        username, password, role
    """
    body = request.get_json(silent=True) or {}
    username = body.get("username", "").strip().lower()
    password = body.get("password", "")
    role = body.get("role", "")

    if not username or not password or not role:
        return jsonify({"error": "username, password, and role are required."}), 400

    db = load_db()
    user = next(
        (u for u in db["users"] if u["username"].lower() == username and u["role"] == role),
        None,
    )
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid username, password, or user type."}), 401

    token = create_access_token(identity=str(user["id"]))
    return jsonify({"token": token, "user": _safe_user(user)}), 200


# ── GET /api/auth/me ─────────────────────────────────────────────────────────

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """Return the current user's profile (JWT required)."""
    user_id = int(get_jwt_identity())
    db = load_db()
    user = next((u for u in db["users"] if u["id"] == user_id), None)
    if not user:
        return jsonify({"error": "User not found."}), 404
    return jsonify(_safe_user(user)), 200


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_user(user: dict) -> dict:
    """Return user dict without the password hash."""
    return {k: v for k, v in user.items() if k != "password_hash"}
