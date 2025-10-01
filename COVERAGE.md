# 📊 Test Coverage & CI/CD Documentation

## Overview

This project uses comprehensive testing and coverage reporting across backend (Python), frontend (React), and E2E (Playwright) tests. All test results and coverage reports are automatically published to GitHub Pages.

## 🔗 Quick Links

- **Live Coverage Reports**: https://sarvarunajvm.github.io/ideal-goggles/
- **CI Pipeline**: [GitHub Actions](https://github.com/sarvarunajvm/ideal-goggles/actions)
- **Codecov Dashboard**: [codecov.io/gh/sarvarunajvm/ideal-goggles](https://codecov.io/gh/sarvarunajvm/ideal-goggles)

## 📈 Current Coverage

| Component | Coverage | Tests | Status |
|-----------|----------|-------|--------|
| Backend   | ~37%     | 163   | ✅ Passing |
| Frontend  | TBD      | 64    | ⚠️ 11 failures |
| E2E       | TBD      | TBD   | 🔄 In Progress |

## 🏃 Running Tests Locally

### Quick Commands

```bash
# Run all tests with coverage
make coverage

# Generate and view HTML reports
make coverage-report

# Individual components
make backend-coverage    # Backend only
make frontend-coverage   # Frontend only

# Using the script directly
./scripts/run-coverage.sh
./scripts/run-coverage.sh --with-e2e  # Include E2E tests
```

### Manual Testing

```bash
# Backend
cd backend
pytest --cov=src --cov-report=html --cov-report=term

# Frontend
cd frontend
pnpm test -- --coverage

# E2E
cd tests
npx playwright test --reporter=html
```

## 🤖 CI/CD Workflows

### 1. Test & Coverage Workflow (`test-and-coverage.yml`)

Triggered on:
- Push to `main` or `develop`
- Pull requests to `main`
- Manual dispatch

Features:
- Parallel test execution (backend, frontend, E2E)
- Coverage report generation
- Automatic deployment to GitHub Pages
- PR comment with coverage summary
- Test result publishing

### 2. CI Workflow (`ci.yml`)

Fast CI checks including:
- Linting (Python & TypeScript)
- Type checking
- Build verification
- P0 critical E2E tests only

## 📝 Coverage Reports

### GitHub Pages

Coverage reports are automatically deployed to GitHub Pages when tests run on the `main` branch:

1. **Backend Coverage**: `/backend/index.html`
   - Unit test coverage
   - Integration test coverage
   - Contract test coverage

2. **Frontend Coverage**: `/frontend/lcov-report/index.html`
   - Component test coverage
   - Unit test coverage

3. **E2E Test Results**: `/e2e/index.html`
   - Playwright test results
   - Screenshots on failure
   - Test execution videos

### Local Reports

After running `make coverage-report`, open:
```bash
open coverage-reports/index.html  # macOS
xdg-open coverage-reports/index.html  # Linux
start coverage-reports/index.html  # Windows
```

## 🔧 Configuration

### Backend (pytest)

Configuration in `backend/pytest.ini`:
```ini
[pytest]
addopts =
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
```

### Frontend (Jest)

Configuration in `frontend/jest.config.js`:
```javascript
collectCoverageFrom: ['src/**/*.(ts|tsx|js|jsx)'],
coverageReporters: ['json', 'lcov', 'html', 'text']
```

### E2E (Playwright)

Configuration in `tests/playwright.config.ts`:
```typescript
reporter: [
  ['html', { outputFolder: 'playwright-report' }],
  ['junit', { outputFile: 'test-results/junit.xml' }]
]
```

## 🎯 Coverage Goals

| Component | Current | Target | Notes |
|-----------|---------|--------|-------|
| Backend   | 37%     | 70%    | Focus on critical paths |
| Frontend  | TBD     | 60%    | Component & integration |
| E2E       | TBD     | -      | Critical user journeys |

## 🚀 Improving Coverage

### Backend

Priority areas:
1. API endpoints (`src/api/`)
2. Core services (`src/services/`)
3. Database operations (`src/db/`)

```bash
# Run specific test markers
pytest -m unit        # Unit tests only
pytest -m integration # Integration tests
pytest -m contract    # API contract tests
```

### Frontend

Priority areas:
1. Component interaction tests
2. Store/state management
3. API client services

```bash
# Run specific test suites
pnpm test SearchBar   # Single component
pnpm test components  # All components
```

## 📋 PR Coverage Requirements

Pull requests will automatically:
1. Run all tests
2. Generate coverage reports
3. Comment coverage summary on PR
4. Fail if coverage decreases significantly

### Bypassing Coverage Checks

In exceptional cases, add to PR description:
```
[skip-coverage-check]
Reason: <explanation>
```

## 🛠️ Troubleshooting

### Common Issues

1. **Coverage not generating**
   ```bash
   # Ensure dependencies installed
   pip install pytest-cov  # Backend
   pnpm add -D jest --coverage  # Frontend
   ```

2. **GitHub Pages not updating**
   - Check workflow permissions in repository settings
   - Ensure GitHub Pages is enabled
   - Verify branch is set to `gh-pages`

3. **Local reports not opening**
   ```bash
   # Check if files exist
   ls -la coverage-reports/

   # Manually open in browser
   python -m http.server 8000 --directory coverage-reports
   # Visit http://localhost:8000
   ```

## 📚 Resources

- [Jest Coverage Docs](https://jestjs.io/docs/configuration#collectcoverage-boolean)
- [Pytest Coverage](https://pytest-cov.readthedocs.io/)
- [Playwright Reporters](https://playwright.dev/docs/test-reporters)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Codecov Documentation](https://docs.codecov.com/)

---

**Note**: Coverage badges and reports update automatically with each push to `main`. Check the [Actions tab](https://github.com/sarvarunajvm/ideal-goggles/actions) for real-time status.