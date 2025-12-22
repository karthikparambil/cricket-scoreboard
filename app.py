import os
import json
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

# FIREBASE IMPORTS
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# SECURITY CONFIGURATION
# In production, use os.environ.get('SECRET_KEY')
app.secret_key = os.environ.get('SECRET_KEY', 'change_this_to_a_complex_random_string')

# CREDENTIALS
ADMIN_USERNAME = "admin"
# Hash for "password123"
ADMIN_PASSWORD_HASH = "scrypt:32768:8:1$9DNbv5RtIf9tq3V0$4b1f2fb08a2bf17fcf7b946033f0fe7a6eb0f4206af4d17ac43356398816d8ab3c858cf4f9d03db6a3d66a72f1491f17398130c92a266717af2fe8c06174c210"

# --- FIREBASE SETUP ---
# We check if Firebase is already initialized to avoid errors during Vercel's hot-reloading
if not firebase_admin._apps:
    # We will store the JSON content in an Environment Variable named FIREBASE_CREDENTIALS
    firebase_creds_str = os.environ.get('FIREBASE_CREDENTIALS')
    
    if firebase_creds_str:
        cred_dict = json.loads(firebase_creds_str)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    else:
        print("WARNING: FIREBASE_CREDENTIALS environment variable not found.")

# Initialize Firestore Client
db = firestore.client() if firebase_admin._apps else None

# CONSTANTS
COLLECTION_NAME = 'scoreboard'
DOCUMENT_NAME = 'current_match'

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

# DEFAULT STATE (Used if database is empty)
DEFAULT_STATE = {
    "team1_name": "India",
    "team1_logo": "https://flagcdn.com/in.svg",
    "team2_name": "Australia", 
    "team2_logo": "https://flagcdn.com/au.svg",
    "score": 0,
    "wickets": 0,
    "overs": 0.0,
    "target": 0,
    "bat1_name": "Batsman 1", 
    "bat1_active": True,
    "bat2_name": "Batsman 2", 
    "bat2_active": False,
    "bowler_name": "Bowler"
}

# --- DATABASE HELPER FUNCTIONS ---
def get_match_data():
    """Fetches data from Firestore. Returns default if db fails or is empty."""
    if not db:
        return DEFAULT_STATE
    
    try:
        doc_ref = db.collection(COLLECTION_NAME).document(DOCUMENT_NAME)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            # Create the doc if it doesn't exist
            doc_ref.set(DEFAULT_STATE)
            return DEFAULT_STATE
    except Exception as e:
        print(f"Error reading DB: {e}")
        return DEFAULT_STATE

def update_match_data(new_data):
    """Updates Firestore with new data."""
    if not db:
        return False
    try:
        doc_ref = db.collection(COLLECTION_NAME).document(DOCUMENT_NAME)
        doc_ref.update(new_data)
        return True
    except Exception as e:
        print(f"Error updating DB: {e}")
        return False

# --- ROUTES ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash("Please log in to access the admin panel.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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
            flash("Invalid credentials. Please try again.", "error")
            
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
    # Fetch fresh data from Firebase every time
    current_data = get_match_data()
    return jsonify(current_data)

@app.route('/api/update', methods=['POST'])
@login_required
def update_data():
    data = request.json
    success = update_match_data(data)
    
    if success:
        # Return the updated state so frontend stays in sync
        return jsonify({"status": "success", "data": data})
    else:
        return jsonify({"status": "error", "message": "Database update failed"}), 500

# Vercel needs the app object to be exposed
app = app

if __name__ == '__main__':
    app.run(debug=False, port=5000)
