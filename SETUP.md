# Doc Chat Setup Guide

This guide will help you set up and run the Doc Chat application locally.

## Quick Start (Recommended)

For first-time setup and running:

```bash
# 1. Clone the repository
git clone <repository-url>
cd 01-doc-chat

# 2. Make scripts executable (if needed)
chmod +x setup.sh start.sh

# 3. Run setup (installs dependencies and creates config files)
./setup.sh

# 4. Start the application
./start.sh
```

That's it! The application will be available at http://localhost:3000

Press `Ctrl+C` to stop both servers.

## Prerequisites

- Python 3.13+
- Node.js 18+
- pnpm (or npm)
- Poetry (Python dependency manager)

## Manual Setup (Alternative)

If you prefer to set up manually or the scripts don't work on your system:

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Create a `.env` file (copy from example if needed):
```bash
# Create .env file with your API keys
cat > .env << EOF
FLASK_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
FLASK_DEBUG=True

# Database
DATABASE_PATH=instance/app.db

# File Storage
UPLOADS_PATH=uploads/

# ChromaDB
CHROMA_PATH=instance/chroma/
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# LLM API Keys - Add your keys here
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GOOGLE_API_KEY=your-google-api-key
GROK_API_KEY=your-grok-api-key

# Session
SESSION_EXPIRY_HOURS=24

# CORS
CORS_ORIGINS=http://localhost:3000
EOF
```

4. Run the backend:
```bash
poetry run python run.py
```

The backend will start on `http://localhost:5001`

### Frontend Setup

1. Navigate to the interface directory:
```bash
cd interface
```

2. Install dependencies:
```bash
pnpm install
```

3. Create a `.env.local` file:
```bash
echo "NEXT_PUBLIC_API_URL=http://localhost:5001" > .env.local
```

4. Run the development server:
```bash
pnpm dev
```

The frontend will start on `http://localhost:3000`

## Usage

1. Open your browser and navigate to `http://localhost:3000`

2. **First Time Login:**
   - Enter a password (min 8 characters)
   - Since it's new, you'll be prompted to choose a username
   - This creates your account

3. **Subsequent Logins:**
   - Enter your password
   - The system recognizes it and prompts for your username
   - Enter your username to login

4. **Configure API Keys:**
   - Click the "Settings" button (gear icon) in the sidebar
   - Enter your API keys for the LLM providers you want to use:
     - OpenAI
     - Anthropic (Claude)
     - Google (Gemini)
     - Grok (xAI)
   - Keys are encrypted and stored securely in the database
   - You can update or delete keys at any time

5. **Upload Documents:**
   - Click "Upload Document" in the sidebar
   - Select a PDF file
   - Wait for processing (embedding generation)

6. **Start Chatting:**
   - Click "New Conversation" for a blank chat
   - OR click any document to start a conversation with that document attached
   - The document opens in a resizable split view (PDF on left, chat on right)
   - Choose your preferred LLM model from the dropdown
   - Type your message and send

7. **Working with Documents:**
   - **Attach/Detach:** Use the +/X buttons next to documents in the sidebar
   - **View Attached:** Click document badges in the chat header to view PDFs
   - **Split View:** Resize the panels by dragging the handle between them
   - **Close Viewer:** Click the X button in the document viewer header
   - **Persistent Context:** Documents stay attached to conversations across sessions

8. **Managing Conversations:**
   - Switch between conversations using the sidebar
   - Empty conversations (no messages) are automatically cleaned up
   - Delete conversations with the trash icon

## Features

### Backend
- **Authentication:** Password-first flow with bcrypt hashing
- **File Storage:** Local PDF storage with metadata
- **Vector Database:** ChromaDB for local embeddings
- **RAG:** Cosine similarity search on conversation-attached documents
- **LLM Integration:** OpenAI, Anthropic, Google Gemini, and Grok support
- **API Key Management:** User-specific encrypted API keys stored in database
- **Real-time:** WebSocket streaming responses
- **Database:** SQLite for conversations, messages, metadata, and API keys
- **PDF Serving:** Authenticated endpoint for secure PDF viewing

### Frontend
- **Modern UI:** Next.js 16 with Tailwind CSS and Radix UI
- **Real-time Chat:** Socket.IO client with streaming
- **Document Management:** Upload, attach, detach, view, and delete PDFs
- **Split View:** Resizable PDF viewer alongside chat interface
- **Conversation History:** Browse and continue past conversations
- **Document Context:** Persistent document attachments per conversation
- **Model Selection:** Switch between models per message
- **Settings Dialog:** Manage API keys for all LLM providers
- **Smart Cleanup:** Auto-delete empty conversations
- **Responsive Design:** Works on desktop and mobile

## Project Structure

### Backend (`/backend`)
```
backend/
├── src/backend/
│   ├── api/           # REST API routes and WebSocket handlers
│   ├── auth/          # Authentication logic
│   ├── db/            # SQLAlchemy models and database
│   ├── storage/       # File management
│   ├── store/         # ChromaDB and embeddings
│   ├── utils/         # LLM providers
│   ├── app.py         # Flask app factory
│   └── config.py      # Configuration
├── instance/          # SQLite DB and ChromaDB data
├── uploads/           # Uploaded PDF files
└── run.py            # Entry point
```

### Frontend (`/interface`)
```
interface/
├── src/
│   ├── app/           # Next.js app router pages
│   ├── components/    # React components
│   ├── context/       # Context providers
│   └── util/          # API client and utilities
└── public/            # Static assets
```

## API Endpoints

### Authentication
- `POST /api/auth/check-password` - Check if password exists
- `POST /api/auth/login` - Login with username/password
- `POST /api/auth/register` - Register new user
- `POST /api/auth/logout` - Logout current user
- `GET /api/auth/me` - Get current user info

### Conversations
- `GET /api/conversations` - List all conversations
- `POST /api/conversations` - Create new conversation
- `GET /api/conversations/:id` - Get conversation with messages and attached documents
- `PUT /api/conversations/:id` - Update conversation title
- `DELETE /api/conversations/:id` - Delete conversation
- `POST /api/conversations/:id/documents` - Attach document to conversation
- `DELETE /api/conversations/:id/documents/:doc_id` - Detach document from conversation

### Documents
- `POST /api/documents/upload` - Upload and process PDF
- `GET /api/documents` - List all documents
- `GET /api/documents/:id` - Get document details
- `GET /api/documents/:id/view` - Serve PDF file (authenticated)
- `DELETE /api/documents/:id` - Delete document

### Settings
- `GET /api/settings/api-keys` - List user's API keys (without keys themselves)
- `POST /api/settings/api-keys` - Save/update API key for a provider
- `DELETE /api/settings/api-keys/:provider` - Delete API key for a provider

### WebSocket Events
- `connect` - Authenticate and connect
- `disconnect` - Clean up connection
- `chat_message` - Send message with RAG context
- `chat_response_start` - Response streaming started
- `chat_response_chunk` - Response text chunk
- `chat_response_end` - Response complete

## Troubleshooting

### Backend Issues

1. **Import Errors:**
   - Make sure you're in the poetry environment
   - Run `poetry install` again

2. **Database Errors:**
   - Delete `instance/app.db` and restart to recreate

3. **ChromaDB Errors:**
   - Delete `instance/chroma/` and restart to recreate
   - Re-upload documents

4. **API Key Errors:**
   - API keys are now stored per-user in the database
   - Configure them in the Settings dialog in the UI
   - Backend `.env` API keys are no longer used (optional fallback only)

### Frontend Issues

1. **Connection Errors:**
   - Ensure backend is running on port 5001
   - Check `.env.local` has correct API URL

2. **WebSocket Issues:**
   - Check browser console for errors
   - Verify CORS settings in backend

3. **Build Errors:**
   - Delete `node_modules` and `.next`
   - Run `pnpm install` and try again

## Development Tips

- The embedding model downloads automatically on first use (~90MB)
- First PDF upload takes longer (model initialization)
- WebSocket connection auto-reconnects on disconnect
- Conversation titles default to "New Conversation" or "Chat with [filename]"
- Documents persist with conversations - they stay attached across sessions
- Empty conversations are automatically cleaned up when switching
- Click document badges in chat to open split view
- API keys are encrypted using Fernet (from Flask SECRET_KEY)

## License

See LICENSE file in the project root.

