"""Vector search functionality."""

from .chroma_client import get_or_create_user_collection
from .embeddings import generate_embedding


def search_user_documents(user_id, query_text, doc_ids=None, n_results=10):
    """Search user's documents using their unified collection.
    
    This is the new architecture where all user documents are in one collection
    (user_{user_id}_default) and can be filtered by doc_id if needed.
    
    Args:
        user_id: User ID
        query_text: Query text to search for
        doc_ids: Optional list of document IDs to filter by (for folder/project feature)
        n_results: Number of results to return (default: 10)
        
    Returns:
        List of result dicts with 'text', 'metadata', 'distance'
    """
    collection = get_or_create_user_collection(user_id, 'default')
    
    # Generate embedding for query
    query_embedding = generate_embedding(query_text)
    
    # Build where clause for filtering if doc_ids provided
    where_clause = None
    if doc_ids:
        # Convert to strings since metadata stores as strings
        doc_ids_str = [str(doc_id) for doc_id in doc_ids]
        if len(doc_ids_str) == 1:
            where_clause = {"doc_id": doc_ids_str[0]}
        else:
            where_clause = {"doc_id": {"$in": doc_ids_str}}
    
    # Perform search
    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause,
            include=['documents', 'metadatas', 'distances']
        )
    except Exception as e:
        print(f"Error searching user {user_id} documents: {e}")
        return []
    
    # Format results
    formatted_results = []
    if results and results['documents'] and results['documents'][0]:
        for i in range(len(results['documents'][0])):
            formatted_results.append({
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            })
    
    return formatted_results


def get_context_from_results(results, max_chunks=10):
    """Convert search results into context text for LLM.
    
    Args:
        results: Search results from search_documents or search_multiple_documents
        max_chunks: Maximum number of chunks to include (default: 10)
        
    Returns:
        Formatted context string
    """
    context_parts = []
    chunk_count = 0
    
    # Handle results from search_multiple_documents (dict)
    if isinstance(results, dict):
        for collection_name, collection_results in results.items():
            for result in collection_results:
                if chunk_count >= max_chunks:
                    break
                
                context_parts.append(
                    f"[Document: {result['metadata'].get('doc_id', 'unknown')}, "
                    f"Page {result['metadata'].get('page_number', 'unknown')}]\n"
                    f"{result['text']}"
                )
                chunk_count += 1
            
            if chunk_count >= max_chunks:
                break
    
    # Handle results from search_documents (list)
    elif isinstance(results, list):
        for result in results[:max_chunks]:
            context_parts.append(
                f"[Document: {result['metadata'].get('doc_id', 'unknown')}, "
                f"Page {result['metadata'].get('page_number', 'unknown')}]\n"
                f"{result['text']}"
            )
    
    if not context_parts:
        return ""
    
    return "\n\n---\n\n".join(context_parts)

