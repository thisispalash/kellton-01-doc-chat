"""Authentication middleware and decorators."""

from functools import wraps
from flask import request, jsonify
from .session import get_user_by_session_token


def require_auth(f):
    """Decorator to require authentication for a route.
    
    Checks for Authorization header with Bearer token.
    Adds 'current_user' to kwargs if authenticated.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'No authorization token provided'}), 401
        
        # Parse Bearer token
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'error': 'Invalid authorization header format'}), 401
        
        token = parts[1]
        
        # Get user by token
        user = get_user_by_session_token(token)
        
        if not user:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Add user to kwargs
        kwargs['current_user'] = user
        
        return f(*args, **kwargs)
    
    return decorated_function


def get_current_user_from_request():
    """Get the current user from the request.
    
    Returns:
        User object if authenticated, None otherwise
    """
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return None
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    token = parts[1]
    return get_user_by_session_token(token)

