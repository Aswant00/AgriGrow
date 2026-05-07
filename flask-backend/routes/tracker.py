# routes/tracker.py — Practice Activity Logging
# GET  /api/tracker  → All of this user's past practice logs
# POST /api/tracker  → Save a new practice log and award points

import json
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from db.database import db_run, db_get, db_all
from middleware.auth_middleware import require_auth

tracker_bp = Blueprint('tracker', __name__)


# GET /api/tracker
@tracker_bp.route('/', methods=['GET'])
@require_auth
def get_logs():
    try:
        logs = db_all(
            'SELECT id, practices, notes, date, pts, has_proof, created_at '
            'FROM activity_logs WHERE user_id = %s ORDER BY created_at DESC',
            (g.user_id,)
        )
        return jsonify({
            'logs': [
                {
                    **log,
                    'practices': json.loads(log['practices']),
                    'hasProof':  log['has_proof'] == 1,
                    'date': str(log['date']),
                    'created_at': str(log['created_at']),
                }
                for log in logs
            ]
        })

    except Exception as e:
        print('Tracker get error:', e)
        return jsonify({'error': 'Failed to load activity logs.'}), 500


# POST /api/tracker
@tracker_bp.route('/', methods=['POST'])
@require_auth
def log_practice():
    try:
        data      = request.get_json()
        practices = data.get('practices', [])
        notes     = data.get('notes', '')
        date      = data.get('date', '')
        has_proof = data.get('hasProof', False)

        if not practices or not isinstance(practices, list) or len(practices) == 0:
            return jsonify({'error': 'At least one practice must be selected.'}), 400
        if not date:
            return jsonify({'error': 'Date is required.'}), 400

        pts = len(practices) * 20

        db_run(
            'INSERT INTO activity_logs (user_id, practices, notes, date, pts, has_proof) VALUES (%s,%s,%s,%s,%s,%s)',
            (g.user_id, json.dumps(practices), notes, date, pts, 1 if has_proof else 0)
        )
        db_run('UPDATE users SET points = points + %s WHERE id = %s', (pts, g.user_id))

        # Badge b2: water saver (drip irrigation logged 3+ times)
        water_count = db_get(
            'SELECT COUNT(*) as cnt FROM activity_logs WHERE user_id=%s AND practices LIKE %s',
            (g.user_id, '%"p2"%')
        )
        if water_count['cnt'] >= 3:
            db_run("UPDATE badges SET earned=1 WHERE user_id=%s AND badge_id='b2' AND earned=0", (g.user_id,))

        # Badge b4: 500 points
        user = db_get('SELECT points FROM users WHERE id = %s', (g.user_id,))
        if user['points'] >= 500:
            db_run("UPDATE badges SET earned=1 WHERE user_id=%s AND badge_id='b4' AND earned=0", (g.user_id,))

        # Mark task t2 done
        today = datetime.now().strftime('%Y-%m-%d')
        db_run("UPDATE today_tasks SET done=1 WHERE user_id=%s AND task_id='t2' AND date=%s",
               (g.user_id, today))

        badges = db_all('SELECT badge_id, earned FROM badges WHERE user_id = %s', (g.user_id,))

        return jsonify({
            'pts':    pts,
            'points': user['points'],
            'badges': [{'id': r['badge_id'], 'earned': r['earned'] == 1} for r in badges],
        }), 201

    except Exception as e:
        print('Tracker post error:', e)
        return jsonify({'error': 'Failed to save activity log.'}), 500
