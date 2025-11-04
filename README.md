# Doc Chat 📄💬

A locally-hosted document chat application with RAG (Retrieval Augmented Generation) capabilities. Upload PDFs, chat with them using various LLM providers, and keep your data completely local.

## ✨ Features

- 🔐 **Password-First Authentication** - Unique UX with secure bcrypt hashing
- 📄 **PDF Upload & Processing** - Automatic text extraction and chunking
- 🧠 **Local Embeddings** - sentence-transformers running entirely on your machine
- 💾 **ChromaDB Vector Store** - Fast, local vector database for RAG
- 🤖 **Multi-LLM Support** - OpenAI, Anthropic, Google Gemini, and Grok
- 🔑 **Encrypted API Keys** - User-specific, encrypted storage in local database
- 💬 **Real-time Streaming** - WebSocket-based chat with streaming responses
- 📎 **Persistent Document Context** - Documents stay attached to conversations
- 📱 **Split View** - Resizable PDF viewer alongside chat
- 🎨 **Modern UI** - Built with Next.js, Tailwind CSS, and Radix UI

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- Node.js 18+
- pnpm (recommended) or npm
- Poetry

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd 01-doc-chat

# Make scripts executable
chmod +x setup.sh start.sh

# Run setup (installs dependencies and creates config files)
./setup.sh

# Start the application
./start.sh
```

The application will be available at:
- **Frontend:** http://localhost:3000
- **Backend:** http://localhost:5001

Press `Ctrl+C` to stop both servers.

## 📖 Usage

### First Time Setup

1. **Create Account:**
   - Open http://localhost:3000
   - Enter a password (min 8 characters)
   - Choose a username
   - You're logged in!

2. **Configure API Keys:**
   - Click the Settings (⚙️) button in the sidebar
   - Enter your API keys for the LLM providers you want to use
   - Keys are encrypted and stored securely

3. **Upload Documents:**
   - Click "Upload Document" in the sidebar
   - Select a PDF file
   - Wait for processing (first upload takes longer as the embedding model downloads)

4. **Start Chatting:**
   - Click a document to create a conversation with it attached
   - Or click "New Conversation" for a blank chat
   - Select your preferred model from the dropdown
   - Type and send messages!

### Advanced Features

- **Attach/Detach Documents:** Use the +/X buttons next to documents
- **View PDFs:** Click document badges in the chat header to open split view
- **Resize Panels:** Drag the handle between PDF viewer and chat
- **Switch Models:** Change model for each message using the dropdown
- **Manage Conversations:** Auto-cleanup of empty conversations, delete with trash icon

## 🏗️ Architecture

### Tech Stack

**Backend:**
- Flask + Flask-SocketIO
- SQLite + SQLAlchemy
- ChromaDB (local vector store)
- sentence-transformers (embeddings)
- bcrypt + Fernet (security)

**Frontend:**
- Next.js 16 (App Router)
- React + TypeScript
- Tailwind CSS + Radix UI
- Socket.IO client

### File Structure

```
01-doc-chat/
├── backend/          # Flask backend
├── interface/        # Next.js frontend
├── setup.sh          # Initial setup script
├── start.sh          # Start both servers
├── SETUP.md          # Detailed setup guide
└── PROJECT_SUMMARY.md # Complete implementation details
```

## 📚 Documentation

- [Setup Guide](SETUP.md) - Detailed installation and configuration
- [Project Summary](PROJECT_SUMMARY.md) - Complete implementation details
- [API Documentation](SETUP.md#api-endpoints) - REST and WebSocket API reference

## 🔧 Development

### Manual Start (without scripts)

**Backend:**
```bash
cd backend
poetry run python run.py
```

**Frontend:**
```bash
cd interface
pnpm dev
```

### Logs

When using `start.sh`, logs are written to:
- `logs/backend.log`
- `logs/frontend.log`

## 🛠️ Troubleshooting

### Backend Issues

- **Import Errors:** Run `poetry install` again
- **Database Errors:** Delete `backend/instance/app.db` and restart
- **ChromaDB Errors:** Delete `backend/instance/chroma/` and re-upload documents

### Frontend Issues

- **Connection Errors:** Ensure backend is running on port 5001
- **Build Errors:** Delete `node_modules` and `.next`, then run `pnpm install`

### Script Issues

- **Permission Denied:** Run `chmod +x setup.sh start.sh`
- **Port Already in Use:** Kill processes on ports 3000 and 5001

## 🔐 Security Notes

- All data is stored locally - no cloud services required
- API keys are encrypted using Fernet (derived from Flask SECRET_KEY)
- Passwords are hashed with bcrypt
- Sessions use cryptographically secure tokens
- CORS is configured for localhost only

## 📦 Dependencies

The setup script automatically installs all dependencies. Key packages:

**Backend:**
- flask, flask-socketio, flask-cors
- sqlalchemy, bcrypt, cryptography
- chromadb, sentence-transformers
- pypdf, openai, anthropic, google-generativeai

**Frontend:**
- next, react, react-dom
- socket.io-client
- @radix-ui/* (UI components)
- tailwindcss

## 🤝 Contributing

This is a local development tool. Feel free to fork and customize for your needs!

## 📝 License

See LICENSE file.

## 🙏 Credits

Built with Flask, Next.js, ChromaDB, and sentence-transformers.

---

**Note:** The first time you upload a document, the embedding model (~90MB) will download automatically. This is a one-time operation.
