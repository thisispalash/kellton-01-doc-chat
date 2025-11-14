"""Configuration module for the backend application."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Config:
    """Application configuration."""
    
    # Flask
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', str(BASE_DIR / 'instance' / 'app.db'))
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Storage
    UPLOADS_PATH = os.getenv('UPLOADS_PATH', str(BASE_DIR / 'uploads'))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # ChromaDB
    CHROMA_PATH = os.getenv('CHROMA_PATH', str(BASE_DIR / 'instance' / 'chroma'))
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '500'))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '50'))

    # Memory / Conversation search
    MEMORY_ENABLED = os.getenv('MEMORY_ENABLED', 'true').lower() == 'true'
    MEMORY_MAX_RESULTS = int(os.getenv('MEMORY_MAX_RESULTS', '3'))
    MEMORY_SEARCH_BOTH_TYPES = os.getenv('MEMORY_SEARCH_BOTH_TYPES', 'true').lower() == 'true'
    
    # LLM API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
    GROK_API_KEY = os.getenv('GROK_API_KEY', '')
    
    # Session
    SESSION_EXPIRY_HOURS = int(os.getenv('SESSION_EXPIRY_HOURS', '24'))
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    @staticmethod
    def init_app(app):
        """Initialize application directories."""
        os.makedirs(Config.UPLOADS_PATH, exist_ok=True)
        os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
        os.makedirs(Config.CHROMA_PATH, exist_ok=True)

