# ResQmeal Python Backend Walkthrough

The ResQmeal Python Backend is a RESTful API built with **Flask** and configured to run on a JSON flat-file storage engine (`db.json`) as a database abstraction layer. This allows rapid client-side prototyping and future scalability to PostgreSQL.

---

## Technical Architecture

### 1. Folder Structure
```text
backend/
├── app.py                  # Flask Application Factory
├── config.py               # Application Config (JWT, Secrets)
├── db_store.py             # JSON Flat-File Database Core
├── db.json                 # Flat-file database (created at runtime/seeding)
├── requirements.txt        # Backend dependencies
├── run.py                  # Dev Web Server entry point
├── seed.py                 # Seeds database with mock data
├── routes/                 # Blueprint controllers
│   ├── auth.py             # User register, OTP, JWT Login
│   ├── chat.py             # Privacy-guarded AI Help chatbot
│   ├── donations.py        # Analyze food safety, Smart Match
│   ├── impact.py           # CO2 prevented, meals saved statistics
│   ├── ngo.py              # Donor ranking for NGO requests
│   └── routes_tracking.py  # Optimal routes, countdown timer
└── services/               # Replicated business logics
    ├── donor_ranking.py    # Donor ranking for NGO queries
    ├── matching.py         # NGO matching logic
    └── safety_score.py     # AI Food Safety score formula
```

---

## Key Backend Implementations

### Flat-File Storage Engine (`db_store.py`)
All database transactions are structured inside a single central service (`db_store.py`) that acts as an ORM abstraction.
- **Reading Data**: Reads `db.json` and parses it into JSON dictionaries.
- **Writing Data**: Performs locking/safeguard and writes back elements as atomic transactions.
- **Future Migration**: Since blueprints only call `db_store` helper functions (like `load_db()`, `save_db()`), updating to PostgreSQL only requires changing the queries inside `db_store.py`.

### AI-Driven Services
- **Safety Scoring (`services/safety_score.py`)**: Computes a dynamic safety score based on the storage packaging, temperature conditions, food volume, and remaining safety hours.
- **NGO Matching (`services/matching.py`)**: Sorts and calculates matching scores for local NGOs based on verified status, pickup capacity, storage fit, and distance.
- **Donor Ranking (`services/donor_ranking.py`)**: Computes priority ratings for neighborhood restaurants and weddings halls to match NGO meal counts.

---

## API Documentation

### 👥 Authentication Blueprints
- **`POST /api/auth/send-otp`**
  - Sends a simulated 6-digit OTP code to the requested phone number.
  - Returns `otp_code` in the JSON response when in Development Mode.
- **`POST /api/auth/verify-otp`**
  - Verifies the OTP, hashes the password using Werkzeug security, saves the user, and credentials a JWT token.
- **`POST /api/auth/login`**
  - Authenticates username, checks hashed passwords, validates role, and issues a JWT token.

### 🍎 Donation & NGO APIs
- **`POST /api/donations`**
  - Creates a new surplus donation post, calculates the AI safety score, and runs matching filters next to available NGOs.
- **`POST /api/ngo/requests`**
  - Registers shelter demand requests post, calculates estimation buffers, and prioritizes local donors within coordinates.
- **`GET /api/routes`**
  - Returns optimized route sequences, stops, expected arrival times, and verification tokens.

### 💬 Privacy-Guarded AI Bot (`/api/chat`)
- Matches questions against internal app definitions.
- Protects personal data fields (passwords, contacts, OTPs, usernames) and returns safety warnings if query tries to access them.

---

## How to Run & Verify

1. **Configure Environment Variables**:
   Create a `.env` file using the template `.env.example`:
   ```bash
   cp .env.example .env
   ```
2. **Install Modules**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Seed Database**:
   ```bash
   python seed.py
   ```
4. **Boot Up Flask server**:
   ```bash
   python run.py
   ```
   *Server starts running on: `http://localhost:5000`*
5. **Open Frontend**:
   Serve `frontend/index ResQmeal - updated auth.html` in your browser. The frontend automatically runs check calls to the local REST API. If the server is offline, the interface falls back to localStorage/sessionStorage.

while the backend is running, open a new terminal(the backend terminal should be running too)
python -m http.server 8000 --directory "f:\ResQmeal-1\frontend"
 open this link: http://localhost:8000/
in web browser. now ur website is working.
