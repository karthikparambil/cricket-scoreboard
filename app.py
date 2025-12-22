import os
import json
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from functools import wraps
from werkzeug.security import check_password_hash
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# SECURITY CONFIGURATION
# In Vercel, we will set this in the Environment Variables
app.secret_key = os.environ.get('SECRET_KEY', 'local_dev_secret_key')

# CREDENTIALS (Hashed 'password123')
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = "scrypt:32768:8:1$kE7e1rJg2n6qL9o$3d9c57223631976075908331872147321585292850901579549320857216853215"

# --- FIREBASE SETUP ---
# We check if Firebase is already initialized to avoid errors in serverless environment
if not firebase_admin._apps:
    # Check if we are on Vercel (using Environment Variable) or Local
    if os.environ.get('FIREBASE_CREDENTIALS'):
        # Parse the JSON string from Vercel Env Var
        cred_dict = json.loads(os.environ.get('FIREBASE_CREDENTIALS'))
        cred = credentials.Certificate(cred_dict)
    else:
        # Use local file
        cred = credentials.Certificate("firebase_key.json")
    
    firebase_admin.initialize_app(cred)

db = firestore.client()
match_ref = db.collection('cricket').document('live_match')

# --- INITIAL DATA HELPER ---
# If database is empty, create the initial data
def init_db():
    if not match_ref.get().exists:
        initial_state = {
            "team1_name": "India",
            "team1_logo": "",
            "team2_name": "Australia", 
            "team2_logo": "",
            "score": 142,
            "wickets": 3,
            "overs": 16.4,
            "target": 180,
            "bat1_name": "V. Kohli", 
            "bat1_active": True,
            "bat2_name": "H. Pandya", 
            "bat2_active": False,
            "bowler_name": "P. Cummins"
        }
        match_ref.set(initial_state)

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

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash("Please log in.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    init_db() # Ensure DB exists
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
    init_db()
    return render_template('admin.html', logo_options=LOGO_OPTIONS)

@app.route('/api/data', methods=['GET'])
def get_data():
    # READ from Firebase
    doc = match_ref.get()
    if doc.exists:
        return jsonify(doc.to_dict())
    else:
        init_db()
        return jsonify(match_ref.get().to_dict())

@app.route('/api/update', methods=['POST'])
@login_required
def update_data():
    data = request.json
    # WRITE to Firebase
    match_ref.update(data)
    return jsonify({"status": "success", "data": data})

# Vercel requires the app to be named 'app'
if __name__ == '__main__':
    app.run(debug=False)