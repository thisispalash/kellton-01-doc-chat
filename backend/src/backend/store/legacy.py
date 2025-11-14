"""Legacy utilities for migration scripts only.

WARNING: DO NOT use these functions in application code.

These functions exist solely to support migration scripts that need to
interact with the old per-document collection architecture. They allow
migrations to read from and clean up old collections.

For all application code, use the functions in chroma_client.py which
implement the new per-user collection architecture.
"""

import chromadb
from .chroma_client import get_chroma_client


def get_collection(collection_name):
    """Get an existing collection from ChromaDB by name.
    
    This is a legacy utility for migration scripts only. Application code
    should use get_or_create_user_collection() instead.
    
    Args:
        collection_name: Name of the collection
        
    Returns:
        Collection object or None if not found
    """
    client = get_chroma_client()
    
    try:
        return client.get_collection(name=collection_name)
    except Exception as e:
        print(f"Error getting collection {collection_name}: {e}")
        return None


def delete_collection(collection_name):
    """Delete a collection from ChromaDB by name.
    
    This is a legacy utility for migration scripts only. Application code
    should use remove_document_from_collection() to remove specific documents
    from a user's collection.
    
    Args:
        collection_name: Name of the collection to delete
        
    Returns:
        True if deleted successfully, False otherwise
    """
    client = get_chroma_client()
    
    try:
        client.delete_collection(name=collection_name)
        return True
    except Exception as e:
        print(f"Error deleting collection {collection_name}: {e}")
        return False

