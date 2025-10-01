#!/bin/bash

# Script to run tests with coverage locally and generate reports

set -e

echo "🧪 Running Tests with Coverage Reports"
echo "======================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create coverage directory
mkdir -p coverage-reports

# Backend Tests
echo -e "\n${YELLOW}📦 Running Backend Tests...${NC}"
cd backend
if command -v pytest &> /dev/null; then
    pytest --cov=src --cov-report=html:../coverage-reports/backend --cov-report=term --cov-report=xml:../coverage-reports/backend-coverage.xml -v
    echo -e "${GREEN}✅ Backend tests completed${NC}"
else
    echo -e "${RED}❌ pytest not found. Run 'make backend-install' first${NC}"
fi
cd ..

# Frontend Tests
echo -e "\n${YELLOW}⚛️ Running Frontend Tests...${NC}"
cd frontend
if command -v pnpm &> /dev/null; then
    pnpm test -- --coverage --coverageDirectory=../coverage-reports/frontend --coverageReporters=html --coverageReporters=lcov --coverageReporters=text
    echo -e "${GREEN}✅ Frontend tests completed${NC}"
else
    echo -e "${RED}❌ pnpm not found. Install pnpm first${NC}"
fi
cd ..

# E2E Tests (optional)
if [ "$1" == "--with-e2e" ]; then
    echo -e "\n${YELLOW}🎭 Running E2E Tests...${NC}"
    cd tests
    if command -v npx &> /dev/null; then
        npx playwright test --reporter=html:../coverage-reports/e2e
        echo -e "${GREEN}✅ E2E tests completed${NC}"
    else
        echo -e "${RED}❌ npx not found${NC}"
    fi
    cd ..
fi

# Generate combined HTML report
echo -e "\n${YELLOW}📊 Generating Combined Report...${NC}"

cat > coverage-reports/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ideal Goggles - Local Coverage Reports</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: white; text-align: center; margin-bottom: 2rem; font-size: 2.5rem; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
        }
        .card {
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .card:hover { transform: translateY(-2px); }
        .card h2 {
            color: #333;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .card p { color: #666; margin-bottom: 1rem; line-height: 1.5; }
        .btn {
            display: inline-block;
            padding: 0.5rem 1rem;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            transition: opacity 0.2s;
        }
        .btn:hover { opacity: 0.9; }
        .timestamp {
            text-align: center;
            color: white;
            margin-top: 2rem;
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🥽 Ideal Goggles - Coverage Reports</h1>

        <div class="grid">
            <div class="card">
                <h2>🐍 Backend Coverage</h2>
                <p>Python backend test coverage including unit, integration, and contract tests.</p>
                <a href="backend/index.html" class="btn">View Report</a>
            </div>

            <div class="card">
                <h2>⚛️ Frontend Coverage</h2>
                <p>React frontend test coverage including component and unit tests.</p>
                <a href="frontend/index.html" class="btn">View Report</a>
            </div>

            <div class="card">
                <h2>🎭 E2E Test Results</h2>
                <p>End-to-end test results using Playwright.</p>
                <a href="e2e/index.html" class="btn">View Report</a>
            </div>
        </div>

        <div class="timestamp">
            Generated: <script>document.write(new Date().toLocaleString())</script>
        </div>
    </div>
</body>
</html>
EOF

echo -e "${GREEN}✅ Coverage reports generated in coverage-reports/${NC}"
echo -e "${YELLOW}📂 Open coverage-reports/index.html in your browser to view the reports${NC}"

# Open in browser if on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    open coverage-reports/index.html
fi