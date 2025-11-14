# Backend - Document Chat Application

Flask-based backend for document chat with RAG (Retrieval-Augmented Generation) capabilities.

## Architecture Overview

### Directory Structure

```
backend/
├── src/
│   └── backend/
│       ├── __init__.py
│       ├── app.py                    # Flask app factory
│       ├── config.py                 # Configuration (env-based)
│       │
│       ├── api/                      # API routes/blueprints
│       │   ├── __init__.py
│       │   ├── auth.py               # Auth endpoints (login, logout, register)
│       │   ├── conversations.py      # Conversation management
│       │   ├── documents.py          # Document upload/management
│       │   ├── settings.py           # User settings & API keys
│       │   └── websocket.py          # WebSocket chat handlers
│       │
│       ├── auth/                     # Authentication logic
│       │   ├── __init__.py
│       │   ├── middleware.py         # Auth decorators/middleware
│       │   └── session.py            # Session management
│       │
│       ├── db/                       # Database layer
│       │   ├── __init__.py
│       │   ├── models.py             # SQLAlchemy models
│       │   └── migrations.py         # Migration framework
│       │
│       ├── storage/                  # File storage
│       │   ├── __init__.py
│       │   └── file_manager.py       # Save/retrieve files from disk
│       │
│       ├── store/                    # Vector store operations (ChromaDB)
│       │   ├── __init__.py
│       │   ├── chroma_client.py      # ChromaDB client & collections
│       │   ├── embeddings.py         # PDF processing & embeddings
│       │   └── search.py             # Vector similarity search
│       │
│       └── utils/                    # Shared utilities
│           ├── __init__.py
│           ├── encryption.py         # API key encryption
│           └── llm_providers.py      # LLM provider integrations
│
├── migrations/                       # Data migrations
│   ├── __init__.py
│   └── 001_consolidate_collections.py
│
├── tests/
│   ├── __init__.py
│   └── ...
│
├── uploads/                          # Uploaded files (gitignored)
├── chroma_data/                      # ChromaDB storage (gitignored)
├── instance/                         # SQLite DB files (gitignored)
├── run_migrations.py                 # Migration CLI tool
├── pyproject.toml
└── README.md
```

## ChromaDB Collection Structure

### Current Architecture (After Migration)

The application uses a **per-user collection strategy** where all documents for a user are stored in a unified ChromaDB collection:

#### Collection Naming

- **Documents**: `user_{user_id}_default`
  - Contains all document chunks for a user
  - Metadata includes `doc_id`, `page_number`, `chunk_index`
  
- **Conversations** (infrastructure ready, not active yet): `user_{user_id}_conversations`
  - Will contain message/conversation embeddings
  - For future "memory" feature - semantic search across past conversations

#### Metadata Structure

Each document chunk in the `user_{user_id}_default` collection has metadata:

```python
{
    'doc_id': '123',           # Document ID (as string)
    'page_number': 5,          # Page number in PDF
    'chunk_index': 2           # Chunk index within document
}
```

### Filtering by Document

To search specific documents (future folder/project feature):

```python
# Search single document
search_user_documents(user_id, query, doc_ids=[123])

# Search multiple documents (e.g., documents in a folder)
search_user_documents(user_id, query, doc_ids=[123, 456, 789])

# Search all documents (default)
search_user_documents(user_id, query)
```

Under the hood, this uses ChromaDB's `where` clause:

```python
# Single document
where={"doc_id": "123"}

# Multiple documents
where={"doc_id": {"$in": ["123", "456", "789"]}}
```

### Benefits of Per-User Collections

1. **Single Query**: Search all user documents in one vector search operation
2. **Efficient**: No need to query multiple collections and merge results
3. **Scalable**: Easy to add metadata filters for folders, projects, tags, etc.
4. **Automatic RAG**: Every message searches all documents automatically
5. **Future-Ready**: Infrastructure supports conversation memory

### Legacy Architecture (Before Migration)

Previously, each document had its own collection: `doc_{user_id}_{doc_id}`

This required:
- Creating a new collection for every document upload
- Searching multiple collections and merging results
- Deleting entire collections when documents were removed
- Manual document attachment to conversations

## Running Migrations

### Migration CLI Tool

The `run_migrations.py` script provides a CLI for managing migrations:

```bash
# Show migration status
python run_migrations.py --status

# Preview migration without executing (dry run)
python run_migrations.py --dry-run

# Run all pending migrations
python run_migrations.py

# Rollback the last migration
python run_migrations.py --rollback
```

### Migration 001: Consolidate Collections

This migration transforms the ChromaDB architecture from per-document to per-user collections.

**What it does:**
1. For each user, creates `user_{user_id}_default` collection
2. Copies all document chunks from old `doc_{user_id}_{doc_id}` collections
3. Preserves all metadata (doc_id, page_number, chunk_index)
4. Updates database records with new collection names
5. Deletes old per-document collections

**Safety:**
- Supports dry-run mode to preview changes
- Logs all operations with timestamps
- Can be rolled back if needed
- Preserves all data during migration

### Creating New Migrations

1. Create a new file in `backend/migrations/` (e.g., `002_your_migration.py`)
2. Inherit from `Migration` class:

```python
from backend.db.migrations import Migration

class YourMigration(Migration):
    version = 2
    name = "Description of your migration"
    
    def up(self) -> bool:
        """Execute the migration."""
        # Your migration code
        return True
    
    def down(self) -> bool:
        """Rollback the migration."""
        # Your rollback code
        return True
    
    def dry_run(self) -> dict:
        """Preview the migration."""
        return {
            'summary': 'What this would do...'
        }
```

3. Add to `migrations/__init__.py`:

```python
ALL_MIGRATIONS = [
    consolidate_collections_migration,
    your_migration,  # Add here
]
```

## RAG Pipeline

### Document Upload Flow

1. User uploads PDF via `/api/documents/upload`
2. PDF is saved to disk (`uploads/{user_id}/{doc_id}/`)
3. PDF is processed into chunks (text extraction)
4. Chunks are embedded using sentence-transformers
5. Embeddings are stored in `user_{user_id}_default` collection
6. Document metadata saved to SQLite database

### Chat/Search Flow

1. User sends message via WebSocket
2. Message is embedded using same model
3. Vector search performed on `user_{user_id}_default` collection
4. Top 10 relevant chunks retrieved
5. Chunks are formatted as context for LLM
6. LLM generates response with context
7. Response streamed back to user

### Automatic RAG

Every chat message automatically searches all user documents. No need to manually "attach" documents to conversations.

To search specific documents in the future (e.g., folder feature):

```python
# In websocket.py
attached_doc_ids = [1, 2, 3]  # Documents in folder
search_results = search_user_documents(
    user_id,
    user_message,
    doc_ids=attached_doc_ids  # Filter to specific documents
)
```

## Future Enhancements

### Conversation Memory

The infrastructure is ready for semantic conversation search:

1. Message embeddings stored in `user_{user_id}_conversations`
2. Metadata includes `message_id`, `conversation_id`, `type`
3. Can search past conversations for context
4. Enable "memory" feature - recall relevant past discussions

Example future implementation:

```python
# Search past conversations
conversation_results = collection.query(
    query_embeddings=[query_embedding],
    where={"type": "user_message"},
    n_results=5
)

# Include relevant past conversations in context
```

### Folders/Projects

Organize documents using metadata filtering:

```python
# Add folder_id to metadata during upload
metadata = {
    'doc_id': str(doc_id),
    'folder_id': '42',
    'page_number': page_num,
    'chunk_index': chunk_idx
}

# Search documents in a folder
where={"folder_id": "42"}

# Search documents with tags
where={"tags": {"$contains": "research"}}
```

## Migrating from Old Installation

If you have an existing installation with the old per-document collection architecture, you need to run the migration:

```bash
cd backend

# Preview what will happen (safe, read-only)
python run_migrations.py --dry-run

# Check current migration status
python run_migrations.py --status

# Run the migration
python run_migrations.py

# If something goes wrong, rollback
python run_migrations.py --rollback
```

**What this does:**
- Consolidates all per-document collections into per-user collections
- Preserves all document data and metadata
- Updates database records with new collection names
- Cleans up old collections

**Note:** New installations automatically use the new architecture and don't need migration.

## Development

### Setup

```bash
cd backend
poetry install
poetry shell
```

### Environment Variables

Create `.env` file:

```
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///instance/app.db
CHROMA_PATH=./chroma_data
```

### Running

```bash
# Development server
python run.py

# Production (with gunicorn)
gunicorn -k eventlet -w 1 -b 0.0.0.0:5000 "backend.app:create_app()"
```

## Testing

```bash
# Run tests
poetry run pytest

# With coverage
poetry run pytest --cov=backend
```