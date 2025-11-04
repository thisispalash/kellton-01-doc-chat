"""SQLAlchemy database models."""

from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import bcrypt
import secrets

Base = declarative_base()


class User(Base):
    """User model."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sessions = relationship('Session', back_populates='user', cascade='all, delete-orphan')
    conversations = relationship('Conversation', back_populates='user', cascade='all, delete-orphan')
    documents = relationship('Document', back_populates='user', cascade='all, delete-orphan')
    api_keys = relationship('ApiKey', back_populates='user', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Check if the provided password matches the hash."""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Session(Base):
    """Session model for managing user sessions."""
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='sessions')
    
    @staticmethod
    def generate_token():
        """Generate a secure session token."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def create_for_user(user, hours=24):
        """Create a new session for a user."""
        session = Session(
            user_id=user.id,
            session_token=Session.generate_token(),
            expires_at=datetime.utcnow() + timedelta(hours=hours)
        )
        return session
    
    def is_valid(self):
        """Check if the session is still valid."""
        return datetime.utcnow() < self.expires_at
    
    def to_dict(self):
        """Convert session to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_token': self.session_token,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


class Conversation(Base):
    """Conversation model."""
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String(255), default='New Conversation')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='conversations')
    messages = relationship('Message', back_populates='conversation', cascade='all, delete-orphan', order_by='Message.timestamp')
    conversation_documents = relationship('ConversationDocument', back_populates='conversation', cascade='all, delete-orphan')
    
    def to_dict(self, include_messages=False, include_documents=False):
        """Convert conversation to dictionary."""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'message_count': len(self.messages)
        }
        if include_messages:
            data['messages'] = [msg.to_dict() for msg in self.messages]
        if include_documents:
            data['attached_documents'] = [cd.document.to_dict() for cd in self.conversation_documents]
        return data


class Message(Base):
    """Message model."""
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    model_used = Column(String(100))  # The LLM model used for assistant messages
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship('Conversation', back_populates='messages')
    
    def to_dict(self):
        """Convert message to dictionary."""
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'role': self.role,
            'content': self.content,
            'model_used': self.model_used,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class Document(Base):
    """Document model."""
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    chroma_collection_id = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='documents')
    conversation_documents = relationship('ConversationDocument', back_populates='document', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert document to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'chroma_collection_id': self.chroma_collection_id,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
        }


class ApiKey(Base):
    """API Key model for storing encrypted user API keys."""
    __tablename__ = 'api_keys'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    provider = Column(String(50), nullable=False)  # 'openai', 'anthropic', 'google', 'grok'
    encrypted_key = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='api_keys')
    
    def to_dict(self, include_key=False):
        """Convert API key to dictionary."""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'provider': self.provider,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_key:
            data['encrypted_key'] = self.encrypted_key
        return data


class ConversationDocument(Base):
    """Junction table for many-to-many relationship between conversations and documents."""
    __tablename__ = 'conversation_documents'
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    attached_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship('Conversation', back_populates='conversation_documents')
    document = relationship('Document', back_populates='conversation_documents')
    
    def to_dict(self):
        """Convert conversation document to dictionary."""
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'document_id': self.document_id,
            'attached_at': self.attached_at.isoformat() if self.attached_at else None
        }

