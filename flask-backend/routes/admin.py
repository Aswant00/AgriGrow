# Admin-only endpoints

import json
from flask import Blueprint, request, jsonify, g
from db.database import db_run, db_get, db_all
from middleware.auth_middleware import require_auth, admin_only

admin_bp = Blueprint('admin', __name__)


def _module_with_lessons(m):
    """Attach lessons list to a module dict."""
    lessons = db_all(
        'SELECT * FROM custom_module_lessons WHERE module_id = %s ORDER BY sort_order, id',
        (m['id'],)
    )
    return {
        **m,
        'created_at': str(m['created_at']),
        'lessons': [
            {
                'id': str(l['id']),
                'title': l['title'],
                'sub': l['subtitle'],
                'pts': l['pts'],
                'expertVerified': bool(l['expert_verified']),
            }
            for l in lessons
        ]
    }


# Get platform stats
@admin_bp.route('/stats', methods=['GET'])
@require_auth
@admin_only
def get_stats():
    try:
        user_count     = db_get("SELECT COUNT(*) as cnt FROM users WHERE role != 'admin'")
        lesson_count   = db_get('SELECT COUNT(*) as cnt FROM completed_lessons')
        practice_count = db_get('SELECT COUNT(*) as cnt FROM activity_logs')
        badge_count    = db_get('SELECT COUNT(*) as cnt FROM badges WHERE earned = 1')

        return jsonify({
            'users':     user_count['cnt'],
            'lessons':   lesson_count['cnt'],
            'practices': practice_count['cnt'],
            'badges':    badge_count['cnt'],
        })

    except Exception as e:
        print('Admin stats error:', e)
        return jsonify({'error': 'Failed to load stats.'}), 500


# Get all users
@admin_bp.route('/users', methods=['GET'])
@require_auth
@admin_only
def get_users():
    try:
        users = db_all(
            'SELECT id, name, email, role, region, crop_type, farm_size, experience, points, streak, created_at '
            'FROM users ORDER BY created_at DESC'
        )
        return jsonify({
            'users': [
                {**u, 'cropType': u['crop_type'], 'farmSize': u['farm_size'],
                 'created_at': str(u['created_at'])}
                for u in users
            ]
        })

    except Exception as e:
        print('Admin users error:', e)
        return jsonify({'error': 'Failed to load users.'}), 500


# Get user details
@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@require_auth
@admin_only
def get_user_detail(user_id):
    try:
        user = db_get('SELECT * FROM users WHERE id = %s', (user_id,))
        if not user:
            return jsonify({'error': 'User not found.'}), 404

        completed_lessons = db_all(
            'SELECT lesson_id, pts, completed_at FROM completed_lessons WHERE user_id = %s', (user_id,)
        )
        badges = db_all('SELECT badge_id, earned FROM badges WHERE user_id = %s', (user_id,))
        activity_logs = db_all(
            'SELECT practices, date, pts FROM activity_logs WHERE user_id = %s ORDER BY created_at DESC LIMIT 10',
            (user_id,)
        )
        post_count = db_get('SELECT COUNT(*) as cnt FROM posts WHERE user_id = %s', (user_id,))

        return jsonify({
            'user': {
                'id': user['id'], 'name': user['name'], 'email': user['email'],
                'role': user['role'], 'region': user['region'],
                'cropType': user['crop_type'], 'farmSize': user['farm_size'],
                'experience': user['experience'], 'points': user['points'],
                'streak': user['streak'], 'createdAt': str(user['created_at']),
            },
            'completedLessons': [l['lesson_id'] for l in completed_lessons],
            'badges': [{'id': b['badge_id'], 'earned': b['earned'] == 1} for b in badges],
            'activityLogs': [
                {**l, 'practices': json.loads(l['practices']), 'date': str(l['date'])}
                for l in activity_logs
            ],
            'postCount': post_count['cnt'],
        })

    except Exception as e:
        print('Admin user detail error:', e)
        return jsonify({'error': 'Failed to load user details.'}), 500


# Get modules
@admin_bp.route('/modules', methods=['GET'])
@require_auth
@admin_only
def get_modules():
    try:
        modules = db_all('SELECT * FROM custom_modules ORDER BY created_at DESC')
        return jsonify({'modules': [_module_with_lessons(m) for m in modules]})

    except Exception as e:
        print('Admin modules error:', e)
        return jsonify({'error': 'Failed to load modules.'}), 500


# Create module
@admin_bp.route('/modules', methods=['POST'])
@require_auth
@admin_only
def create_module():
    try:
        data            = request.get_json()
        title           = (data.get('title') or '').strip()
        category        = data.get('category', '')
        difficulty      = data.get('difficulty', '')
        description     = (data.get('description') or '').strip()
        icon            = data.get('icon', 'eco')
        icon_color      = data.get('iconColor', '#2e7d32')
        duration        = data.get('duration', '30 min')
        expert_verified = 1 if data.get('expertVerified') else 0

        if not title or not category or not difficulty or not description:
            return jsonify({'error': 'Title, category, difficulty and description are required.'}), 400

        result = db_run(
            '''INSERT INTO custom_modules
               (title, category, difficulty, icon, icon_color, description, duration, expert_verified, created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
            (title, category, difficulty, icon, icon_color, description, duration, expert_verified, g.user_id)
        )

        module = db_get('SELECT * FROM custom_modules WHERE id = %s', (result['lastID'],))
        return jsonify({'module': _module_with_lessons(module)}), 201

    except Exception as e:
        print('Admin create module error:', e)
        return jsonify({'error': 'Failed to create module.'}), 500


# Update module
@admin_bp.route('/modules/<int:module_id>', methods=['PUT'])
@require_auth
@admin_only
def update_module(module_id):
    try:
        module = db_get('SELECT id FROM custom_modules WHERE id = %s', (module_id,))
        if not module:
            return jsonify({'error': 'Module not found.'}), 404

        data            = request.get_json()
        title           = (data.get('title') or '').strip()
        category        = data.get('category', '')
        difficulty      = data.get('difficulty', '')
        description     = (data.get('description') or '').strip()
        icon            = data.get('icon', 'eco')
        icon_color      = data.get('iconColor', '#2e7d32')
        duration        = data.get('duration', '30 min')
        expert_verified = 1 if data.get('expertVerified') else 0

        if not title or not category or not difficulty or not description:
            return jsonify({'error': 'Title, category, difficulty and description are required.'}), 400

        db_run(
            '''UPDATE custom_modules SET
               title=%s, category=%s, difficulty=%s, icon=%s, icon_color=%s,
               description=%s, duration=%s, expert_verified=%s
               WHERE id=%s''',
            (title, category, difficulty, icon, icon_color, description, duration, expert_verified, module_id)
        )

        updated = db_get('SELECT * FROM custom_modules WHERE id = %s', (module_id,))
        return jsonify({'module': _module_with_lessons(updated)})

    except Exception as e:
        print('Admin update module error:', e)
        return jsonify({'error': 'Failed to update module.'}), 500


# Delete module
@admin_bp.route('/modules/<int:module_id>', methods=['DELETE'])
@require_auth
@admin_only
def delete_module(module_id):
    try:
        db_run('DELETE FROM custom_modules WHERE id = %s', (module_id,))
        return jsonify({'success': True})

    except Exception as e:
        print('Admin delete module error:', e)
        return jsonify({'error': 'Failed to delete module.'}), 500


# ── Lesson endpoints ──────────────────────────────────────────────────────────

# Get lessons
@admin_bp.route('/modules/<int:module_id>/lessons', methods=['GET'])
@require_auth
@admin_only
def get_lessons(module_id):
    try:
        lessons = db_all(
            'SELECT * FROM custom_module_lessons WHERE module_id = %s ORDER BY sort_order, id',
            (module_id,)
        )
        return jsonify({'lessons': [
            {
                'id': l['id'], 'title': l['title'], 'subtitle': l['subtitle'],
                'pts': l['pts'], 'expertVerified': bool(l['expert_verified']),
                'sortOrder': l['sort_order'],
            }
            for l in lessons
        ]})
    except Exception as e:
        print('Get lessons error:', e)
        return jsonify({'error': 'Failed to load lessons.'}), 500


# Add lesson
@admin_bp.route('/modules/<int:module_id>/lessons', methods=['POST'])
@require_auth
@admin_only
def add_lesson(module_id):
    try:
        module = db_get('SELECT id FROM custom_modules WHERE id = %s', (module_id,))
        if not module:
            return jsonify({'error': 'Module not found.'}), 404

        data            = request.get_json()
        title           = (data.get('title') or '').strip()
        subtitle        = (data.get('subtitle') or '').strip()
        pts             = int(data.get('pts', 20))
        expert_verified = 1 if data.get('expertVerified') else 0

        if not title:
            return jsonify({'error': 'Lesson title is required.'}), 400

        # sort_order = current max + 1
        max_order = db_get(
            'SELECT COALESCE(MAX(sort_order), 0) as mo FROM custom_module_lessons WHERE module_id = %s',
            (module_id,)
        )
        sort_order = (max_order['mo'] or 0) + 1

        result = db_run(
            '''INSERT INTO custom_module_lessons
               (module_id, title, subtitle, pts, expert_verified, sort_order)
               VALUES (%s,%s,%s,%s,%s,%s)''',
            (module_id, title, subtitle, pts, expert_verified, sort_order)
        )

        lesson = db_get('SELECT * FROM custom_module_lessons WHERE id = %s', (result['lastID'],))
        return jsonify({'lesson': {
            'id': lesson['id'], 'title': lesson['title'], 'subtitle': lesson['subtitle'],
            'pts': lesson['pts'], 'expertVerified': bool(lesson['expert_verified']),
            'sortOrder': lesson['sort_order'],
        }}), 201

    except Exception as e:
        print('Add lesson error:', e)
        return jsonify({'error': 'Failed to add lesson.'}), 500


# Update lesson
@admin_bp.route('/modules/<int:module_id>/lessons/<int:lesson_id>', methods=['PUT'])
@require_auth
@admin_only
def update_lesson(module_id, lesson_id):
    try:
        lesson = db_get(
            'SELECT id FROM custom_module_lessons WHERE id = %s AND module_id = %s',
            (lesson_id, module_id)
        )
        if not lesson:
            return jsonify({'error': 'Lesson not found.'}), 404

        data            = request.get_json()
        title           = (data.get('title') or '').strip()
        subtitle        = (data.get('subtitle') or '').strip()
        pts             = int(data.get('pts', 20))
        expert_verified = 1 if data.get('expertVerified') else 0

        if not title:
            return jsonify({'error': 'Lesson title is required.'}), 400

        db_run(
            '''UPDATE custom_module_lessons SET title=%s, subtitle=%s, pts=%s, expert_verified=%s
               WHERE id=%s AND module_id=%s''',
            (title, subtitle, pts, expert_verified, lesson_id, module_id)
        )

        updated = db_get('SELECT * FROM custom_module_lessons WHERE id = %s', (lesson_id,))
        return jsonify({'lesson': {
            'id': updated['id'], 'title': updated['title'], 'subtitle': updated['subtitle'],
            'pts': updated['pts'], 'expertVerified': bool(updated['expert_verified']),
            'sortOrder': updated['sort_order'],
        }})

    except Exception as e:
        print('Update lesson error:', e)
        return jsonify({'error': 'Failed to update lesson.'}), 500


# Delete lesson
@admin_bp.route('/modules/<int:module_id>/lessons/<int:lesson_id>', methods=['DELETE'])
@require_auth
@admin_only
def delete_lesson(module_id, lesson_id):
    try:
        db_run(
            'DELETE FROM custom_module_lessons WHERE id = %s AND module_id = %s',
            (lesson_id, module_id)
        )
        return jsonify({'success': True})

    except Exception as e:
        print('Delete lesson error:', e)
        return jsonify({'error': 'Failed to delete lesson.'}), 500
