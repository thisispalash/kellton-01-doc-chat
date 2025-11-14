# RAG Collection Restructure Plan

**Created**: November 13, 2025  
**Completed**: November 14, 2025  
**Status**: Completed

## Overview
Migrate from per-document ChromaDB collections to per-user collections to enable:
- All user documents searchable in one query
- Future folder/project organization via metadata filtering
- Conversation memory infrastructure (setup only, search implemented later)

## Current Architecture
- Each document upload creates `doc_{user_id}_{doc_id}` collection
- Documents must be manually attached to conversations
- RAG only searches attached documents

## Target Architecture
- **`user_{user_id}_default`**: All document chunks with `doc_id`, `page_number`, `chunk_index` metadata
- **`user_{user_id}_conversations`**: Message/conversation embeddings with `message_id`, `conversation_id`, `type` metadata (infrastructure only)
- Automatic search across all user documents
- Metadata filtering ready for future features (folders, projects)

## Implementation Steps

### 1. Update ChromaDB Client
**File**: `backend/src/backend/store/chroma_client.py`
- Add `get_or_create_user_collection(user_id, collection_type)` function
  - `collection_type` can be "default" or "conversations"
  - Returns `user_{user_id}_{collection_type}` collection
- Add `add_documents_to_user_collection(user_id, chunks, embeddings, doc_id)` 
  - Gets/creates user's default collection
  - Adds chunks with proper metadata
- Add `remove_document_from_collection(user_id, doc_id)` for deletion
  - Removes all chunks where `doc_id` matches
- Keep existing functions for backward compatibility during migration

### 2. Update Database Models
**File**: `backend/src/backend/db/models.py`
- `chroma_collection_id` field remains but stores `user_{user_id}_default` for all documents
- This allows tracking which collection strategy is used
- Consider adding `collection_type` field for future expansion (optional)

### 3. Update Document Upload API
**File**: `backend/src/backend/api/documents.py`
- Change collection naming from `doc_{user_id}_{doc_id}` to `user_{user_id}_default`
- Use new `add_documents_to_user_collection()` function
- All documents for a user go to same collection with `doc_id` in metadata

### 4. Update Document Deletion
**File**: `backend/src/backend/api/documents.py`
- Instead of deleting entire collection, delete chunks by `doc_id` filter
- Use new `remove_document_from_collection()` function

### 5. Update Search Logic
**File**: `backend/src/backend/store/search.py`
- Add `search_user_documents(user_id, query_text, doc_ids=None, n_results=10)`
  - Searches `user_{user_id}_default` collection
  - If `doc_ids` provided, filter with `where={"doc_id": {"$in": doc_ids}}`
  - Otherwise search all user documents

### 6. Update WebSocket Handler
**File**: `backend/src/backend/api/websocket.py`
- Remove attached document filtering logic
- Call `search_user_documents(user_id, query_text)` directly
- Automatic RAG on every message across all user documents

### 7. Conversation Embeddings Infrastructure (Setup Only)
**File**: `backend/src/backend/store/chroma_client.py`
- Add `add_message_to_conversation_collection(user_id, message_id, conversation_id, text, embedding)`
  - Stores message embedding in `user_{user_id}_conversations`
  - Metadata: `message_id`, `conversation_id`, `type="user_message"` or `"assistant_message"`
- Add placeholder in websocket handler to call this (commented out or feature-flagged)
- Document intended use for future memory/semantic conversation search

### 8. Create Migration Framework
**File**: `backend/src/backend/db/migrations.py` (new file)
- Create base `Migration` class with:
  - `name`, `version`, `up()`, `down()`, `dry_run()`
  - Progress logging
- Create `MigrationRunner` class:
  - Track completed migrations in DB or file
  - Run pending migrations
  - Support rollback

### 9. Create Collection Migration Script
**File**: `backend/migrations/001_consolidate_collections.py` (new file)
- Implement specific migration:
  1. Query all documents grouped by user
  2. For each user:
     - Create `user_{user_id}_default` collection
     - For each document:
       - Get chunks from old `doc_{user_id}_{doc_id}` collection
       - Add to new collection with `doc_id` in metadata
       - Update document record `chroma_collection_id`
     - Delete old collections
  3. Log progress and any errors
- Support dry-run mode to preview changes

### 10. Create Migration Runner Script
**File**: `backend/run_migrations.py` (new file)
- CLI tool to run migrations:
  - `python run_migrations.py --dry-run` - preview
  - `python run_migrations.py` - execute
  - `python run_migrations.py --rollback` - undo last
- Uses migration framework

### 11. Update Documentation
**Files**: `backend/README.md`, comments in code
- Document new collection structure
- Explain metadata filtering approach
- Add migration instructions
- Document conversation collection for future use

## Testing Considerations
- Test document upload to new collection structure
- Test document deletion (chunks removed, not collection)
- Test search across multiple user documents
- Test migration script with sample data
- Verify old per-document collections are cleaned up

## Future Enhancements Enabled
- Folder/project organization via `where={"doc_id": {"$in": [...]}}` filtering
- Semantic conversation search using `user_{user_id}_conversations`
- Memory feature by searching past relevant conversations
- Cross-document insights and relationships

## Implementation Status

- [x] Update ChromaDB Client - Add user-based collection functions
- [x] Update Document Upload API - Modify to use new collection structure
- [x] Update Document Deletion - Change to filter-based removal
- [x] Update Search Logic - Add search_user_documents function
- [x] Update WebSocket Handler - Enable automatic search across all documents
- [x] Add Conversation Infrastructure - Setup conversation collection (infrastructure only)
- [x] Create Migration Framework - Build reusable migration system
- [x] Create Collection Migration - Implement specific consolidation migration
- [x] Create Migration CLI - Build CLI tool for executing migrations
- [x] Update Documentation - Document new architecture and migration process

## Post-Implementation: Legacy Code Cleanup

### Strategy

Since backwards compatibility is not required, we can aggressively remove all legacy code from the main codebase. For migration-only utilities, we'll use separation of concerns by creating a dedicated `legacy.py` module.

This approach is preferred over keeping legacy functions in the main codebase because it prevents accidental use of old patterns, makes the API crystal clear, and allows easy removal of migration utilities in the future.

#### Step 1: Create Legacy Module for Migrations

**New File: `backend/src/backend/store/legacy.py`**

Contains utilities needed ONLY by migration scripts:
- `get_collection()` - Get collection by name (for reading old collections)
- `delete_collection()` - Delete collection by name (for cleanup)
- Clearly documented as "Migration utilities only - DO NOT use in application code"

#### Step 2: Remove ALL Legacy Functions from Main Files

**In `backend/src/backend/store/chroma_client.py` - Remove:**
- `create_collection()` - Old per-document architecture
- `add_documents_to_collection()` - Replaced by `add_documents_to_user_collection()`
- `get_collection()` - Move to `legacy.py`
- `delete_collection()` - Move to `legacy.py`
- `collection_exists()` - Not needed, remove entirely

**Keep ONLY:**
- `get_chroma_client()` - Core utility
- `get_or_create_user_collection()` - New architecture
- `add_documents_to_user_collection()` - New architecture
- `remove_document_from_collection()` - New architecture
- `add_message_to_conversation_collection()` - Future feature

**In `backend/src/backend/store/search.py` - Remove:**
- `search_documents()` - Single collection search (old)
- `search_multiple_documents()` - Multi-collection search (old)

**Keep ONLY:**
- `search_user_documents()` - New architecture
- `get_context_from_results()` - Still needed

#### Step 3: Update Imports

**In `backend/src/backend/store/__init__.py`:**
Remove all legacy function exports, keep only:
```python
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
```

**In `backend/src/backend/api/documents.py`:**
Remove unused imports:
- `create_collection`
- `add_documents_to_collection`
- `delete_collection`

**In `backend/src/backend/api/websocket.py`:**
Remove unused import:
- `search_multiple_documents`

#### Step 4: Update Migration Script

**In `backend/migrations/001_consolidate_collections.py`:**
Change imports to use legacy module:
```python
from backend.store.legacy import get_collection, delete_collection
```

### Files to Create/Modify

#### Create:
1. `backend/src/backend/store/legacy.py` - Migration utilities only

#### Modify:
1. `backend/src/backend/store/chroma_client.py` - Remove 5 functions (move 2, delete 3)
2. `backend/src/backend/store/search.py` - Remove 2 functions
3. `backend/src/backend/store/__init__.py` - Clean exports (remove 7, keep 7)
4. `backend/src/backend/api/documents.py` - Clean imports
5. `backend/src/backend/api/websocket.py` - Clean imports
6. `backend/migrations/001_consolidate_collections.py` - Update imports

### Benefits

1. **Crystal clear API**: Only new architecture functions visible
2. **No confusion**: Can't accidentally use old functions
3. **Smaller codebase**: ~100 lines removed
4. **Better documentation**: Main files show only current patterns
5. **Easier onboarding**: New developers see only one way to do things
6. **Separation of concerns**: Migration code clearly separated
7. **Future-proof**: Easy to remove legacy.py when migrations are ancient

### Legacy Module Structure

```python
# backend/src/backend/store/legacy.py
"""
Legacy utilities for migration scripts only.

WARNING: DO NOT use these functions in application code.
These exist solely to support migration scripts that need to
interact with the old per-document collection architecture.

Use the functions in chroma_client.py for all application code.
"""

def get_collection(collection_name):
    """Get collection by name (for migrations only)."""
    ...

def delete_collection(collection_name):
    """Delete collection by name (for migrations only)."""
    ...
```

