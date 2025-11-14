"""Migration 001: Consolidate per-document collections to per-user collections.

This migration transforms the ChromaDB architecture from:
  OLD: doc_{user_id}_{doc_id} (one collection per document)
  NEW: user_{user_id}_default (one collection per user)

All document chunks are moved to the user's unified collection with doc_id in metadata.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from backend.db import get_db, Document, User
from backend.store import get_chroma_client, get_or_create_user_collection
from backend.store.legacy import get_collection, delete_collection
from backend.db.migrations import Migration


class ConsolidateCollectionsMigration(Migration):
    """Consolidate per-document ChromaDB collections into per-user collections."""
    
    version = 1
    name = "Consolidate Collections - Per-Document to Per-User"
    
    def __init__(self, verbose: bool = True):
        super().__init__(verbose)
        self.db = get_db()
        self.client = get_chroma_client()
    
    def up(self) -> bool:
        """Execute the migration: consolidate collections.
        
        For each user:
        1. Get all their documents
        2. Create user_{user_id}_default collection
        3. For each document:
           - Get chunks from doc_{user_id}_{doc_id} collection
           - Add to user's unified collection with doc_id metadata
           - Delete old collection
        4. Update database records
        
        Returns:
            True if successful, False otherwise
        """
        self.log("Starting collection consolidation migration")
        
        try:
            # Get all users
            users = self.db.query(User).all()
            self.log(f"Found {len(users)} user(s)")
            
            total_docs = 0
            total_chunks = 0
            migrated_docs = 0
            errors = []
            
            for user in users:
                user_id = user.id
                username = user.username
                
                self.log(f"\nProcessing user {user_id} ({username})")
                
                # Get all documents for this user
                documents = self.db.query(Document).filter_by(user_id=user_id).all()
                
                if not documents:
                    self.log(f"  No documents for user {user_id}, skipping")
                    continue
                
                self.log(f"  Found {len(documents)} document(s)")
                total_docs += len(documents)
                
                # Create/get user's unified collection
                user_collection = get_or_create_user_collection(user_id, 'default')
                new_collection_name = f"user_{user_id}_default"
                self.log(f"  Using collection: {new_collection_name}")
                
                # Process each document
                for doc in documents:
                    doc_id = doc.id
                    old_collection_name = doc.chroma_collection_id
                    
                    self.log(f"    Processing document {doc_id}: {doc.filename}")
                    self.log(f"      Old collection: {old_collection_name}")
                    
                    # Skip if already using new naming convention
                    if old_collection_name.startswith(f"user_{user_id}_"):
                        self.log(f"      Already using new naming convention, skipping")
                        continue
                    
                    try:
                        # Get old collection
                        old_collection = get_collection(old_collection_name)
                        
                        if old_collection is None:
                            self.log(f"      WARNING: Old collection not found, skipping", "WARNING")
                            errors.append(f"User {user_id}, Doc {doc_id}: Old collection not found")
                            continue
                        
                        # Get all chunks from old collection
                        old_data = old_collection.get(
                            include=['embeddings', 'documents', 'metadatas']
                        )
                        
                        if not old_data or not old_data['ids']:
                            self.log(f"      No chunks found in old collection")
                        else:
                            chunk_count = len(old_data['ids'])
                            self.log(f"      Found {chunk_count} chunk(s)")
                            total_chunks += chunk_count
                            
                            # Add chunks to new collection
                            user_collection.add(
                                ids=old_data['ids'],
                                embeddings=old_data['embeddings'],
                                documents=old_data['documents'],
                                metadatas=old_data['metadatas']
                            )
                            
                            self.log(f"      Copied {chunk_count} chunk(s) to new collection")
                        
                        # Update document record
                        doc.chroma_collection_id = new_collection_name
                        
                        # Delete old collection
                        delete_collection(old_collection_name)
                        self.log(f"      Deleted old collection")
                        
                        migrated_docs += 1
                        
                    except Exception as e:
                        self.log(f"      ERROR: Failed to migrate document {doc_id}: {e}", "ERROR")
                        errors.append(f"User {user_id}, Doc {doc_id}: {str(e)}")
                        continue
                
                # Commit changes for this user
                self.db.commit()
                self.log(f"  Committed changes for user {user_id}")
            
            # Summary
            self.log(f"\n{'='*60}")
            self.log("Migration Summary:")
            self.log(f"  Total users processed: {len(users)}")
            self.log(f"  Total documents: {total_docs}")
            self.log(f"  Successfully migrated: {migrated_docs}")
            self.log(f"  Total chunks moved: {total_chunks}")
            self.log(f"  Errors: {len(errors)}")
            
            if errors:
                self.log("\nErrors encountered:")
                for error in errors:
                    self.log(f"  - {error}", "ERROR")
            
            self.log(f"{'='*60}")
            
            return len(errors) == 0
        
        except Exception as e:
            self.log(f"FATAL ERROR: Migration failed: {e}", "ERROR")
            self.db.rollback()
            return False
    
    def down(self) -> bool:
        """Rollback the migration: split user collections back to per-document.
        
        WARNING: This is a complex rollback that recreates the old structure.
        
        Returns:
            True if successful, False otherwise
        """
        self.log("Starting rollback: splitting collections back to per-document")
        
        try:
            # Get all users
            users = self.db.query(User).all()
            self.log(f"Found {len(users)} user(s)")
            
            for user in users:
                user_id = user.id
                username = user.username
                
                self.log(f"\nProcessing user {user_id} ({username})")
                
                # Get all documents for this user
                documents = self.db.query(Document).filter_by(user_id=user_id).all()
                
                if not documents:
                    self.log(f"  No documents for user {user_id}, skipping")
                    continue
                
                self.log(f"  Found {len(documents)} document(s)")
                
                # Get user's unified collection
                user_collection_name = f"user_{user_id}_default"
                user_collection = get_collection(user_collection_name)
                
                if user_collection is None:
                    self.log(f"  WARNING: User collection not found, skipping", "WARNING")
                    continue
                
                # Process each document
                for doc in documents:
                    doc_id = doc.id
                    old_collection_name = f"doc_{user_id}_{doc_id}"
                    
                    self.log(f"    Processing document {doc_id}: {doc.filename}")
                    
                    try:
                        # Get chunks for this document from user collection
                        doc_data = user_collection.get(
                            where={"doc_id": str(doc_id)},
                            include=['embeddings', 'documents', 'metadatas']
                        )
                        
                        if not doc_data or not doc_data['ids']:
                            self.log(f"      No chunks found for document")
                            continue
                        
                        chunk_count = len(doc_data['ids'])
                        self.log(f"      Found {chunk_count} chunk(s)")
                        
                        # Create new per-document collection
                        new_collection = self.client.create_collection(
                            name=old_collection_name,
                            metadata={"hnsw:space": "cosine"}
                        )
                        
                        # Add chunks to new collection
                        new_collection.add(
                            ids=doc_data['ids'],
                            embeddings=doc_data['embeddings'],
                            documents=doc_data['documents'],
                            metadatas=doc_data['metadatas']
                        )
                        
                        self.log(f"      Created collection {old_collection_name} with {chunk_count} chunks")
                        
                        # Update document record
                        doc.chroma_collection_id = old_collection_name
                        
                        # Remove chunks from user collection
                        user_collection.delete(ids=doc_data['ids'])
                        
                    except Exception as e:
                        self.log(f"      ERROR: Failed to rollback document {doc_id}: {e}", "ERROR")
                        continue
                
                # Delete user collection if it's now empty
                remaining = user_collection.get()
                if not remaining or not remaining['ids']:
                    delete_collection(user_collection_name)
                    self.log(f"  Deleted empty user collection")
                
                # Commit changes for this user
                self.db.commit()
                self.log(f"  Committed changes for user {user_id}")
            
            self.log("\nRollback completed")
            return True
        
        except Exception as e:
            self.log(f"FATAL ERROR: Rollback failed: {e}", "ERROR")
            self.db.rollback()
            return False
    
    def dry_run(self) -> dict:
        """Preview what the migration would do.
        
        Returns:
            Dictionary with preview information
        """
        try:
            users = self.db.query(User).all()
            
            preview = {
                'total_users': len(users),
                'users_to_process': 0,
                'total_documents': 0,
                'documents_to_migrate': 0,
                'estimated_chunks': 0,
                'collections_to_create': [],
                'collections_to_delete': []
            }
            
            for user in users:
                user_id = user.id
                documents = self.db.query(Document).filter_by(user_id=user_id).all()
                
                if not documents:
                    continue
                
                preview['users_to_process'] += 1
                preview['total_documents'] += len(documents)
                
                new_collection_name = f"user_{user_id}_default"
                if new_collection_name not in preview['collections_to_create']:
                    preview['collections_to_create'].append(new_collection_name)
                
                for doc in documents:
                    old_collection_name = doc.chroma_collection_id
                    
                    # Skip if already migrated
                    if old_collection_name.startswith(f"user_{user_id}_"):
                        continue
                    
                    preview['documents_to_migrate'] += 1
                    
                    # Try to get chunk count
                    old_collection = get_collection(old_collection_name)
                    if old_collection:
                        old_data = old_collection.get()
                        if old_data and old_data['ids']:
                            preview['estimated_chunks'] += len(old_data['ids'])
                        
                        if old_collection_name not in preview['collections_to_delete']:
                            preview['collections_to_delete'].append(old_collection_name)
            
            return preview
        
        except Exception as e:
            return {
                'error': f"Failed to preview migration: {str(e)}"
            }


# Create instance for easy import
consolidate_collections_migration = ConsolidateCollectionsMigration()

