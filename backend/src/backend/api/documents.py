"""Document management API routes."""

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from pathlib import Path
from ..db import get_db, Document
from ..auth import require_auth
from ..storage import save_file, delete_file
from ..store import (
    process_pdf_to_chunks,
    generate_embeddings,
    create_collection,
    add_documents_to_collection,
    delete_collection
)

documents_bp = Blueprint('documents', __name__)


@documents_bp.route('/upload', methods=['POST'])
@require_auth
def upload_document(current_user):
    """Upload and process a PDF document.
    
    Requires:
        - Authorization header with Bearer token
        - File in 'file' field of multipart form
        
    Returns:
        Document object with id, filename, etc.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    db = get_db()
    
    # Create document record first to get ID
    document = Document(
        user_id=current_user.id,
        filename='',
        file_path='',
        chroma_collection_id=''
    )
    db.add(document)
    db.flush()  # Get the document ID without committing
    
    # Save file to disk
    file_path, original_filename = save_file(file, current_user.id, document.id)
    
    if not file_path:
        db.rollback()
        return jsonify({'error': 'Failed to save file'}), 500
    
    # Update document with file info
    document.filename = original_filename
    document.file_path = file_path
    
    # Create ChromaDB collection
    collection_name = f"doc_{current_user.id}_{document.id}"
    document.chroma_collection_id = collection_name
    
    try:
        # Process PDF to chunks
        chunks = process_pdf_to_chunks(file_path)
        
        if not chunks:
            db.rollback()
            delete_file(file_path)
            return jsonify({'error': 'Failed to extract text from PDF'}), 500
        
        # Generate embeddings
        texts = [chunk['text'] for chunk in chunks]
        embeddings = generate_embeddings(texts)
        
        # Create collection and add documents
        collection = create_collection(collection_name)
        add_documents_to_collection(collection, chunks, embeddings, document.id)
        
        # Commit the document
        db.commit()
        db.refresh(document)
        
        return jsonify(document.to_dict()), 201
        
    except Exception as e:
        db.rollback()
        delete_file(file_path)
        delete_collection(collection_name)
        return jsonify({'error': f'Failed to process document: {str(e)}'}), 500


@documents_bp.route('', methods=['GET'])
@require_auth
def list_documents(current_user):
    """List all documents for the current user.
    
    Requires Authorization header with Bearer token.
    
    Returns:
        List of document objects
    """
    db = get_db()
    documents = db.query(Document).filter_by(user_id=current_user.id).order_by(Document.uploaded_at.desc()).all()
    
    return jsonify([doc.to_dict() for doc in documents]), 200


@documents_bp.route('/<int:doc_id>', methods=['GET'])
@require_auth
def get_document(current_user, doc_id):
    """Get a specific document.
    
    Requires Authorization header with Bearer token.
    
    Args:
        doc_id: Document ID
        
    Returns:
        Document object
    """
    db = get_db()
    document = db.query(Document).filter_by(id=doc_id, user_id=current_user.id).first()
    
    if not document:
        return jsonify({'error': 'Document not found'}), 404
    
    return jsonify(document.to_dict()), 200


@documents_bp.route('/<int:doc_id>', methods=['DELETE'])
@require_auth
def delete_document(current_user, doc_id):
    """Delete a document.
    
    Requires Authorization header with Bearer token.
    
    Args:
        doc_id: Document ID
        
    Returns:
        {message: 'Document deleted'}
    """
    db = get_db()
    document = db.query(Document).filter_by(id=doc_id, user_id=current_user.id).first()
    
    if not document:
        return jsonify({'error': 'Document not found'}), 404
    
    # Delete file from disk
    delete_file(document.file_path)
    
    # Delete ChromaDB collection
    delete_collection(document.chroma_collection_id)
    
    # Delete document record
    db.delete(document)
    db.commit()
    
    return jsonify({'message': 'Document deleted'}), 200


@documents_bp.route('/<int:doc_id>/view', methods=['GET'])
@require_auth
def view_document(current_user, doc_id):
    """Serve a document file for viewing.
    
    Requires Authorization header with Bearer token.
    
    Args:
        doc_id: Document ID
        
    Returns:
        PDF file
    """
    db = get_db()
    document = db.query(Document).filter_by(id=doc_id, user_id=current_user.id).first()
    
    if not document:
        return jsonify({'error': 'Document not found'}), 404
    
    file_path = Path(document.file_path)
    
    if not file_path.exists():
        return jsonify({'error': 'File not found on disk'}), 404
    
    return send_file(
        str(file_path),
        mimetype='application/pdf',
        as_attachment=False,
        download_name=document.filename
    )

