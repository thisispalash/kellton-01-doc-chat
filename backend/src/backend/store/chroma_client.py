"""ChromaDB client for vector storage."""

import chromadb
from chromadb.config import Settings
from ..config import Config

# Global ChromaDB client
_chroma_client = None


def get_chroma_client():
    """Get or initialize the ChromaDB client.
    
    Returns:
        ChromaDB client instance
    """
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=Config.CHROMA_PATH,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
    return _chroma_client


def get_or_create_user_collection(user_id, collection_type='default'):
    """Get or create a user-specific collection.
    
    This is the new architecture where each user has collections like:
    - user_{user_id}_default: For all document chunks
    - user_{user_id}_conversations: For message/conversation embeddings
    
    Args:
        user_id: User ID
        collection_type: Type of collection ('default' or 'conversations')
        
    Returns:
        Collection object
    """
    collection_name = f"user_{user_id}_{collection_type}"
    client = get_chroma_client()
    
    try:
        # Try to get existing collection
        collection = client.get_collection(name=collection_name)
        return collection
    except:
        # Create new collection if it doesn't exist
        collection = client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        return collection


def add_documents_to_user_collection(user_id, chunks, embeddings, doc_id):
    """Add document chunks to a user's default collection.
    
    All documents for a user are stored in the same collection (user_{user_id}_default)
    with doc_id in metadata for filtering and organization.
    
    Args:
        user_id: User ID
        chunks: List of chunk dicts with 'text', 'page_number', 'chunk_index'
        embeddings: List of embedding vectors
        doc_id: Document ID for metadata
    """
    collection = get_or_create_user_collection(user_id, 'default')
    
    ids = [f"doc_{doc_id}_chunk_{chunk['chunk_index']}" for chunk in chunks]
    documents = [chunk['text'] for chunk in chunks]
    metadatas = [
        {
            'doc_id': str(doc_id),
            'page_number': chunk['page_number'],
            'chunk_index': chunk['chunk_index']
        }
        for chunk in chunks
    ]
    
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )


def remove_document_from_collection(user_id, doc_id):
    """Remove all chunks of a specific document from user's collection.
    
    Instead of deleting entire collections (old architecture), this removes
    chunks by filtering on doc_id metadata.
    
    Args:
        user_id: User ID
        doc_id: Document ID to remove
        
    Returns:
        True if successful, False otherwise
    """
    collection = get_or_create_user_collection(user_id, 'default')
    
    try:
        # Get all chunk IDs for this document
        results = collection.get(
            where={"doc_id": str(doc_id)},
            include=[]  # We only need IDs
        )
        
        if results and results['ids']:
            # Delete all chunks for this document
            collection.delete(ids=results['ids'])
            return True
        
        return True  # No chunks found, consider it successful
    except Exception as e:
        print(f"Error removing document {doc_id} from user {user_id} collection: {e}")
        return False


def add_message_to_conversation_collection(user_id, message_id, conversation_id, text, embedding, message_type='user_message'):
    """Add a message embedding to user's conversation collection.
    
    NOTE: This is infrastructure setup for future "memory" feature.
    The function is ready but not actively used yet.
    
    Future use cases:
    - Semantic search across past conversations
    - Memory feature to recall relevant past discussions
    - Cross-conversation insights
    
    Args:
        user_id: User ID
        message_id: Message ID
        conversation_id: Conversation ID
        text: Message text content
        embedding: Message embedding vector
        message_type: Type of message ('user_message' or 'assistant_message')
    """
    collection = get_or_create_user_collection(user_id, 'conversations')
    
    message_unique_id = f"conv_{conversation_id}_msg_{message_id}"
    
    collection.add(
        ids=[message_unique_id],
        embeddings=[embedding],
        documents=[text],
        metadatas=[{
            'message_id': str(message_id),
            'conversation_id': str(conversation_id),
            'type': message_type
        }]
    )

