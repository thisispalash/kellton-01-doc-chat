#!/bin/bash

# Doc Chat - Start Script
# This script starts both backend and frontend servers

set -e  # Exit on error

echo "=========================================="
echo "  Doc Chat - Starting Application"
echo "=========================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo ""
    print_info "Shutting down servers..."
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        print_success "Backend stopped"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        print_success "Frontend stopped"
    fi
    
    echo ""
    print_info "Application shut down successfully"
    exit 0
}

# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

# Check if setup has been run
if [ ! -f "backend/.env" ] || [ ! -f "interface/.env.local" ]; then
    print_error "Setup not complete. Please run './setup.sh' first."
    exit 1
fi

# Check for package manager
if command -v pnpm &> /dev/null; then
    PKG_MANAGER="pnpm"
elif command -v npm &> /dev/null; then
    PKG_MANAGER="npm"
else
    print_error "Neither pnpm nor npm found. Please install one of them."
    exit 1
fi

# Create log directory
mkdir -p logs

# Start backend
echo "Starting backend server..."
cd backend
poetry run python run.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..
sleep 2  # Give backend time to start

# Check if backend started successfully
if kill -0 $BACKEND_PID 2>/dev/null; then
    print_success "Backend started on http://localhost:5001 (PID: $BACKEND_PID)"
else
    print_error "Backend failed to start. Check logs/backend.log for details."
    exit 1
fi

# Start frontend
echo "Starting frontend server..."
cd interface
$PKG_MANAGER dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
sleep 3  # Give frontend time to start

# Check if frontend started successfully
if kill -0 $FRONTEND_PID 2>/dev/null; then
    print_success "Frontend started on http://localhost:3000 (PID: $FRONTEND_PID)"
else
    print_error "Frontend failed to start. Check logs/frontend.log for details."
    cleanup
    exit 1
fi

echo ""
echo "=========================================="
echo "  Application Running!"
echo "=========================================="
echo ""
print_success "Backend:  http://localhost:5001"
print_success "Frontend: http://localhost:3000"
echo ""
print_info "Logs are being written to:"
echo "  - logs/backend.log"
echo "  - logs/frontend.log"
echo ""
print_warning "Press Ctrl+C to stop both servers"
echo ""

# Wait for user interrupt
wait

