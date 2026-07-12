from flask import Flask, render_template, request, jsonify
import json
import os

app = Flask(__name__)

# Ensure data directory and files exist
DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

def write_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        f.write('\n')

def initialize_json(filename, default_data):
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        write_json(filepath, default_data)
    return filepath

USERS_FILE = initialize_json('users.json', {})
PROGRESS_FILE = initialize_json('progress.json', {})
LEADERBOARD_FILE = initialize_json('leaderboard.json', {"1": [], "2": [], "3": []})

def read_json(filepath, default=None):
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        return default if default is not None else {}

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return default if default is not None else {}
            return json.loads(content)
    except (json.JSONDecodeError, ValueError):
        if default is not None:
            write_json(filepath, default)
            return default
        return {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()

    if not username or not password:
        return jsonify({"success": False, "message": "Please enter username and password."})

    users = read_json(USERS_FILE, {})
    if username in users:
        return jsonify({"success": False, "message": "Username already exists."})

    users[username] = password
    write_json(USERS_FILE, users)

    progress = read_json(PROGRESS_FILE, {})
    progress[username] = {"unlocked": 1}
    write_json(PROGRESS_FILE, progress)

    return jsonify({"success": True, "message": "Registration successful."})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()

    users = read_json(USERS_FILE, {})
    if users.get(username) == password:
        progress = read_json(PROGRESS_FILE, {})
        return jsonify({"success": True, "unlocked": progress.get(username, {}).get('unlocked', 1)})

    return jsonify({"success": False, "message": "Invalid username or password."})

@app.route('/api/progress', methods=['POST'])
def update_progress():
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    level = data.get('level')

    progress = read_json(PROGRESS_FILE, {})
    if username in progress:
        if level > progress[username].get('unlocked', 1) and level <= 3:
            progress[username]['unlocked'] = level
            write_json(PROGRESS_FILE, progress)
    return jsonify({"success": True})

@app.route('/api/leaderboard/<level>', methods=['GET'])
def get_leaderboard(level):
    leaderboard = read_json(LEADERBOARD_FILE, {"1": [], "2": [], "3": []})
    level_scores = leaderboard.get(str(level), [])
    level_scores = sorted(level_scores, key=lambda x: x.get('time', x.get('score', 0)))[:3]
    return jsonify({"scores": level_scores})

@app.route('/api/score', methods=['POST'])
def save_score():
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    level = str(data.get('level'))
    clear_time = data.get('time', data.get('score'))

    leaderboard = read_json(LEADERBOARD_FILE, {"1": [], "2": [], "3": []})
    if level not in leaderboard:
        leaderboard[level] = []

    leaderboard[level].append({"username": username, "time": clear_time})
    leaderboard[level] = sorted(leaderboard[level], key=lambda x: x.get('time', x.get('score', 0)))[:3]

    write_json(LEADERBOARD_FILE, leaderboard)
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)