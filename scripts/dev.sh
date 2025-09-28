#!/bin/bash

# Start backend and frontend for development

echo "Starting Photo Search development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down development environment...${NC}"

    # Kill backend if running
    if [ ! -z "$BACKEND_PID" ]; then
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null
    fi

    # Kill any python process running on port 5555
    lsof -ti:5555 | xargs kill -9 2>/dev/null

    exit 0
}

# Set trap to cleanup on script exit
trap cleanup EXIT INT TERM

# Check if backend is already running on port 5555
if lsof -Pi :5555 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}Backend already running on port 5555${NC}"
else
    # Start backend
    echo -e "${GREEN}Starting backend on port 5555...${NC}"
    cd backend
    python3 -m src.main &
    BACKEND_PID=$!
    cd ..

    # Wait for backend to be ready
    echo "Waiting for backend to start..."
    for i in {1..20}; do
        if curl -s http://127.0.0.1:5555/ > /dev/null; then
            echo -e "${GREEN}Backend is ready!${NC}"
            break
        fi
        sleep 1
    done
fi

# Start frontend/electron in dev mode
echo -e "${GREEN}Starting Electron app in development mode...${NC}"
pnpm run dev

# Script will stay running until interrupted
wait