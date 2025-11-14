"""WebSocket event handlers for real-time chat."""

from flask import request
from flask_socketio import emit, disconnect
from datetime import datetime
from ..app import socketio
from ..auth import get_user_by_session_token
from ..db import get_db, Conversation, Message, Document
from ..store import search_user_documents, get_context_from_results
from ..utils import get_provider_from_model
from ..utils.llm_providers import get_provider
from .settings import get_user_api_key

# Store connected users
connected_users = {}


@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection with authentication."""
    # Get token from query string or auth header
    token = request.args.get('token')
    
    if not token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
    
    if not token:
        print("No token provided for WebSocket connection")
        disconnect()
        return False
    
    # Authenticate user
    user = get_user_by_session_token(token)
    
    if not user:
        print("Invalid token for WebSocket connection")
        disconnect()
        return False
    
    # Store user connection
    connected_users[request.sid] = user.id
    
    print(f"User {user.username} connected via WebSocket")
    emit('connected', {'message': 'Connected successfully', 'user_id': user.id})
    
    return True


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    user_id = connected_users.pop(request.sid, None)
    if user_id:
        print(f"User {user_id} disconnected from WebSocket")


@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle incoming chat message with RAG and streaming response.
    
    Expected data:
        conversation_id: ID of the conversation
        message: User's message text
        model: LLM model to use
        selected_doc_ids: List of document IDs to use for RAG (optional)
    """
    # Get user
    user_id = connected_users.get(request.sid)
    if not user_id:
        emit('error', {'message': 'Not authenticated'})
        return
    
    # Extract data
    conversation_id = data.get('conversation_id')
    user_message = data.get('message')
    model = data.get('model', 'gpt-4')
    
    if not conversation_id or not user_message:
        emit('error', {'message': 'conversation_id and message are required'})
        return
    
    db = get_db()
    
    # Verify conversation belongs to user
    conversation = db.query(Conversation).filter_by(id=conversation_id, user_id=user_id).first()
    
    if not conversation:
        emit('error', {'message': 'Conversation not found'})
        return
    
    try:
        # Get user's API key for the selected model
        provider_name = get_provider_from_model(model)
        api_key = get_user_api_key(user_id, provider_name)
        
        if not api_key:
            emit('error', {
                'message': f'No API key configured for {provider_name}. Please add your API key in settings.'
            })
            return
        
        # Save user message to database
        user_msg = Message(
            conversation_id=conversation_id,
            role='user',
            content=user_message,
            timestamp=datetime.utcnow()
        )
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)
        
        # Emit acknowledgment
        emit('message_saved', {'message_id': user_msg.id})
        
        # Perform RAG automatically across all user documents
        # This replaces the old "attached documents" logic with automatic search
        context = ""
        
        # Check if user has any documents
        doc_count = db.query(Document).filter_by(user_id=user_id).count()
        
        if doc_count > 0:
            # Search across all user documents automatically
            search_results = search_user_documents(
                user_id,
                user_message,
                n_results=10
            )
            
            # Build context from results
            context = get_context_from_results(search_results, max_chunks=10)
        
        # Build message history for LLM
        messages = []
        
        # Add system message with context if available
        if context:
            system_message = ( # TODO: Add custom system message for the conversation
                "You are a helpful assistant. Use the following context from the user's documents "
                "to answer their question. If the context doesn't contain relevant information, "
                "you can use your general knowledge.\n\n"
                f"Context:\n{context}"
            )
        else:
            system_message = "You are a helpful assistant."
        
        messages.append({
            'role': 'system',
            'content': system_message
        })
        
        # Add conversation history (last 10 messages for context)
        history_messages = db.query(Message).filter_by(
            conversation_id=conversation_id
        ).order_by(Message.timestamp.desc()).limit(10).all()
        
        # Reverse to get chronological order
        history_messages.reverse()
        
        for msg in history_messages[:-1]:  # Exclude the message we just added
            messages.append({
                'role': msg.role,
                'content': msg.content
            })
        
        # Add current user message
        messages.append({
            'role': 'user',
            'content': user_message
        })
        
        # Stream LLM response using user's API key
        full_response = ""
        
        emit('chat_response_start', {'message_id': user_msg.id})
        
        # Get provider with user's API key
        provider_class = get_provider(provider_name).__class__
        provider = provider_class(api_key=api_key)
        
        for chunk in provider.stream_chat(messages, model):
            full_response += chunk
            emit('chat_response_chunk', {'chunk': chunk})
        
        emit('chat_response_end', {})
        
        # Save assistant message to database
        assistant_msg = Message(
            conversation_id=conversation_id,
            role='assistant',
            content=full_response,
            model_used=model,
            timestamp=datetime.utcnow()
        )
        db.add(assistant_msg)
        
        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        
        # Update conversation title if it's the first message
        if len(history_messages) <= 1:
            # Generate a simple title from the first user message
            title = user_message[:50] + ('...' if len(user_message) > 50 else '')
            conversation.title = title
        
        db.commit()
        db.refresh(assistant_msg)
        
        emit('message_complete', {
            'user_message_id': user_msg.id,
            'assistant_message_id': assistant_msg.id
        })
        
    except Exception as e:
        print(f"Error handling chat message: {e}")
        import traceback
        traceback.print_exc()
        emit('error', {'message': f'Error processing message: {str(e)}'})
        db.rollback()


@socketio.on('typing')
def handle_typing(data):
    """Handle typing indicator (optional feature for future)."""
    user_id = connected_users.get(request.sid)
    if user_id:
        conversation_id = data.get('conversation_id')
        # Broadcast typing indicator to other users in the conversation (if multi-user)
        pass

