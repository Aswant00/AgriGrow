# Profile routes

from datetime import datetime
from flask import Blueprint, request, jsonify, g
from db.database import db_run, db_get, db_all
from middleware.auth_middleware import require_auth

profile_bp = Blueprint('profile', __name__)

TASK_LABELS = {
    't1': {'text': 'Complete one learning lesson', 'pts': 50},
    't2': {'text': 'Log a sustainable practice',   'pts': 30},
    't3': {'text': 'Post or reply in community',   'pts': 20},
}


# Get profile
@profile_bp.route('/', methods=['GET'])
@require_auth
def get_profile():
    try:
        user = db_get('SELECT * FROM users WHERE id = %s', (g.user_id,))
        if not user:
            return jsonify({'error': 'User not found.'}), 404

        today = datetime.now().strftime('%Y-%m-%d')

        lesson_rows = db_all('SELECT lesson_id FROM completed_lessons WHERE user_id = %s', (g.user_id,))
        completed_lessons = [r['lesson_id'] for r in lesson_rows]

        task_rows = db_all(
            'SELECT task_id, done FROM today_tasks WHERE user_id = %s AND date = %s',
            (g.user_id, today)
        )
        today_tasks = [
            {
                'id':   r['task_id'],
                'done': r['done'] == 1,
                'text': TASK_LABELS.get(r['task_id'], {}).get('text', ''),
                'pts':  TASK_LABELS.get(r['task_id'], {}).get('pts', 0),
            }
            for r in task_rows
        ]

        badge_rows = db_all('SELECT badge_id, earned FROM badges WHERE user_id = %s', (g.user_id,))
        badges = [{'id': r['badge_id'], 'earned': r['earned'] == 1} for r in badge_rows]

        log_count = db_get('SELECT COUNT(*) as cnt FROM activity_logs WHERE user_id = %s', (g.user_id,))

        return jsonify({
            'user': {
                'id': user['id'], 'name': user['name'], 'email': user['email'],
                'role': user['role'], 'region': user['region'],
                'cropType': user['crop_type'], 'farmSize': user['farm_size'],
                'experience': user['experience'], 'points': user['points'],
                'streak': user['streak'],
            },
            'completedLessons': completed_lessons,
            'todayTasks': today_tasks,
            'badges': badges,
            'activityCount': log_count['cnt'],
        })

    except Exception as e:
        print('Profile get error:', e)
        return jsonify({'error': 'Failed to load profile.'}), 500


# Update profile
@profile_bp.route('/', methods=['PUT'])
@require_auth
def update_profile():
    try:
        data       = request.get_json()
        name       = data.get('name', '').strip()
        email      = data.get('email', '').strip()
        region     = data.get('region', '')
        crop_type  = data.get('cropType', '')
        farm_size  = data.get('farmSize', '')
        experience = data.get('experience', '')

        if not name or not email:
            return jsonify({'error': 'Name and email are required.'}), 400

        conflict = db_get('SELECT id FROM users WHERE email = %s AND id != %s', (email, g.user_id))
        if conflict:
            return jsonify({'error': 'Email already in use.'}), 400

        db_run(
            'UPDATE users SET name=%s, email=%s, region=%s, crop_type=%s, farm_size=%s, experience=%s WHERE id=%s',
            (name, email, region, crop_type, farm_size, experience, g.user_id)
        )

        user = db_get('SELECT * FROM users WHERE id = %s', (g.user_id,))
        return jsonify({
            'user': {
                'id': user['id'], 'name': user['name'], 'email': user['email'],
                'role': user['role'], 'region': user['region'],
                'cropType': user['crop_type'], 'farmSize': user['farm_size'],
                'experience': user['experience'], 'points': user['points'],
                'streak': user['streak'],
            }
        })

    except Exception as e:
        print('Profile update error:', e)
        return jsonify({'error': 'Failed to update profile.'}), 500
