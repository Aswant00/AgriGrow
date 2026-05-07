# app.py
# ─────────────────────────────────────────────────────────────────────────────
# AgriGrow Flask Backend — Entry Point
#
# HOW IT WORKS:
#   Browser (AgriGrow.html)
#       ↓  makes fetch() calls to /api/...
#   Flask (this file)
#       ↓  matches the URL to a Blueprint (route file)
#   Route file (e.g. routes/auth.py)
#       ↓  queries MySQL via db/database.py
#   MySQL Database
#       ↑  returns data back up the chain to the browser
#
# TO START THE SERVER:
#   python app.py
#   Then open:  http://localhost:5000/AgriGrow.html
# ─────────────────────────────────────────────────────────────────────────────

import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# ── Import all route Blueprints ───────────────────────────────────────────────
from routes.auth        import auth_bp
from routes.profile     import profile_bp
from routes.progress    import progress_bp
from routes.tracker     import tracker_bp
from routes.community   import community_bp
from routes.leaderboard import leaderboard_bp
from routes.admin       import admin_bp
from routes.modules     import modules_bp

# ── Create the Flask app ──────────────────────────────────────────────────────
app = Flask(__name__, static_folder='..', static_url_path='')
CORS(app)  # Allow requests from any origin (fine for local dev)

# ── Register Blueprints (each maps a URL prefix to a route file) ──────────────
app.register_blueprint(auth_bp,        url_prefix='/api/auth')
app.register_blueprint(profile_bp,     url_prefix='/api/profile')
app.register_blueprint(progress_bp,    url_prefix='/api/progress')
app.register_blueprint(tracker_bp,     url_prefix='/api/tracker')
app.register_blueprint(community_bp,   url_prefix='/api/posts')
app.register_blueprint(leaderboard_bp, url_prefix='/api/leaderboard')
app.register_blueprint(admin_bp,       url_prefix='/api/admin')
app.register_blueprint(modules_bp,     url_prefix='/api/modules')

# ── Serve AgriGrow.html from the parent folder ───────────────────────────────
@app.route('/')
@app.route('/AgriGrow.html')
def serve_frontend():
    return send_from_directory('..', 'AgriGrow.html')

# ── Health check ─────────────────────────────────────────────────────────────
from datetime import datetime
@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'message': 'AgriGrow API is running!',
                    'time': datetime.now().isoformat()})

# ── 404 handler ──────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': f'Route not found.'}), 404

# ── 500 handler ──────────────────────────────────────────────────────────────
@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error.'}), 500

# ── Start the server ──────────────────────────────────────────────────────────
if __name__ == '__main__':
    PORT = int(os.getenv('PORT', 5000))
    print()
    print('🌱 AgriGrow Flask Backend running!')
    print(f'   Health: http://localhost:{PORT}/api/health')
    print(f'   App:    http://localhost:{PORT}/AgriGrow.html')
    print()
    app.run(host='0.0.0.0', port=PORT, debug=True)
