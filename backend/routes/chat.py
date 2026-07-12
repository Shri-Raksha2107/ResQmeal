"""routes/chat.py – AI chat proxy endpoint."""

from flask import Blueprint, request, jsonify

chat_bp = Blueprint("chat", __name__, url_prefix="/api")

# Knowledge base mirrored from the frontend JS
_KNOWLEDGE: list[dict] = [
    {
        "keys": ["login", "log in", "signin", "sign in", "username", "password"],
        "answer": "Login uses Username, Password, and User Type. The API checks those values against registered accounts in the database before returning a JWT token.",
    },
    {
        "keys": ["signup", "sign up", "register", "account", "create"],
        "answer": "Sign Up collects Full Name, Username, Phone Number, Email, Password, Confirm Password, and User Type. The account is created only after OTP verification.",
    },
    {
        "keys": ["otp", "verify", "verification", "phone"],
        "answer": "A 6-digit OTP is generated for the entered phone number during sign up. In dev mode the OTP is returned in the API response so the flow can be tested without an SMS service.",
    },
    {
        "keys": ["user type", "role", "ngo", "food donor", "donor"],
        "answer": "There are two user types: NGO and Food Donor. Food Donors use donation, route, and impact tools. NGOs use demand, route, and impact tools.",
    },
    {
        "keys": ["donation", "surplus", "post food", "food safety", "safety score", "analyze"],
        "answer": "The Donor Rescue section lets donors post surplus food details. The backend computes an AI Food Safety Score and returns ranked NGO matches.",
    },
    {
        "keys": ["match", "matches", "smart match", "priority", "nearby"],
        "answer": "Smart matching considers food safety score, quantity fit, urgency, distance, and NGO verification status.",
    },
    {
        "keys": ["request", "demand", "shelter", "people", "radius"],
        "answer": "The NGO Demand section lets NGOs request food by entering the shelter name, people count, search radius, storage, and notes.",
    },
    {
        "keys": ["route", "tracking", "pickup", "qr", "delivery"],
        "answer": "Routes & Tracking shows optimised pickup stops, QR preview, pickup confirmation, expiry countdown, and NGO verification status.",
    },
    {
        "keys": ["impact", "dashboard", "meals saved", "co2", "leaderboard", "prediction"],
        "answer": "The Impact Dashboard shows meals saved, CO2 prevented, money saved, fast rescues, leftover prediction, and a leaderboard.",
    },
    {
        "keys": ["what is", "about", "website", "resqmeal", "food rescue"],
        "answer": "ResQmeal is an AI-powered Smart Food Rescue Network. It helps food donors share surplus food and helps NGOs find suitable nearby donations before food expires.",
    },
]

_PRIVATE_WORDS = [
    "personal", "private", "password", "email", "phone", "number", "contact",
    "username", "account details", "stored user", "all users", "localstorage",
    "sessionstorage", "otp",
]
_REVEAL_VERBS = r"\b(show|give|list|reveal|view|see|display|fetch|read|export)\b"


# ── POST /api/chat ────────────────────────────────────────────────────────────

@chat_bp.route("/chat", methods=["POST"])
def chat():
    """
    Simple keyword-based AI chat.

    Body (JSON):
        question  – user's question string
    Returns:
        { answer: str }
    """
    import re
    body = request.get_json(silent=True) or {}
    question = body.get("question", "").strip()
    if not question:
        return jsonify({"answer": "Please type a question."}), 200

    text = question.lower()

    # Privacy guard
    asks_private = any(w in text for w in _PRIVATE_WORDS) and bool(re.search(_REVEAL_VERBS, text))
    if asks_private:
        return jsonify({
            "answer": (
                "I can't reveal personal account details, stored user records, "
                "passwords, OTPs, phone numbers, or contacts."
            )
        }), 200

    # Score each knowledge entry
    scored = [
        {"answer": item["answer"], "score": sum(1 for k in item["keys"] if k in text)}
        for item in _KNOWLEDGE
    ]
    best = max(scored, key=lambda x: x["score"])
    if best["score"] > 0:
        return jsonify({"answer": best["answer"]}), 200

    return jsonify({
        "answer": (
            "I can only answer about this ResQmeal website: login, sign up, OTP, "
            "donor rescue, NGO demand, routes, tracking, and impact metrics."
        )
    }), 200
