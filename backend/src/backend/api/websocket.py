"""WebSocket event handlers for real-time chat."""

from flask import request
from flask_socketio import emit, disconnect
from datetime import datetime
from ..app import socketio
from ..auth import get_user_by_session_token
from ..db import get_db, Conversation, Message, Document
from ..store import (
    search_user_documents,
    search_conversation_memory,
    get_context_from_results,
    format_memory_context,
    add_message_to_conversation_collection,
    generate_embedding
)
from ..utils import get_provider_from_model
from ..utils.llm_providers import get_provider
from .settings import get_user_api_key
from ..config import Config

# Store connected users
connected_users = {}


def _parse_bool(value, default=False):
    """Utility to parse booleans from various input types."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ('true', '1', 'yes', 'on')
    return bool(value)


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
    memory_enabled = _parse_bool(
        data.get('memory_enabled'),
        default=Config.MEMORY_ENABLED
    )
    
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
        
        # Store user message embedding in conversation memory (best-effort)
        if memory_enabled:
            try:
                user_embedding = generate_embedding(user_message)
                add_message_to_conversation_collection(
                    user_id=user_id,
                    message_id=user_msg.id,
                    conversation_id=conversation_id,
                    text=user_message,
                    embedding=user_embedding,
                    message_type='user_message'
                )
            except Exception as e:
                print(f"Warning: Failed to store user message embedding: {e}")

        # Emit acknowledgment
        emit('message_saved', {'message_id': user_msg.id})
        
        # Perform RAG automatically across all user documents
        document_context = ""
        
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
            document_context = get_context_from_results(search_results, max_chunks=10)

        # Retrieve conversation memory context if enabled
        memory_context = ""
        if memory_enabled:
            try:
                memory_types = None
                if not Config.MEMORY_SEARCH_BOTH_TYPES:
                    memory_types = ['user_message']

                memory_results = search_conversation_memory(
                    user_id,
                    user_message,
                    exclude_conversation_id=conversation_id,
                    n_results=Config.MEMORY_MAX_RESULTS,
                    message_types=memory_types
                )

                memory_context = format_memory_context(
                    memory_results,
                    max_items=Config.MEMORY_MAX_RESULTS
                )
            except Exception as e:
                print(f"Warning: Memory search failed: {e}")
        
        # Build message history for LLM
        messages = []
        
        # Build system message with combined context if available
        combined_context_parts = []
        if document_context:
            combined_context_parts.append(f"Document Context:\n{document_context}")
        if memory_context:
            combined_context_parts.append(f"Relevant Past Discussions:\n{memory_context}")

        combined_context = "\n\n".join(part for part in combined_context_parts if part)

        if combined_context:
            system_message = (
                "You are a helpful assistant. Use the following information to answer the user's "
                "question. Reference it naturally when relevant.\n\n"
                f"{combined_context}\n\n"
                "If the provided information does not contain an answer, rely on your general knowledge."
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
        
        # Store assistant message embedding in conversation memory (best-effort)
        if memory_enabled:
            try:
                assistant_embedding = generate_embedding(full_response)
                add_message_to_conversation_collection(
                    user_id=user_id,
                    message_id=assistant_msg.id,
                    conversation_id=conversation_id,
                    text=full_response,
                    embedding=assistant_embedding,
                    message_type='assistant_message'
                )
            except Exception as e:
                print(f"Warning: Failed to store assistant message embedding: {e}")

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

