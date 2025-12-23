from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from functools import wraps
# Import security functions
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# SECURITY CONFIGURATION
app.secret_key = 'change_this_to_a_complex_random_string' 

# CREDENTIALS
ADMIN_USERNAME = "admin"
# This is the hash for "password123"
# If you want a different password, use generate_password_hash("your_new_password") to get the new string
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

match_state = {
    "team1_name": "India",
    "team1_logo": "https://flagcdn.com/in.svg",
    "team2_name": "Australia", 
    "team2_logo": "https://flagcdn.com/au.svg",
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

        # VERIFY CREDENTIALS
        # We check if the username matches AND if the password matches the hash
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
    return jsonify(match_state)

@app.route('/api/update', methods=['POST'])
@login_required
def update_data():
    global match_state
    data = request.json
    match_state.update(data)
    return jsonify({"status": "success", "data": match_state})

if __name__ == '__main__':
    app.run(debug=False, port=5000)
