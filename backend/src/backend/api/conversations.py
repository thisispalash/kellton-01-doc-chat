"""Conversation management API routes."""

from flask import Blueprint, request, jsonify
from datetime import datetime
from ..db import get_db, Conversation, Message
from ..auth import require_auth

conversations_bp = Blueprint('conversations', __name__)


@conversations_bp.route('', methods=['GET'])
@require_auth
def list_conversations(current_user):
    """List all conversations for the current user.
    
    Requires Authorization header with Bearer token.
    
    Returns:
        List of conversation objects
    """
    db = get_db()
    conversations = db.query(Conversation).filter_by(user_id=current_user.id).order_by(Conversation.updated_at.desc()).all()
    
    return jsonify([conv.to_dict() for conv in conversations]), 200


@conversations_bp.route('', methods=['POST'])
@require_auth
def create_conversation(current_user):
    """Create a new conversation.
    
    Requires Authorization header with Bearer token.
    
    Request body:
        title: Optional conversation title
        
    Returns:
        Conversation object
    """
    data = request.get_json() or {}
    title = data.get('title', 'New Conversation')
    
    db = get_db()
    
    conversation = Conversation(
        user_id=current_user.id,
        title=title
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return jsonify(conversation.to_dict()), 201


@conversations_bp.route('/<int:conv_id>', methods=['GET'])
@require_auth
def get_conversation(current_user, conv_id):
    """Get a specific conversation with its messages.
    
    Requires Authorization header with Bearer token.
    
    Args:
        conv_id: Conversation ID
        
    Returns:
        Conversation object with messages
    """
    db = get_db()
    conversation = db.query(Conversation).filter_by(id=conv_id, user_id=current_user.id).first()
    
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    return jsonify(conversation.to_dict(include_messages=True)), 200


@conversations_bp.route('/<int:conv_id>', methods=['PUT'])
@require_auth
def update_conversation(current_user, conv_id):
    """Update a conversation (e.g., change title).
    
    Requires Authorization header with Bearer token.
    
    Args:
        conv_id: Conversation ID
        
    Request body:
        title: New conversation title
        
    Returns:
        Updated conversation object
    """
    data = request.get_json()
    
    if not data or 'title' not in data:
        return jsonify({'error': 'Title is required'}), 400
    
    db = get_db()
    conversation = db.query(Conversation).filter_by(id=conv_id, user_id=current_user.id).first()
    
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    conversation.title = data['title']
    conversation.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(conversation)
    
    return jsonify(conversation.to_dict()), 200


@conversations_bp.route('/<int:conv_id>', methods=['DELETE'])
@require_auth
def delete_conversation(current_user, conv_id):
    """Delete a conversation and all its messages.
    
    Requires Authorization header with Bearer token.
    
    Args:
        conv_id: Conversation ID
        
    Returns:
        {message: 'Conversation deleted'}
    """
    db = get_db()
    conversation = db.query(Conversation).filter_by(id=conv_id, user_id=current_user.id).first()
    
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    db.delete(conversation)
    db.commit()
    
    return jsonify({'message': 'Conversation deleted'}), 200

