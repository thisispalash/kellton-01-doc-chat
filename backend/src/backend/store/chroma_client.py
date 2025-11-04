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


def create_collection(collection_name):
    """Create a new collection in ChromaDB.
    
    Args:
        collection_name: Name for the collection
        
    Returns:
        Collection object
    """
    client = get_chroma_client()
    
    # Delete collection if it already exists
    try:
        client.delete_collection(name=collection_name)
    except:
        pass
    
    # Create new collection
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    
    return collection


def get_collection(collection_name):
    """Get an existing collection from ChromaDB.
    
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


def add_documents_to_collection(collection, chunks, embeddings, doc_id):
    """Add document chunks to a collection.
    
    Args:
        collection: ChromaDB collection object
        chunks: List of chunk dicts with 'text', 'page_number', 'chunk_index'
        embeddings: List of embedding vectors
        doc_id: Document ID for metadata
    """
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


def delete_collection(collection_name):
    """Delete a collection from ChromaDB.
    
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


def collection_exists(collection_name):
    """Check if a collection exists.
    
    Args:
        collection_name: Name of the collection
        
    Returns:
        True if collection exists, False otherwise
    """
    return get_collection(collection_name) is not None

