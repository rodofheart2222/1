#!/bin/bash

# MT5 Dashboard Quick Start Script
# ================================

echo "MT5 Dashboard Quick Start"
echo "========================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to script directory
cd "$(dirname "$0")"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python
echo -e "${YELLOW}Checking Python...${NC}"
if command_exists python3; then
    echo -e "${GREEN}✓ Python3 found: $(python3 --version)${NC}"
else
    echo -e "${RED}✗ Python3 not found! Please install Python 3.8+${NC}"
    exit 1
fi

# Check Node.js (optional for backend-only mode)
if [ "$1" != "--backend-only" ]; then
    echo -e "${YELLOW}Checking Node.js...${NC}"
    if command_exists node; then
        echo -e "${GREEN}✓ Node.js found: $(node --version)${NC}"
    else
        echo -e "${RED}✗ Node.js not found! Install it or use --backend-only${NC}"
        exit 1
    fi
fi

# Install Python dependencies
echo -e "\n${YELLOW}Installing Python dependencies...${NC}"
if [ -f "backend/requirements.txt" ]; then
    # Try different pip installation methods
    if pip3 install --user -r backend/requirements.txt 2>/dev/null; then
        echo -e "${GREEN}✓ Python dependencies installed${NC}"
    elif pip3 install --break-system-packages -r backend/requirements.txt 2>/dev/null; then
        echo -e "${GREEN}✓ Python dependencies installed${NC}"
    else
        echo -e "${YELLOW}⚠ Some Python dependencies may be missing${NC}"
        # Install essential packages individually
        for package in fastapi uvicorn websockets sqlalchemy pandas numpy requests python-dotenv pydantic aiofiles; do
            pip3 install --user $package 2>/dev/null || pip3 install --break-system-packages $package 2>/dev/null
        done
    fi
else
    echo -e "${RED}✗ backend/requirements.txt not found!${NC}"
fi

# Install Node dependencies (if not backend-only)
if [ "$1" != "--backend-only" ] && [ -d "frontend" ]; then
    echo -e "\n${YELLOW}Installing Node.js dependencies...${NC}"
    cd frontend
    if npm install; then
        echo -e "${GREEN}✓ Node.js dependencies installed${NC}"
    else
        echo -e "${YELLOW}⚠ Some Node.js dependencies may have failed${NC}"
    fi
    cd ..
fi

# Create data directory
mkdir -p data

# Setup database
echo -e "\n${YELLOW}Setting up database...${NC}"
for script in fix_database_schema.py populate_ea_database.py setup_mt5_communication.py; do
    if [ -f "$script" ]; then
        echo "Running $script..."
        python3 "$script" 2>/dev/null || echo "  ⚠ $script had warnings"
    fi
done
echo -e "${GREEN}✓ Database setup complete${NC}"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    echo -e "${GREEN}✓ All services stopped${NC}"
    exit 0
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Start backend
echo -e "\n${YELLOW}Starting backend server...${NC}"
if [ -f "backend/main.py" ]; then
    python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    sleep 3
    
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${GREEN}✓ Backend server started on http://localhost:8000${NC}"
    else
        echo -e "${RED}✗ Backend server failed to start${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ backend/main.py not found!${NC}"
    exit 1
fi

# Start frontend (if not backend-only)
if [ "$1" != "--backend-only" ] && [ -d "frontend" ]; then
    echo -e "\n${YELLOW}Starting frontend server...${NC}"
    
    # Create frontend .env file
    cat > frontend/.env << EOF
GENERATE_SOURCEMAP=false
DISABLE_ESLINT_PLUGIN=true
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8001
PORT=3000
EOF
    
    cd frontend
    npm start &
    FRONTEND_PID=$!
    cd ..
    
    sleep 5
    
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${GREEN}✓ Frontend server started on http://localhost:3000${NC}"
    else
        echo -e "${YELLOW}⚠ Frontend may take longer to start${NC}"
    fi
fi

echo -e "\n${GREEN}✓ All services started successfully!${NC}"
echo -e "${YELLOW}Access the dashboard at: http://localhost:3000${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}\n"

# Keep script running
while true; do
    sleep 1
    
    # Check if backend is still running
    if [ ! -z "$BACKEND_PID" ] && ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}Backend server stopped unexpectedly${NC}"
        cleanup
    fi
    
    # Check if frontend is still running (if started)
    if [ ! -z "$FRONTEND_PID" ] && ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${YELLOW}Frontend server stopped${NC}"
        # Frontend stopping is less critical
    fi
done