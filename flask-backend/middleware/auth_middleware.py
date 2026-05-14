# JWT Token Verification Middleware

import os
import jwt
from functools import wraps
from flask import request, jsonify, g


def require_auth(f):
    """JWT verification decorator."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No token provided. Please log in.'}), 401

        token = auth_header.split(' ', 1)[1]
        try:
            decoded = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
            g.user_id   = decoded['userId']
            g.user_role = decoded['role']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Invalid or expired token. Please log in again.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid or expired token. Please log in again.'}), 401

        return f(*args, **kwargs)
    return decorated


def admin_only(f):
    """Admin-only access decorator."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if g.user_role != 'admin':
            return jsonify({'error': 'Admin access required.'}), 403
        return f(*args, **kwargs)
    return decorated
