"""Authentication API routes."""

from flask import Blueprint, request, jsonify
from ..db import get_db, User
from ..auth import create_session, invalidate_session, require_auth
from ..config import Config

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/check-password', methods=['POST'])
def check_password():
    """Check if a password exists in the system.
    
    Request body:
        password: Password to check
        
    Returns:
        {exists: bool, user_id: int (if exists)}
    """
    data = request.get_json()
    password = data.get('password')
    
    if not password:
        return jsonify({'error': 'Password is required'}), 400
    
    db = get_db()
    
    # Check all users for password match
    users = db.query(User).all()
    
    for user in users:
        if user.check_password(password): # TODO: check all users for password match, not just the first one
            return jsonify({
                'exists': True,
                'user_id': user.id
            }), 200
    
    return jsonify({'exists': False}), 200


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login with username and password.
    
    Request body:
        username: Username
        password: Password
        
    Returns:
        {session_token, user, expires_at}
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    db = get_db()
    
    # Find user by username
    user = db.query(User).filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    # Create session
    session = create_session(user, hours=Config.SESSION_EXPIRY_HOURS)
    
    return jsonify({
        'session_token': session.session_token,
        'user': user.to_dict(),
        'expires_at': session.expires_at.isoformat()
    }), 200


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user.
    
    Request body:
        username: Username (must be unique)
        password: Password (min 8 characters)
        
    Returns:
        {session_token, user, expires_at}
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400
    
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    
    db = get_db()
    
    # Check if username already exists
    existing_user = db.query(User).filter_by(username=username).first()
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 400
    
    # Create new user
    user = User(username=username)
    user.set_password(password)
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create session
    session = create_session(user, hours=Config.SESSION_EXPIRY_HOURS)
    
    return jsonify({
        'session_token': session.session_token,
        'user': user.to_dict(),
        'expires_at': session.expires_at.isoformat()
    }), 201


@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout(current_user):
    """Logout the current user.
    
    Requires Authorization header with Bearer token.
    
    Returns:
        {message: 'Logged out successfully'}
    """
    auth_header = request.headers.get('Authorization')
    token = auth_header.split()[1] if auth_header else None
    
    if token:
        invalidate_session(token)
    
    return jsonify({'message': 'Logged out successfully'}), 200


@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user(current_user):
    """Get the current user's information.
    
    Requires Authorization header with Bearer token.
    
    Returns:
        User object
    """
    return jsonify(current_user.to_dict()), 200

