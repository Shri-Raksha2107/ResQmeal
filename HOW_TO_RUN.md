# How to Run ResQmeal

To get the full ResQmeal platform running seamlessly, you need to start two things:
1. The Backend (Flask API)
2. The Frontend (HTML/JS/CSS)

You will need to open **two separate terminal windows**.

---

### Terminal 1: Start the Backend (API Server)

1. Open your first terminal and make sure you are inside the `ResQmeal-1` project folder.
2. Navigate into the backend folder:
   ```bash
   cd backend
   ```
3. Install the dependencies (you only need to do this once):
   ```bash
   pip install -r requirements.txt
   ```
4. Start the Flask server:
   ```bash
   python run.py
   ```
   *You should see output saying it is running on `http://127.0.0.1:5000`.*

---

### Terminal 2: Start the Frontend (Web Server)

1. Open a **new, second terminal** and make sure you are inside the `ResQmeal-1` project folder.
2. Navigate into the frontend folder:
   ```bash
   cd frontend
   ```
3. Start the Python local web server on port 8000 (do not include any parentheses):
   ```bash
   python -m http.server 8000
   ```
4. Open your web browser and go to this exact address:
   [http://localhost:8000/index ResQmeal - updated auth.html](http://localhost:8000/index%20ResQmeal%20-%20updated%20auth.html)

---

### Troubleshooting

- **"No matching distribution found for requirements.txt"**: This means you typed `pip install requirements.txt` without the `-r` flag. It must be `pip install -r requirements.txt`.
- **"Could not open requirements file"**: This means you are in the wrong folder. Make sure you typed `cd backend` first.
- **Frontend isn't talking to Backend**: Make sure BOTH terminals are running at the same time. The frontend expects the backend to be running at `http://localhost:5000`.
