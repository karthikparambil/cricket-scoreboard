from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# SECURITY CONFIGURATION
# In Vercel, set this as an Environment Variable, or it will reset on every deploy
app.secret_key = os.environ.get('SECRET_KEY', 'fallback_secret_key_for_local_testing')

# --- FIREBASE SETUP ---
# We check if Firebase is already initialized to avoid errors in Vercel's hot-reload
if not firebase_admin._apps:
    # On Vercel, we will paste the JSON content into an Environment Variable named FIREBASE_CREDS
    creds_json = os.environ.get('FIREBASE_CREDS')
    
    if creds_json:
        cred_dict = json.loads(creds_json)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    else:
        # Fallback for local testing if you have the file locally
        try:
            cred = credentials.Certificate("firebase_credentials.json")
            firebase_admin.initialize_app(cred)
        except:
            print("WARNING: Firebase credentials not found.")

db = firestore.client()

# --- CONSTANTS ---
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = "scrypt:32768:8:1$9DNbv5RtIf9tq3V0$4b1f2fb08a2bf17fcf7b946033f0fe7a6eb0f4206af4d17ac43356398816d8ab3c858cf4f9d03db6a3d66a72f1491f17398130c92a266717af2fe8c06174c210"

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

# DEFAULT STATE (Used if DB is empty)
DEFAULT_STATE = {
    "team1_name": "India",
    "team1_logo": "https://flagcdn.com/in.svg",
    "team2_name": "Australia", 
    "team2_logo": "https://flagcdn.com/au.svg",
    "score": 0,
    "wickets": 0,
    "overs": 0.0,
    "target": 0,
    "bat1_name": "Player 1", 
    "bat1_active": True,
    "bat2_name": "Player 2", 
    "bat2_active": False,
    "bowler_name": "Bowler"
}

# --- DATABASE HELPERS ---
def get_match_data():
    """Reads data from Firestore. If not exists, creates it."""
    doc_ref = db.collection('matches').document('live_match')
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        # Initialize DB with defaults
        doc_ref.set(DEFAULT_STATE)
        return DEFAULT_STATE

def update_match_data(new_data):
    """Updates Firestore data."""
    doc_ref = db.collection('matches').document('live_match')
    doc_ref.update(new_data)
    return get_match_data()

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
    # Pass initial data to the template so it loads instantly
    data = get_match_data()
    return render_template('index.html', initial_data=data)

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
    # Fetch current state from DB to populate Admin inputs
    current_data = get_match_data()
    return render_template('admin.html', logo_options=LOGO_OPTIONS, data=current_data)

@app.route('/api/data', methods=['GET'])
def get_data_api():
    """API for the frontend to poll for updates"""
    return jsonify(get_match_data())

@app.route('/api/update', methods=['POST'])
@login_required
def update_data_api():
    """API called by Admin panel to update DB"""
    data = request.json
    updated_state = update_match_data(data)
    return jsonify({"status": "success", "data": updated_state})

# This is for Vercel
app.debug = True
