#!/bin/bash

# Kill Ports Script for ideal-goggles project
# This script kills processes using common development ports

echo "🔍 Checking and killing processes on common ports..."

# Define the ports used by the application
PORTS=(
    3000    # Frontend development server (old)
    3333    # Frontend development server (current)
    5555    # Backend API server
    9999    # Playwright test report server
    8080    # Alternative web server
    8000    # Alternative API server
)

# Function to kill process on a specific port
kill_port() {
    local port=$1
    echo -n "Port $port: "

    # Find process using the port
    local pid=$(lsof -ti :$port 2>/dev/null)

    if [ -z "$pid" ]; then
        echo "✅ Available (no process found)"
    else
        # Get process name for information
        local process_name=$(ps -p $pid -o comm= 2>/dev/null)
        echo -n "Found process '$process_name' (PID: $pid) - killing... "

        # Kill the process
        kill -9 $pid 2>/dev/null

        if [ $? -eq 0 ]; then
            echo "✅ Killed"
        else
            echo "❌ Failed to kill (may require sudo)"
        fi
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Kill processes on all defined ports
for port in "${PORTS[@]}"; do
    kill_port $port
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Also kill any node processes that might be hanging
echo ""
echo "🔍 Checking for hanging node processes..."

# Find playwright test processes
playwright_pids=$(pgrep -f "playwright test" 2>/dev/null)
if [ ! -z "$playwright_pids" ]; then
    echo "Found Playwright test processes: $playwright_pids"
    echo "$playwright_pids" | xargs kill -9 2>/dev/null
    echo "✅ Killed Playwright test processes"
else
    echo "✅ No Playwright test processes found"
fi

# Find vite processes
vite_pids=$(pgrep -f "vite" 2>/dev/null)
if [ ! -z "$vite_pids" ]; then
    echo "Found Vite processes: $vite_pids"
    echo "$vite_pids" | xargs kill -9 2>/dev/null
    echo "✅ Killed Vite processes"
else
    echo "✅ No Vite processes found"
fi

# Find python backend processes
python_pids=$(pgrep -f "src.main" 2>/dev/null)
if [ ! -z "$python_pids" ]; then
    echo "Found Python backend processes: $python_pids"
    echo "$python_pids" | xargs kill -9 2>/dev/null
    echo "✅ Killed Python backend processes"
else
    echo "✅ No Python backend processes found"
fi

echo ""
echo "✨ Cleanup complete! All ports should now be available."
echo ""
echo "You can now run:"
echo "  • Frontend: pnpm run dev:frontend"
echo "  • Backend: cd backend && python -m src.main"
echo "  • Tests: cd tests && pnpm test"
