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

    # Kill any python process running on port 5555
    lsof -ti:5555 | xargs kill -9 2>/dev/null

    # Kill any node process running on port 3333
    lsof -ti:3333 | xargs kill -9 2>/dev/null

    exit 0
}

# Set trap to cleanup on script exit
trap cleanup EXIT INT TERM

# Check if ports are in use and kill them
echo -e "${YELLOW}Checking for processes on development ports...${NC}"
if lsof -Pi :5555 -sTCP:LISTEN -t >/dev/null ; then
    echo "Killing process on port 5555..."
    lsof -ti:5555 | xargs kill -9 2>/dev/null
    sleep 1
fi

if lsof -Pi :3333 -sTCP:LISTEN -t >/dev/null ; then
    echo "Killing process on port 3333..."
    lsof -ti:3333 | xargs kill -9 2>/dev/null
    sleep 1
fi

# Start all services using pnpm dev (which runs backend, frontend, and electron concurrently)
echo -e "${GREEN}Starting all services in development mode...${NC}"
echo -e "${YELLOW}Backend will run on port 5555${NC}"
echo -e "${YELLOW}Frontend will run on port 3333${NC}"
echo ""
pnpm run dev