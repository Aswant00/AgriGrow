# User authentication routes

import os
import re
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify, g
from db.database import db_run, db_get, init_badges_for_user, init_tasks_for_user
from middleware.auth_middleware import require_auth

auth_bp = Blueprint('auth', __name__)

# Validation helpers

EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

def is_valid_email(email: str) -> bool:
    """Return True if email matches a basic name@domain.tld pattern."""
    return bool(EMAIL_RE.match(email))


def is_strong_password(password: str) -> bool:
    """Check if password meets strength criteria."""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?`~]', password):
        return False
    return True


def generate_token(user):
    """Create a JWT token that expires in 7 days."""
    payload = {
        'userId': user['id'],
        'role': user['role'],
        'exp': datetime.now(timezone.utc) + timedelta(days=7),
    }
    return jwt.encode(payload, os.getenv('JWT_SECRET'), algorithm='HS256')


def safe_user(user):
    """Return only the fields the frontend needs (no password)."""
    return {
        'id': user['id'],
        'name': user['name'],
        'email': user['email'],
        'role': user['role'],
        'region': user['region'],
        'cropType': user['crop_type'],
        'farmSize': user['farm_size'],
        'experience': user['experience'],
        'points': user['points'],
        'streak': user['streak'],
    }


# Register user
@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        name     = data.get('name', '').strip()
        email    = data.get('email', '').strip()
        password = data.get('password', '')
        region   = data.get('region', '').strip()
        crop_type  = data.get('cropType', '')
        farm_size  = data.get('farmSize', '')
        experience = data.get('experience', '')

        if not name or not email or not password or not region:
            return jsonify({'error': 'Please fill all required fields.'}), 400
        if not is_valid_email(email):
            return jsonify({'error': 'Please enter a valid email address.'}), 400
        if not is_strong_password(password):
            return jsonify({'error': 'Password must include uppercase, lowercase, numbers, and symbols.'}), 400

        existing = db_get('SELECT id FROM users WHERE email = %s', (email,))
        if existing:
            return jsonify({'error': 'Email already registered.'}), 400

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        today  = datetime.now().strftime('%Y-%m-%d')

        result = db_run(
            """INSERT INTO users (name, email, password, role, region, crop_type, farm_size, experience)
               VALUES (%s, %s, %s, 'farmer', %s, %s, %s, %s)""",
            (name, email, hashed, region, crop_type, farm_size, experience)
        )

        user_id = result['lastID']
        init_badges_for_user(user_id)
        init_tasks_for_user(user_id, today)

        user = db_get('SELECT * FROM users WHERE id = %s', (user_id,))
        return jsonify({'token': generate_token(user), 'user': safe_user(user)}), 201

    except Exception as e:
        print('Register error:', e)
        return jsonify({'error': 'Registration failed. Please try again.'}), 500


# Check username availability
@auth_bp.route('/check-username', methods=['GET'])
def check_username():
    """Case-insensitive lookup — returns {available: true/false}."""
    name = request.args.get('name', '').strip()
    if not name:
        return jsonify({'available': False, 'error': 'Name is required.'}), 400
    existing = db_get('SELECT id FROM users WHERE LOWER(name) = LOWER(%s)', (name,))
    return jsonify({'available': existing is None})


# Change password
@auth_bp.route('/change-password', methods=['PUT'])
@require_auth
def change_password():
    """Verify current password, validate the new one, then update."""
    try:
        data       = request.get_json()
        current_pw = data.get('currentPassword', '')
        new_pw     = data.get('newPassword', '')
        confirm_pw = data.get('confirmPassword', '')

        if not current_pw or not new_pw or not confirm_pw:
            return jsonify({'error': 'All fields are required.'}), 400
        if new_pw != confirm_pw:
            return jsonify({'error': 'New passwords do not match.'}), 400
        if not is_strong_password(new_pw):
            return jsonify({'error': 'Password must include uppercase, lowercase, numbers, and symbols.'}), 400

        user = db_get('SELECT * FROM users WHERE id = %s', (g.user_id,))
        if not user:
            return jsonify({'error': 'User not found.'}), 404
        if not bcrypt.checkpw(current_pw.encode(), user['password'].encode()):
            return jsonify({'error': 'Current password is incorrect.'}), 401

        hashed = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
        db_run('UPDATE users SET password = %s WHERE id = %s', (hashed, g.user_id))
        return jsonify({'message': 'Password updated successfully.'})

    except Exception as e:
        print('Change password error:', e)
        return jsonify({'error': 'Failed to update password. Please try again.'}), 500


# Login user
@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data     = request.get_json()
        email    = data.get('email', '').strip()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'error': 'Email and password are required.'}), 400

        user = db_get('SELECT * FROM users WHERE email = %s', (email,))
        if not user:
            return jsonify({'error': 'Wrong email or password.'}), 401

        if not bcrypt.checkpw(password.encode(), user['password'].encode()):
            return jsonify({'error': 'Wrong email or password.'}), 401

        today = datetime.now().strftime('%Y-%m-%d')
        init_tasks_for_user(user['id'], today)

        return jsonify({'token': generate_token(user), 'user': safe_user(user)})

    except Exception as e:
        print('Login error:', e)
        return jsonify({'error': 'Login failed. Please try again.'}), 500
