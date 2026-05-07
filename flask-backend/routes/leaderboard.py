# routes/leaderboard.py — Top Users by Points
# GET /api/leaderboard  → Top 20 users ranked by points (admins excluded)

from flask import Blueprint, jsonify
from db.database import db_all
from middleware.auth_middleware import require_auth

leaderboard_bp = Blueprint('leaderboard', __name__)


# GET /api/leaderboard
@leaderboard_bp.route('/', methods=['GET'])
@require_auth
def get_leaderboard():
    try:
        top = db_all(
            "SELECT id, name, region, points FROM users WHERE role != 'admin' ORDER BY points DESC LIMIT 20"
        )
        return jsonify({'leaderboard': top})

    except Exception as e:
        print('Leaderboard error:', e)
        return jsonify({'error': 'Failed to load leaderboard.'}), 500
