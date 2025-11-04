"""Session management utilities."""

from datetime import datetime
from ..db import get_db, Session, User


def create_session(user, hours=24):
    """Create a new session for a user.
    
    Args:
        user: User object
        hours: Session expiry in hours (default: 24)
        
    Returns:
        Session object with token
    """
    db = get_db()
    
    # Clean up expired sessions for this user
    cleanup_expired_sessions(user.id)
    
    # Create new session
    session = Session.create_for_user(user, hours)
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return session


def get_session_by_token(token):
    """Get a session by its token.
    
    Args:
        token: Session token string
        
    Returns:
        Session object if valid, None otherwise
    """
    db = get_db()
    session = db.query(Session).filter_by(session_token=token).first()
    
    if session and session.is_valid():
        return session
    
    # Clean up invalid session
    if session:
        db.delete(session)
        db.commit()
    
    return None


def get_user_by_session_token(token):
    """Get a user by their session token.
    
    Args:
        token: Session token string
        
    Returns:
        User object if session is valid, None otherwise
    """
    session = get_session_by_token(token)
    if session:
        db = get_db()
        return db.query(User).filter_by(id=session.user_id).first()
    return None


def invalidate_session(token):
    """Invalidate a session by its token.
    
    Args:
        token: Session token string
        
    Returns:
        True if session was invalidated, False otherwise
    """
    db = get_db()
    session = db.query(Session).filter_by(session_token=token).first()
    
    if session:
        db.delete(session)
        db.commit()
        return True
    
    return False


def cleanup_expired_sessions(user_id=None):
    """Clean up expired sessions.
    
    Args:
        user_id: Optional user ID to clean up sessions for specific user
    """
    db = get_db()
    query = db.query(Session).filter(Session.expires_at < datetime.utcnow())
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    expired_sessions = query.all()
    for session in expired_sessions:
        db.delete(session)
    
    if expired_sessions:
        db.commit()

