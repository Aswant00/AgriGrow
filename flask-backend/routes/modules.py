# routes/modules.py — Public (auth-required) Modules Endpoint
# GET /api/modules  →  Returns all admin-created custom modules with their lessons

from flask import Blueprint, jsonify
from db.database import db_get, db_all
from middleware.auth_middleware import require_auth

modules_bp = Blueprint('modules', __name__)


def _format_module(m):
    """Format a custom_modules row plus its lessons for the frontend."""
    lessons = db_all(
        'SELECT * FROM custom_module_lessons WHERE module_id = %s ORDER BY sort_order, id',
        (m['id'],)
    )
    total_pts = sum(l['pts'] for l in lessons)
    return {
        # Use a string prefix so IDs don't clash with built-in module IDs (1-4)
        'id': f'cm_{m["id"]}',
        'dbId': m['id'],
        'icon': m['icon'] or 'eco',
        'title': m['title'],
        'cat': m['category'],
        'difficulty': m['difficulty'],
        'iconColor': m['icon_color'] or '#2e7d32',
        'bg': (m['icon_color'] or '#2e7d32') + '22',
        'pts': total_pts or 0,
        'time': m['duration'] or '—',
        'expertVerified': bool(m['expert_verified']),
        'desc': m['description'],
        'isCustom': True,
        'lessons': [
            {
                'id': f'cm_{m["id"]}_l{l["id"]}',
                'dbId': l['id'],
                'title': l['title'],
                'sub': l['subtitle'] or '',
                'pts': l['pts'],
                'expertVerified': bool(l['expert_verified']),
                # Custom lessons have no quiz — use a simple mark-complete content stub
                'content': {
                    'heading': l['title'],
                    'sections': [
                        {'type': 'p', 'text': l['subtitle'] or 'Complete this lesson to earn points.'}
                    ],
                    'quiz': None,
                },
            }
            for l in lessons
        ],
    }


# GET /api/modules
@modules_bp.route('/', methods=['GET'])
@require_auth
def get_custom_modules():
    try:
        rows = db_all('SELECT * FROM custom_modules ORDER BY created_at DESC')
        return jsonify({'modules': [_format_module(r) for r in rows]})
    except Exception as e:
        print('Public modules error:', e)
        return jsonify({'error': 'Failed to load modules.'}), 500
