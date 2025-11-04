#!/bin/bash

# Doc Chat - Setup Script
# This script sets up both backend and frontend for first-time use

set -e  # Exit on error

echo "=========================================="
echo "  Doc Chat - Initial Setup"
echo "=========================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check prerequisites
echo "Checking prerequisites..."
echo ""

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    print_success "Python found: $PYTHON_VERSION"
else
    print_error "Python 3 is not installed. Please install Python 3.13+ first."
    exit 1
fi

# Check Poetry
if command -v poetry &> /dev/null; then
    POETRY_VERSION=$(poetry --version | awk '{print $3}')
    print_success "Poetry found: $POETRY_VERSION"
else
    print_error "Poetry is not installed. Install it with: curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_success "Node.js found: $NODE_VERSION"
else
    print_error "Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Check pnpm (or npm)
if command -v pnpm &> /dev/null; then
    PNPM_VERSION=$(pnpm --version)
    print_success "pnpm found: $PNPM_VERSION"
    PKG_MANAGER="pnpm"
elif command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    print_warning "pnpm not found, using npm: $NPM_VERSION"
    PKG_MANAGER="npm"
else
    print_error "Neither pnpm nor npm found. Please install one of them."
    exit 1
fi

echo ""
echo "=========================================="
echo "  Setting up Backend"
echo "=========================================="
echo ""

cd backend

# Install backend dependencies
echo "Installing Python dependencies with Poetry..."
poetry install
print_success "Backend dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating backend .env file..."
    
    # Generate a random secret key
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
    
    cat > .env << EOF
# Flask Configuration
FLASK_SECRET_KEY=$SECRET_KEY
FLASK_DEBUG=True

# Database
DATABASE_PATH=instance/app.db

# File Storage
UPLOADS_PATH=uploads/

# ChromaDB Configuration
CHROMA_PATH=instance/chroma/
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# Session Configuration
SESSION_EXPIRY_HOURS=24

# CORS Configuration
CORS_ORIGINS=http://localhost:3000

# NOTE: LLM API keys are now stored per-user in the database (encrypted)
# Configure them in the Settings dialog after logging in
EOF
    
    print_success "Backend .env file created"
    print_warning "Configure your LLM API keys in the Settings dialog after logging in"
else
    print_warning "Backend .env file already exists, skipping creation"
fi

cd ..

echo ""
echo "=========================================="
echo "  Setting up Frontend"
echo "=========================================="
echo ""

cd interface

# Install frontend dependencies
echo "Installing frontend dependencies with $PKG_MANAGER..."
$PKG_MANAGER install
print_success "Frontend dependencies installed"

# Create .env.local file if it doesn't exist
if [ ! -f .env.local ]; then
    echo ""
    echo "Creating frontend .env.local file..."
    
    cat > .env.local << EOF
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:5001
EOF
    
    print_success "Frontend .env.local file created"
else
    print_warning "Frontend .env.local file already exists, skipping creation"
fi

cd ..

echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
print_success "All dependencies installed"
print_success "Configuration files created"
echo ""
echo "Next steps:"
echo "  1. Run './start.sh' to start the application"
echo "  2. Open http://localhost:3000 in your browser"
echo "  3. Create an account and configure your API keys in Settings"
echo ""
echo "To start manually:"
echo "  Backend:  cd backend && poetry run python run.py"
echo "  Frontend: cd interface && $PKG_MANAGER dev"
echo ""

