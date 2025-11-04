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
│       │   ├── documents.py          # File upload endpoints
│       │   └── search.py             # Search/query endpoints
│       │
│       ├── auth/                     # Authentication logic
│       │   ├── __init__.py
│       │   ├── models.py             # User model
│       │   ├── session.py            # Session management
│       │   └── middleware.py         # Auth decorators/middleware
│       │
│       ├── storage/                  # File storage
│       │   ├── __init__.py
│       │   └── file_manager.py       # Save/retrieve files from disk
│       │
│       ├── vector/                   # Vector DB operations
│       │   ├── __init__.py
│       │   ├── embeddings.py         # PDF -> embeddings conversion
│       │   ├── pinecone_client.py    # Pinecone operations
│       │   └── search.py             # Cosine similarity search
│       │
│       ├── db/                       # SQLite database
│       │   ├── __init__.py
│       │   ├── models.py             # SQLAlchemy models (sessions, metadata)
│       │   └── connection.py         # DB connection/initialization
│       │
│       └── utils/                    # Shared utilities
│           ├── __init__.py
│           ├── pdf_processor.py      # PDF extraction/processing
│           └── validators.py         # Input validation
│
├── tests/
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_documents.py
│   ├── test_search.py
│   └── fixtures/
│
├── uploads/                          # Uploaded files (add to .gitignore)
├── instance/                         # SQLite DB files (add to .gitignore)
├── .env.example
├── pyproject.toml
└── README.md