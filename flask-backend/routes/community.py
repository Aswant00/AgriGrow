# routes/community.py — Forum Posts and Likes
# GET    /api/posts          → All forum posts (newest first)
# POST   /api/posts          → Create a new forum post
# DELETE /api/posts/<id>     → Delete a post (owner only)
# POST   /api/posts/<id>/like → Toggle a like on/off

from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, g
from db.database import db_run, db_get, db_all
from middleware.auth_middleware import require_auth

community_bp = Blueprint('community', __name__)


def format_time(dt_value):
    """Convert a datetime to a human-readable relative time string."""
    if dt_value is None:
        return 'Just now'
    # dt_value is a Python datetime from PyMySQL
    now  = datetime.now()
    diff = now - dt_value  # both are naive local times from MySQL
    secs  = int(diff.total_seconds())
    mins  = secs // 60
    hours = secs // 3600
    days  = secs // 86400

    if mins < 1:   return 'Just now'
    if mins < 60:  return f"{mins} minute{'s' if mins != 1 else ''} ago"
    if hours < 24: return f"{hours} hour{'s' if hours != 1 else ''} ago"
    if days == 1:  return 'Yesterday'
    return f"{days} days ago"


# GET /api/posts
@community_bp.route('/', methods=['GET'])
@require_auth
def get_posts():
    try:
        posts      = db_all('SELECT * FROM posts ORDER BY created_at DESC')
        liked_rows = db_all('SELECT post_id FROM post_likes WHERE user_id = %s', (g.user_id,))
        liked_set  = {r['post_id'] for r in liked_rows}

        return jsonify({
            'posts': [
                {
                    'id':       p['id'],
                    'userId':   p['user_id'],
                    'author':   p['author'],
                    'isExpert': p['is_expert'] == 1,
                    'tag':      p['tag'],
                    'body':     p['body'],
                    'likes':    p['likes'],
                    'liked':    p['id'] in liked_set,
                    'time':     format_time(p['created_at']),
                    'reply':    {
                        'author':   p['reply_author'],
                        'text':     p['reply_text'],
                        'isExpert': p['reply_is_expert'] == 1,
                    } if p['reply_text'] else None,
                }
                for p in posts
            ]
        })

    except Exception as e:
        print('Posts get error:', e)
        return jsonify({'error': 'Failed to load posts.'}), 500


# POST /api/posts
@community_bp.route('/', methods=['POST'])
@require_auth
def create_post():
    try:
        data = request.get_json()
        body = (data.get('body') or '').strip()
        tag  = data.get('tag', 'General')

        if not body:
            return jsonify({'error': 'Post body is required.'}), 400

        user      = db_get('SELECT name, role FROM users WHERE id = %s', (g.user_id,))
        is_expert = 1 if user['role'] == 'expert' else 0

        result = db_run(
            'INSERT INTO posts (user_id, author, is_expert, tag, body) VALUES (%s,%s,%s,%s,%s)',
            (g.user_id, user['name'], is_expert, tag, body)
        )

        db_run('UPDATE users SET points = points + 10 WHERE id = %s', (g.user_id,))
        db_run("UPDATE badges SET earned=1 WHERE user_id=%s AND badge_id='b6' AND earned=0", (g.user_id,))

        today = datetime.now().strftime('%Y-%m-%d')
        db_run("UPDATE today_tasks SET done=1 WHERE user_id=%s AND task_id='t3' AND date=%s",
               (g.user_id, today))

        updated_user = db_get('SELECT points FROM users WHERE id = %s', (g.user_id,))
        badges       = db_all('SELECT badge_id, earned FROM badges WHERE user_id = %s', (g.user_id,))

        return jsonify({
            'post': {
                'id':       result['lastID'],
                'userId':   g.user_id,
                'author':   user['name'],
                'isExpert': is_expert == 1,
                'tag':      tag,
                'body':     body,
                'likes':    0,
                'liked':    False,
                'time':     'Just now',
                'reply':    None,
            },
            'points': updated_user['points'],
            'badges': [{'id': r['badge_id'], 'earned': r['earned'] == 1} for r in badges],
        }), 201

    except Exception as e:
        print('Post create error:', e)
        return jsonify({'error': 'Failed to create post.'}), 500


# DELETE /api/posts/<id>
@community_bp.route('/<int:post_id>', methods=['DELETE'])
@require_auth
def delete_post(post_id):
    try:
        post = db_get('SELECT id, user_id FROM posts WHERE id = %s', (post_id,))
        if not post:
            return jsonify({'error': 'Post not found.'}), 404
        if post['user_id'] != g.user_id:
            return jsonify({'error': 'You can only delete your own posts.'}), 403

        db_run('DELETE FROM post_likes WHERE post_id = %s', (post_id,))
        db_run('DELETE FROM posts WHERE id = %s', (post_id,))
        return jsonify({'success': True})

    except Exception as e:
        print('Delete post error:', e)
        return jsonify({'error': 'Failed to delete post.'}), 500


# POST /api/posts/<id>/like
@community_bp.route('/<int:post_id>/like', methods=['POST'])
@require_auth
def toggle_like(post_id):
    try:
        post = db_get('SELECT id, likes FROM posts WHERE id = %s', (post_id,))
        if not post:
            return jsonify({'error': 'Post not found.'}), 404

        already = db_get('SELECT 1 FROM post_likes WHERE user_id=%s AND post_id=%s',
                         (g.user_id, post_id))

        if already:
            db_run('DELETE FROM post_likes WHERE user_id=%s AND post_id=%s', (g.user_id, post_id))
            db_run('UPDATE posts SET likes = likes - 1 WHERE id = %s', (post_id,))
            return jsonify({'liked': False, 'likes': post['likes'] - 1})
        else:
            db_run('INSERT INTO post_likes (user_id, post_id) VALUES (%s,%s)', (g.user_id, post_id))
            db_run('UPDATE posts SET likes = likes + 1 WHERE id = %s', (post_id,))
            return jsonify({'liked': True, 'likes': post['likes'] + 1})

    except Exception as e:
        print('Like error:', e)
        return jsonify({'error': 'Failed to toggle like.'}), 500
