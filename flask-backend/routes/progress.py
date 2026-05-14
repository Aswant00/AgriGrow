# Progress tracking and daily tasks

from datetime import datetime
from flask import Blueprint, request, jsonify, g
from db.database import db_run, db_get, db_all
from middleware.auth_middleware import require_auth

progress_bp = Blueprint('progress', __name__)


def check_and_award_badges(user_id):
    """Unlock earned badges."""
    user    = db_get('SELECT points FROM users WHERE id = %s', (user_id,))
    lessons = db_all('SELECT lesson_id FROM completed_lessons WHERE user_id = %s', (user_id,))

    if len(lessons) >= 1:
        db_run("UPDATE badges SET earned=1 WHERE user_id=%s AND badge_id='b1' AND earned=0", (user_id,))
    if user['points'] >= 500:
        db_run("UPDATE badges SET earned=1 WHERE user_id=%s AND badge_id='b4' AND earned=0", (user_id,))
    if len(lessons) >= 6:
        db_run("UPDATE badges SET earned=1 WHERE user_id=%s AND badge_id='b5' AND earned=0", (user_id,))


# Get progress
@progress_bp.route('/', methods=['GET'])
@require_auth
def get_progress():
    try:
        user    = db_get('SELECT points, streak FROM users WHERE id = %s', (g.user_id,))
        lessons = db_all('SELECT lesson_id FROM completed_lessons WHERE user_id = %s', (g.user_id,))
        badges  = db_all('SELECT badge_id, earned FROM badges WHERE user_id = %s', (g.user_id,))

        return jsonify({
            'points': user['points'],
            'streak': user['streak'],
            'completedLessons': [r['lesson_id'] for r in lessons],
            'badges': [{'id': r['badge_id'], 'earned': r['earned'] == 1} for r in badges],
        })

    except Exception as e:
        print('Progress get error:', e)
        return jsonify({'error': 'Failed to load progress.'}), 500


# Complete lesson
@progress_bp.route('/lesson', methods=['POST'])
@require_auth
def complete_lesson():
    try:
        data      = request.get_json()
        lesson_id = data.get('lessonId')
        pts       = data.get('pts')

        if not lesson_id or pts is None:
            return jsonify({'error': 'lessonId and pts are required.'}), 400

        already = db_get(
            'SELECT id FROM completed_lessons WHERE user_id = %s AND lesson_id = %s',
            (g.user_id, lesson_id)
        )
        if already:
            return jsonify({'alreadyDone': True})

        db_run('INSERT INTO completed_lessons (user_id, lesson_id, pts) VALUES (%s, %s, %s)',
               (g.user_id, lesson_id, pts))
        db_run('UPDATE users SET points = points + %s WHERE id = %s', (pts, g.user_id))
        check_and_award_badges(g.user_id)

        today = datetime.now().strftime('%Y-%m-%d')
        db_run("UPDATE today_tasks SET done=1 WHERE user_id=%s AND task_id='t1' AND date=%s",
               (g.user_id, today))

        user   = db_get('SELECT points FROM users WHERE id = %s', (g.user_id,))
        badges = db_all('SELECT badge_id, earned FROM badges WHERE user_id = %s', (g.user_id,))

        return jsonify({
            'points': user['points'],
            'badges': [{'id': r['badge_id'], 'earned': r['earned'] == 1} for r in badges],
        })

    except Exception as e:
        print('Complete lesson error:', e)
        return jsonify({'error': 'Failed to save lesson progress.'}), 500


# Toggle task
@progress_bp.route('/task', methods=['POST'])
@require_auth
def toggle_task():
    try:
        data    = request.get_json()
        task_id = data.get('taskId')

        if not task_id:
            return jsonify({'error': 'taskId is required.'}), 400

        today    = datetime.now().strftime('%Y-%m-%d')
        TASK_PTS = {'t1': 50, 't2': 30, 't3': 20}

        task = db_get(
            'SELECT done FROM today_tasks WHERE user_id=%s AND task_id=%s AND date=%s',
            (g.user_id, task_id, today)
        )
        if not task:
            return jsonify({'error': 'Task not found for today.'}), 404

        now_done  = 0 if task['done'] == 1 else 1
        pts_delta = TASK_PTS.get(task_id, 0) if now_done else -TASK_PTS.get(task_id, 0)

        db_run('UPDATE today_tasks SET done=%s WHERE user_id=%s AND task_id=%s AND date=%s',
               (now_done, g.user_id, task_id, today))
        db_run('UPDATE users SET points = GREATEST(0, points + %s) WHERE id = %s',
               (pts_delta, g.user_id))

        user = db_get('SELECT points FROM users WHERE id = %s', (g.user_id,))
        return jsonify({'done': now_done == 1, 'points': user['points']})

    except Exception as e:
        print('Toggle task error:', e)
        return jsonify({'error': 'Failed to update task.'}), 500
