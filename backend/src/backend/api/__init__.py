"""API routes module."""

from .auth import auth_bp
from .documents import documents_bp
from .conversations import conversations_bp

__all__ = ['auth_bp', 'documents_bp', 'conversations_bp']

