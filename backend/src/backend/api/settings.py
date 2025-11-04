"""Settings API routes for user preferences and API keys."""

from flask import Blueprint, request, jsonify
from datetime import datetime
from ..db import get_db, ApiKey
from ..auth import require_auth
from ..utils.encryption import encrypt_api_key, decrypt_api_key

settings_bp = Blueprint('settings', __name__)

VALID_PROVIDERS = ['openai', 'anthropic', 'google', 'grok']


@settings_bp.route('/api-keys', methods=['GET'])
@require_auth
def get_api_keys(current_user):
    """Get list of configured API keys (without actual keys).
    
    Requires Authorization header with Bearer token.
    
    Returns:
        List of providers with configuration status
    """
    db = get_db()
    api_keys = db.query(ApiKey).filter_by(user_id=current_user.id).all()
    
    # Return providers with status
    configured_providers = {key.provider for key in api_keys}
    
    result = []
    for provider in VALID_PROVIDERS:
        result.append({
            'provider': provider,
            'configured': provider in configured_providers,
            'updated_at': next((key.updated_at.isoformat() for key in api_keys if key.provider == provider), None)
        })
    
    return jsonify(result), 200


@settings_bp.route('/api-keys', methods=['POST'])
@require_auth
def save_api_key(current_user):
    """Save or update an API key for a provider.
    
    Requires Authorization header with Bearer token.
    
    Request body:
        provider: Provider name (openai, anthropic, google, grok)
        api_key: API key to save
        
    Returns:
        Success message
    """
    data = request.get_json()
    provider = data.get('provider', '').lower()
    api_key = data.get('api_key', '')
    
    if not provider or provider not in VALID_PROVIDERS:
        return jsonify({'error': f'Invalid provider. Must be one of: {", ".join(VALID_PROVIDERS)}'}), 400
    
    if not api_key:
        return jsonify({'error': 'API key is required'}), 400
    
    db = get_db()
    
    # Check if key already exists for this provider
    existing_key = db.query(ApiKey).filter_by(
        user_id=current_user.id,
        provider=provider
    ).first()
    
    # Encrypt the API key
    encrypted_key = encrypt_api_key(api_key)
    
    if existing_key:
        # Update existing key
        existing_key.encrypted_key = encrypted_key
        existing_key.updated_at = datetime.utcnow()
        message = f'API key for {provider} updated successfully'
    else:
        # Create new key
        new_key = ApiKey(
            user_id=current_user.id,
            provider=provider,
            encrypted_key=encrypted_key
        )
        db.add(new_key)
        message = f'API key for {provider} added successfully'
    
    db.commit()
    
    return jsonify({'message': message}), 200


@settings_bp.route('/api-keys/<provider>', methods=['DELETE'])
@require_auth
def delete_api_key(current_user, provider):
    """Delete an API key for a provider.
    
    Requires Authorization header with Bearer token.
    
    Args:
        provider: Provider name
        
    Returns:
        Success message
    """
    provider = provider.lower()
    
    if provider not in VALID_PROVIDERS:
        return jsonify({'error': f'Invalid provider. Must be one of: {", ".join(VALID_PROVIDERS)}'}), 400
    
    db = get_db()
    
    api_key = db.query(ApiKey).filter_by(
        user_id=current_user.id,
        provider=provider
    ).first()
    
    if not api_key:
        return jsonify({'error': f'No API key found for {provider}'}), 404
    
    db.delete(api_key)
    db.commit()
    
    return jsonify({'message': f'API key for {provider} deleted successfully'}), 200


def get_user_api_key(user_id, provider):
    """Helper function to get decrypted API key for a user and provider.
    
    Args:
        user_id: User ID
        provider: Provider name
        
    Returns:
        Decrypted API key or None if not found
    """
    db = get_db()
    
    api_key = db.query(ApiKey).filter_by(
        user_id=user_id,
        provider=provider
    ).first()
    
    if not api_key:
        return None
    
    return decrypt_api_key(api_key.encrypted_key)

