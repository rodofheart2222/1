#!/bin/bash

# MT5 Dashboard Startup Script (Shell Version)
# Simple version for quick startup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default configuration
BACKEND_PORT=${BACKEND_PORT:-80}
FRONTEND_PORT=${FRONTEND_PORT:-3000}
HOST=${HOST:-127.0.0.1}
MODE=${MODE:-dev}

# Print header
echo -e "${BLUE}
╔═══════════════════════════════════════════════════════════════╗
║                    MT5 Dashboard Startup                     ║
║              Commander-in-Chief Trading System               ║
╚═══════════════════════════════════════════════════════════════╝
${NC}"

# Function to log messages
log() {
    echo -e "${CYAN}[$(date +'%H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ❌ $1${NC}"
}

success() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] ✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] ⚠️ $1${NC}"
}

# Cleanup function
cleanup() {
    warning "Shutting down services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    success "All services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check dependencies
log "🔍 Checking dependencies..."

if ! command -v python3 &> /dev/null; then
    error "python3 is required but not installed"
    exit 1
fi
success "python3: $(python3 --version)"

if ! command -v node &> /dev/null; then
    error "node is required but not installed"
    exit 1
fi
success "node: $(node --version)"

if ! command -v npm &> /dev/null; then
    error "npm is required but not installed"
    exit 1
fi
success "npm: $(npm --version)"

# Set environment variables
log "🔧 Setting up environment..."
export ENVIRONMENT=$MODE
export MT5_API_PORT=$BACKEND_PORT
export MT5_HOST=$HOST
export DATABASE_PATH=data/mt5_dashboard.db
export PYTHONPATH=$(pwd)
export NODE_ENV=$MODE

# Initialize database
log "🗄️ Initializing database..."
python3 -c "
import sqlite3
import os
from pathlib import Path

# Ensure data directory exists
data_dir = Path('data')
data_dir.mkdir(exist_ok=True)

# Create database with schema
db_path = 'data/mt5_dashboard.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Apply main schema
schema_file = Path('backend/database/schema.sql')
if schema_file.exists():
    with open(schema_file, 'r') as f:
        cursor.executescript(f.read())

# Apply migrations
migrations_dir = Path('backend/database/migrations')
if migrations_dir.exists():
    migration_files = sorted(migrations_dir.glob('*.sql'))
    for migration_file in migration_files:
        with open(migration_file, 'r') as f:
            cursor.executescript(f.read())

conn.commit()
conn.close()
print('Database initialized successfully')
"

if [ $? -eq 0 ]; then
    success "Database initialization completed"
else
    error "Database initialization failed"
    exit 1
fi

# Install Python dependencies
log "📦 Installing Python dependencies..."
python3 -m pip install --break-system-packages fastapi uvicorn sqlalchemy python-multipart beautifulsoup4 requests pandas numpy &>/dev/null
if [ $? -eq 0 ]; then
    success "Python dependencies installed"
else
    warning "Some Python dependencies may have failed to install"
fi

# Install Node.js dependencies (if frontend directory exists)
if [ -d "frontend" ]; then
    log "📦 Installing Node.js dependencies..."
    cd frontend
    npm install --legacy-peer-deps --silent &>/dev/null
    if [ $? -eq 0 ]; then
        success "Node.js dependencies installed"
    else
        warning "Some Node.js dependencies may have failed to install"
    fi
    cd ..
fi

# Start backend
log "🚀 Starting backend server..."
cd backend
PORT=$BACKEND_PORT HOST=$HOST ENVIRONMENT=$MODE python3 main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Check if backend is running
if kill -0 $BACKEND_PID 2>/dev/null; then
    success "Backend server started on $HOST:$BACKEND_PORT"
else
    error "Backend server failed to start"
    exit 1
fi

# Start frontend (if directory exists)
if [ -d "frontend" ]; then
    log "🌐 Starting frontend server..."
    cd frontend
    
    if [ "$MODE" = "dev" ]; then
        PORT=$FRONTEND_PORT REACT_APP_API_URL=http://$HOST:$BACKEND_PORT BROWSER=none npm run dev &
    else
        log "📦 Building frontend for production..."
        npm run build &>/dev/null
        if [ $? -eq 0 ]; then
            npx serve -s build -l $FRONTEND_PORT &>/dev/null &
        else
            error "Frontend build failed"
            cleanup
            exit 1
        fi
    fi
    
    FRONTEND_PID=$!
    cd ..
    
    # Wait for frontend to start
    sleep 5
    
    # Check if frontend is running
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        success "Frontend server started on http://localhost:$FRONTEND_PORT"
    else
        error "Frontend server failed to start"
        cleanup
        exit 1
    fi
fi

# Print status
echo -e "\n${GREEN}🎉 MT5 Dashboard is running!${NC}\n"
echo -e "  🔧 Backend API: ${CYAN}http://$HOST:$BACKEND_PORT${NC}"
echo -e "  📊 API Docs: ${CYAN}http://$HOST:$BACKEND_PORT/docs${NC}"

if [ -d "frontend" ] && [ ! -z "$FRONTEND_PID" ]; then
    echo -e "  🌐 Frontend: ${CYAN}http://localhost:$FRONTEND_PORT${NC}"
fi

echo -e "\n${YELLOW}Press Ctrl+C to stop all services${NC}\n"

# Wait for processes
wait