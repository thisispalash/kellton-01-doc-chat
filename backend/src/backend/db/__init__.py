"""Database initialization and utilities."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from .models import Base, User, Session, Conversation, Message, Document, ApiKey, ConversationDocument

# Global session factory
SessionLocal = None
engine = None


def init_db(app):
    """Initialize the database with the Flask app."""
    global SessionLocal, engine
    
    # Create engine
    engine = create_engine(
        app.config['SQLALCHEMY_DATABASE_URI'],
        echo=app.config['DEBUG']
    )
    
    # Create session factory
    SessionLocal = scoped_session(sessionmaker(bind=engine))
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Add teardown context
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        if SessionLocal:
            SessionLocal.remove()
    
    return engine


def get_db():
    """Get a database session."""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db first.")
    return SessionLocal()


__all__ = ['init_db', 'get_db', 'User', 'Session', 'Conversation', 'Message', 'Document', 'ApiKey', 'ConversationDocument']

