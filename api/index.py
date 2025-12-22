import os
import json
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from functools import wraps
from werkzeug.security import check_password_hash
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__, template_folder='../templates')

# --- CONFIGURATION ---
# Use Environment Variable for security on Vercel
app.secret_key = os.environ.get('SECRET_KEY', 'default_local_secret')
ADMIN_USERNAME = "admin"
# Hash for "password123"
ADMIN_PASSWORD_HASH = "scrypt:32768:8:1$9DNbv5RtIf9tq3V0$4b1f2fb08a2bf17fcf7b946033f0fe7a6eb0f4206af4d17ac43356398816d8ab3c858cf4f9d03db6a3d66a72f1491f17398130c92a266717af2fe8c06174c210"

# --- FIREBASE SETUP ---
# We check if Firebase is already initialized to avoid errors during hot-reload
if not firebase_admin._apps:
    # Load credentials from Vercel Environment Variable
    firebase_creds_json = os.environ.get('FIREBASE_CREDENTIALS')
    
    if firebase_creds_json:
        cred_dict = json.loads(firebase_creds_json)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    else:
        print("WARNING: FIREBASE_CREDENTIALS not found in env vars")

db = firestore.client()

# --- DEFAULT DATA ---
DEFAULT_STATE = {
    "team1_name": "India",
    "team1_logo": "https://flagcdn.com/in.svg",
    "team2_name": "Australia", 
    "team2_logo": "https://flagcdn.com/au.svg",
    "score": 0,
    "wickets": 0,
    "overs": 0.0,
    "target": 200,
    "bat1_name": "Batter 1", 
    "bat1_active": True,
    "bat2_name": "Batter 2", 
    "bat2_active": False,
    "bowler_name": "Bowler"
}

LOGO_OPTIONS = [
    {"label": "404", "url": "https://raw.githubusercontent.com/karthikparambil/football-scoreboard/refs/heads/main/static/logos/404.png"},
    {"label": "cloud", "url": "https://raw.githubusercontent.com/karthikparambil/football-scoreboard/refs/heads/main/static/logos/cloud.png"},
    {"label": "diffenso", "url": "https://raw.githubusercontent.com/karthikparambil/football-scoreboard/refs/heads/main/static/logos/diffenso.png"},
    {"label": "echo", "url": "https://raw.githubusercontent.com/karthikparambil/football-scoreboard/refs/heads/main/static/logos/echo.png"},
    {"label": "los", "url": "https://raw.githubusercontent.com/karthikparambil/football-scoreboard/refs/heads/main/static/logos/los.png"},
    {"label": "offenso", "url": "https://raw.githubusercontent.com/karthikparambil/football-scoreboard/refs/heads/main/static/logos/offenso.png"},
    {"label": "rootkits", "url": "https://raw.githubusercontent.com/karthikparambil/football-scoreboard/refs/heads/main/static/logos/rootkits.png"},
    {"label": "soccer", "url": "https://raw.githubusercontent.com/karthikparambil/football-scoreboard/refs/heads/main/static/logos/soccer.png"},
    {"label": "sp", "url": "https://raw.githubusercontent.com/karthikparambil/football-scoreboard/refs/heads/main/static/logos/sp.png"},
    {"label": "torrent", "url": "https://raw.githubusercontent.com/karthikparambil/football-scoreboard/refs/heads/main/static/logos/torrent.png"},
    {"label": "united", "url": "https://raw.githubusercontent.com/karthikparambil/football-scoreboard/refs/heads/main/static/logos/united.png"},
    {"label": "yg", "url": "https://raw.githubusercontent.com/karthikparambil/football-scoreboard/refs/heads/main/static/logos/yg.png"},
]

# --- HELPERS ---
def get_db_data():
    """Fetches data from Firestore. If doc doesn't exist, creates it."""
    doc_ref = db.collection('matches').document('live')
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        # Initialize DB with default data
        doc_ref.set(DEFAULT_STATE)
        return DEFAULT_STATE

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash("Please log in first.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'logged_in' in session:
        return redirect(url_for('admin'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            flash("Invalid credentials.", "error")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/admin')
@login_required 
def admin():
    return render_template('admin.html', logo_options=LOGO_OPTIONS)

@app.route('/api/data', methods=['GET'])
def get_data():
    data = get_db_data()
    return jsonify(data)

@app.route('/api/update', methods=['POST'])
@login_required
def update_data():
    try:
        data = request.json
        # Update Firestore
        doc_ref = db.collection('matches').document('live')
        doc_ref.update(data)
        
        # Return the updated full object
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# For Vercel, we expose the app as 'app'
if __name__ == '__main__':
    app.run(debug=True)
