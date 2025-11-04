"""Backend application package."""

from .app import create_app, socketio

__version__ = '0.1.0'
__all__ = ['create_app', 'socketio']

