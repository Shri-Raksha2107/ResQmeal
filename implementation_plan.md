# ResQmeal – Python + PostgreSQL Backend

## Overview

ResQmeal is an AI-powered Smart Food Rescue Network. The current codebase is a fully self-contained single-page HTML/JS prototype that stores users in `localStorage`. This plan replaces that with a real Python (Flask) backend backed by PostgreSQL, then integrates it into the existing HTML frontend.

---

## Architecture

```
Browser (HTML/JS)
     │  fetch() API calls (JSON)
     ▼
Flask REST API  (Python 3.11+, Flask 3.x)
     │  JSON file (db.json) — swap for PostgreSQL later
     ▼
db.json  (flat-file store, drop-in replaceable)
```

No React/Vue rewrite – only the `fetch` calls in the HTML are redirected to the real API.  
PostgreSQL will be wired in later; `db_store.py` abstracts all reads/writes so the swap is trivial.

---

## Proposed Changes

### 1 – Backend (`f:\ResQmeal-1\backend\`)

#### [NEW] `app.py` – Flask application factory & entry point
- Creates the Flask app, registers blueprints, and starts the dev server.

#### [NEW] `config.py` – Configuration
- `DATABASE_URL` (PostgreSQL connection string)
- `SECRET_KEY` (JWT signing key)
- `OTP_EXPIRY_SECONDS = 300`
- `TWILIO_*` env vars (optional SMS; simulation mode if absent)

#### [NEW] `extensions.py`
- Initialises `SQLAlchemy`, `Flask-Migrate`, `Flask-JWT-Extended`, `Flask-CORS`.

#### [NEW] `db_store.py` – Flat-file JSON store (PostgreSQL-ready abstraction)

Provides `load_db()` / `save_db()` helpers. All routes call these — swapping for SQLAlchemy later only requires changing this one file.

**db.json collections:**

| Collection | Fields |
|---|---|
| `users` | id, full_name, username, phone, email, password_hash, role, is_verified, created_at |
| `otps` | id, phone, otp_code, expires_at, used |
| `donations` | id, donor_id, donor_type, food_name, meals, hours, temperature, packaging, location, photo_path, safety_score, status, created_at |
| `ngo_requests` | id, ngo_id, ngo_name, people_needed, radius_km, storage_type, notes, status, created_at |
| `matches` | id, donation_id, ngo_request_id, match_score, status, created_at |
| `impact` | meals_saved, co2_kg, money_saved_inr, fast_rescues_pct, weekly_chart, leaderboard |

#### [NEW] `routes/auth.py` – Authentication endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/send-otp` | Generate 6-digit OTP, store in DB (TTL 5 min), return OTP in dev mode |
| POST | `/api/auth/verify-otp` | Validate OTP, create user, return JWT |
| POST | `/api/auth/login` | Validate credentials, return JWT |
| GET | `/api/auth/me` | Return current user profile (JWT required) |
| POST | `/api/auth/logout` | Client-side only; endpoint for logging |

#### [NEW] `routes/donations.py` – Donor operations

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/donations` | Create a new donation + run safety scoring algorithm |
| GET | `/api/donations` | List donations (filterable by status, donor) |
| GET | `/api/donations/<id>` | Get single donation with matches |
| PATCH | `/api/donations/<id>/status` | Update status |
| POST | `/api/donations/<id>/analyze` | Re-run AI matching and return ranked NGO matches |

#### [NEW] `routes/ngo.py` – NGO operations

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/ngo/requests` | Post a food request + run donor ranking |
| GET | `/api/ngo/requests` | List requests |
| GET | `/api/ngo/requests/<id>` | Get request + ranked donors list |

#### [NEW] `routes/routes_tracking.py` – Routes & tracking

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/routes` | Get optimized route stops for a donation |
| POST | `/api/routes/<donation_id>/confirm-pickup` | Mark pickup confirmed |

#### [NEW] `routes/impact.py` – Impact dashboard

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/impact/stats` | Aggregate stats (meals, CO2, money, fast rescues) |
| GET | `/api/impact/chart` | Weekly meals-saved chart data |
| GET | `/api/impact/leaderboard` | Top donors / NGOs / volunteers |

#### [NEW] `routes/chat.py` – AI chat proxy

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/chat` | Accepts `{question}`, runs keyword matching + returns answer |

#### [NEW] `services/safety_score.py`
- Replicates the frontend scoring formula in Python (pure function, unit-testable).

#### [NEW] `services/matching.py`
- Ranks NGOs against a donation, returns sorted list with match %.

#### [NEW] `services/donor_ranking.py`
- Ranks donors for an NGO request, returns sorted list with priority score.

#### [NEW] `services/otp_service.py`
- Generates OTP, stores it, optionally sends via Twilio SMS; returns OTP in dev mode.

#### [NEW] `requirements.txt`
```
Flask>=3.0
Flask-JWT-Extended>=4.6
Flask-CORS>=4.0
python-dotenv>=1.0
Werkzeug>=3.0
```

#### [NEW] `.env.example`
```
SECRET_KEY=change_me_in_production
JWT_SECRET_KEY=another_secret
OTP_DEV_MODE=true
```

---

### 2 – Frontend Integration (`f:\ResQmeal-1\`)

#### [MODIFY] `index ResQmeal - updated auth.html`

- Replace the `localStorage`-based `getUsers()` / `saveUsers()` / `login()` / `sendOtp()` / `verifyOtpAndCreateAccount()` functions with `fetch()` calls to the new API.
- Add a JWT token store (`sessionStorage`) and attach `Authorization: Bearer <token>` on protected calls.
- Redirect `scoreDonation()` → `POST /api/donations` (creates + analyzes).
- Redirect `rankDonors()` → `POST /api/ngo/requests`.
- Redirect `renderImpact()` → `GET /api/impact/stats` + chart + leaderboard.
- Keep the original fallback logic so the page still works if the backend is offline.

---

### 3 – Setup Scripts

#### [NEW] `seed.py`
Populates `db.json` with sample donors, NGOs, donations, impact stats, and leaderboard data.

#### [NEW] `run.py`
Convenience entry point: `python run.py` to start Flask on port 5000 in debug mode.

---

## Verification Plan

### Automated / CLI
1. `python -m pytest backend/tests/` – unit tests for safety score, matching, OTP generation.
2. `flask db upgrade` – migrations apply without errors.
3. `python seed.py` – seed data loads.
4. `python run.py` – server starts on port 5000.

### Browser Tests
5. Open the HTML page → sign up → verify OTP → log in → all tabs work with live data.
6. Post a donation → AI score and NGO matches appear from the backend.
7. Impact dashboard shows database-populated stats.

---

## Decisions (Confirmed)

- ✅ No PostgreSQL yet — flat JSON file store, swappable later
- ✅ OTP simulated — returned in API response (dev mode)
- ✅ Photo uploads stored locally in `backend/static/uploads/`
