import os
import json
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import redis

app = Flask(__name__)

# SECURITY CONFIGURATION
# Try to get secret from Environment (Vercel), fallback to hardcoded for local testing
app.secret_key = os.environ.get('SECRET_KEY', 'change_this_to_a_complex_random_string')

# DATABASE CONNECTION (Redis)
# Vercel will provide the KV_URL environment variable automatically
redis_url = os.environ.get('KV_URL')
# Fallback to local redis or None if not set
r = redis.from_url(redis_url) if redis_url else None

# CREDENTIALS
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

# INITIAL DEFAULT STATE
DEFAULT_STATE = {
    "team1_name": "Echo FC",
    "team1_logo": "https://raw.githubusercontent.com/karthikparambil/football-scoreboard/refs/heads/main/static/logos/echo.png",
    "team2_name": "Team Offenso", 
    "team2_logo": "https://raw.githubusercontent.com/karthikparambil/football-scoreboard/refs/heads/main/static/logos/offenso.png",
    "score": 30,
    "wickets": 0,
    "overs": 2.0,
    "target": 26,
    "bat1_name": "", 
    "bat1_active": True,
    "bat2_name": "", 
    "bat2_active": False,
    "bowler_name": ""
}

# --- DATABASE HELPERS ---
def get_match_state():
    """Fetch state from Redis, or return default if DB is empty/missing"""
    if not r: return DEFAULT_STATE # Fallback for local testing without Redis
    
    try:
        data = r.get("match_state")
        if data:
            return json.loads(data)
        else:
            # Initialize DB with default
            r.set("match_state", json.dumps(DEFAULT_STATE))
            return DEFAULT_STATE
    except:
        return DEFAULT_STATE

def update_match_state(new_data):
    """Update specific fields in the Redis DB"""
    current_state = get_match_state()
    current_state.update(new_data)
    
    if r:
        r.set("match_state", json.dumps(current_state))
    
    return current_state
# ------------------------

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
    # Fetch from DB instead of global variable
    return jsonify(get_match_state())

@app.route('/api/update', methods=['POST'])
@login_required
def update_data():
    data = request.json
    # Update DB
    new_state = update_match_state(data)
    return jsonify({"status": "success", "data": new_state})

if __name__ == '__main__':
    app.run(debug=False, port=5000)
