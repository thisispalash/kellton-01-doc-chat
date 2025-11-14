"""Vector store module for ChromaDB operations."""

from .embeddings import (
    get_embedding_model,
    extract_text_from_pdf,
    process_pdf_to_chunks,
    generate_embeddings,
    generate_embedding
)
from .chroma_client import (
    get_chroma_client,
    get_or_create_user_collection,
    add_documents_to_user_collection,
    remove_document_from_collection,
    add_message_to_conversation_collection
)
from .search import (
    search_user_documents,
    get_context_from_results
)

__all__ = [
    'get_embedding_model',
    'extract_text_from_pdf',
    'process_pdf_to_chunks',
    'generate_embeddings',
    'generate_embedding',
    'get_chroma_client',
    'get_or_create_user_collection',
    'add_documents_to_user_collection',
    'remove_document_from_collection',
    'add_message_to_conversation_collection',
    'search_user_documents',
    'get_context_from_results'
]

