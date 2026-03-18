"""
Authentication API
"""
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
import jwt
import os
import re
from functools import wraps

from app import db, limiter
from app.models.backup import User
from app.config import Config

auth_bp = Blueprint('auth', __name__)


def validate_password(password):
    """
    Validate password strength according to best practices 2025
    Returns: (is_valid, error_message)
    """
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"

    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"

    return True, None


def token_required(f):
    """Decorator for protected routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        try:
            data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            current_user = User.query.filter_by(id=data['user_id']).first()
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")  # Rate limiting: max 5 login attempts per minute
def login():
    """User login with rate limiting"""
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Missing username or password'}), 400

    user = User.query.filter_by(username=data['username']).first()

    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.session.commit()

    # Generate token
    token = jwt.encode({
        'user_id': user.id,
        'username': user.username,
        'exp': datetime.now(timezone.utc) + Config.JWT_ACCESS_TOKEN_EXPIRES
    }, Config.JWT_SECRET_KEY, algorithm='HS256')

    return jsonify({
        'access_token': token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/register', methods=['POST'])
@token_required
@limiter.limit("3 per hour")
def register(current_user):
    """User registration (admin only, rate limited)"""
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Missing username or password'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400

    # Validate password strength
    is_valid, error_msg = validate_password(data['password'])
    if not is_valid:
        return jsonify({'error': error_msg}), 400

    password_hash = generate_password_hash(data['password'])
    new_user = User(username=data['username'], password_hash=password_hash)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        'message': 'User created successfully',
        'user': new_user.to_dict()
    }), 201


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """Get current user information"""
    return jsonify(current_user.to_dict()), 200


@auth_bp.route('/password', methods=['PUT'])
@token_required
def change_password(current_user):
    """Change user password"""
    data = request.get_json()

    if not data or not data.get('new_password'):
        return jsonify({'error': 'New password is required'}), 400

    # Validate password strength
    is_valid, error_msg = validate_password(data['new_password'])
    if not is_valid:
        return jsonify({'error': error_msg}), 400

    # Update password
    current_user.password_hash = generate_password_hash(data['new_password'])
    db.session.commit()

    return jsonify({'message': 'Password changed successfully'}), 200


@auth_bp.route('/init', methods=['POST'])
def init_admin():
    """Initialize admin user if none exists"""
    if User.query.count() > 0:
        return jsonify({'error': 'Users already exist'}), 400

    import secrets
    password = secrets.token_urlsafe(16)
    password_hash = generate_password_hash(password)

    admin_user = User(username='admin', password_hash=password_hash)
    db.session.add(admin_user)
    db.session.commit()

    return jsonify({
        'message': 'Admin user created',
        'username': 'admin',
        'password': password,
        'warning': 'Save this password securely! It will not be shown again.'
    }), 201
