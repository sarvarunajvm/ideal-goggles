#!/bin/bash

# Integration Test Runner for Photo Search Application
# Usage: ./run-tests.sh [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
TEST_SUITE="all"
HEADED=false
DEBUG=false
BROWSERS="chromium"
WORKERS=4

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --suite)
      TEST_SUITE="$2"
      shift 2
      ;;
    --headed)
      HEADED=true
      shift
      ;;
    --debug)
      DEBUG=true
      shift
      ;;
    --browsers)
      BROWSERS="$2"
      shift 2
      ;;
    --workers)
      WORKERS="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  --suite <name>     Run specific test suite (smoke|search|settings|people|workflows|all)"
      echo "  --headed           Run tests in headed mode"
      echo "  --debug            Run tests in debug mode"
      echo "  --browsers <list>  Browsers to test (chromium|firefox|webkit|all)"
      echo "  --workers <num>    Number of parallel workers"
      echo "  --help             Show this help message"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

echo -e "${GREEN}🚀 Photo Search Integration Tests${NC}"
echo "=================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    echo "Please install Node.js 18+ first"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm is not installed${NC}"
    exit 1
fi

# Navigate to tests directory
cd "$(dirname "$0")"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    npm install
fi

# Install Playwright browsers if needed
if [ ! -d "$HOME/.cache/ms-playwright" ]; then
    echo -e "${YELLOW}🌐 Installing Playwright browsers...${NC}"
    npx playwright install
fi

# Check if backend is running
echo -e "${YELLOW}🔍 Checking backend status...${NC}"
if curl -s http://localhost:5555/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is running${NC}"
else
    echo -e "${YELLOW}⚠️  Backend is not running. Starting it...${NC}"
    cd ../backend
    python -m src.main &
    BACKEND_PID=$!
    cd ../tests
    sleep 5
fi

# Check if frontend is running
echo -e "${YELLOW}🔍 Checking frontend status...${NC}"
if curl -s http://localhost:3333 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend is running${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend is not running. Starting it...${NC}"
    cd ../frontend
    pnpm run dev &
    FRONTEND_PID=$!
    cd ../tests
    sleep 5
fi

# Build test command
TEST_CMD="npx playwright test"

# Add test suite selection
case $TEST_SUITE in
  smoke)
    TEST_CMD="$TEST_CMD 01-smoke"
    ;;
  search)
    TEST_CMD="$TEST_CMD 02-search"
    ;;
  settings)
    TEST_CMD="$TEST_CMD 03-settings"
    ;;
  people)
    TEST_CMD="$TEST_CMD 04-people"
    ;;
  workflows)
    TEST_CMD="$TEST_CMD 05-workflows"
    ;;
  all)
    # Run all tests
    ;;
  *)
    echo -e "${RED}Unknown test suite: $TEST_SUITE${NC}"
    exit 1
    ;;
esac

# Add browser selection
if [ "$BROWSERS" = "all" ]; then
    # Use all configured browsers
    true
else
    TEST_CMD="$TEST_CMD --project=$BROWSERS"
fi

# Add headed mode
if [ "$HEADED" = true ]; then
    TEST_CMD="$TEST_CMD --headed"
fi

# Add debug mode
if [ "$DEBUG" = true ]; then
    TEST_CMD="$TEST_CMD --debug"
    WORKERS=1
fi

# Add workers
TEST_CMD="$TEST_CMD --workers=$WORKERS"

# Run tests
echo ""
echo -e "${GREEN}🧪 Running tests...${NC}"
echo "Command: $TEST_CMD"
echo ""

# Execute tests and capture exit code
set +e
$TEST_CMD
TEST_EXIT_CODE=$?
set -e

# Generate report if tests completed
if [ -d "playwright-report" ]; then
    echo ""
    echo -e "${YELLOW}📊 Test report generated${NC}"
    echo "Run 'pnpm run test:report' to view the HTML report"
fi

# Cleanup processes if we started them
if [ ! -z "$BACKEND_PID" ]; then
    echo -e "${YELLOW}Stopping backend...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
fi

if [ ! -z "$FRONTEND_PID" ]; then
    echo -e "${YELLOW}Stopping frontend...${NC}"
    kill $FRONTEND_PID 2>/dev/null || true
fi

# Exit with test exit code
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo ""
    echo -e "${RED}❌ Some tests failed${NC}"
fi

exit $TEST_EXIT_CODE