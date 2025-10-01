# Test Strategy - Ideal Goggles

## Test Priority Levels

### P0 - Critical (CI Required)
**Runtime: ~10-15 seconds**
- Application loads successfully
- Backend API health check
- Basic text search functionality
- Navigation between pages
- Error handling for backend failures

### P1 - Important (Nightly)
**Runtime: ~5 minutes**
- All search modes (text, semantic, image)
- Settings configuration
- Filter functionality
- Search result pagination
- Responsive design

### P2 - Extended (Weekly)
**Runtime: ~15 minutes**
- People management
- Face search integration
- Advanced workflows
- Performance tests
- Accessibility tests

## Test Execution Environments

### 1. CI Pipeline (Every PR/Push)
- **What**: P0 tests only
- **When**: On every push to main/develop, on every PR
- **Duration**: < 2 minutes
- **Browser**: Chromium only
- **Config**: `playwright.config.ci.ts`
- **Command**: `npx playwright test --config=playwright.config.ci.ts --grep @P0`

### 2. Nightly Tests
- **What**: Full test suite
- **When**: Daily at 2 AM UTC
- **Duration**: ~30 minutes
- **Browser**: All browsers
- **Config**: `playwright.config.ts`
- **Command**: `npx playwright test`

### 3. Local Development
- **Quick**: `npx playwright test e2e/00-p0-critical.test.ts`
- **Feature**: `npx playwright test e2e/02-search.test.ts`
- **Full**: `npx playwright test`

## Test Organization

```
tests/
├── e2e/
│   ├── 00-p0-critical.test.ts    # P0 - Must pass in CI
│   ├── 01-smoke.test.ts          # P0/P1 - Basic functionality
│   ├── 02-search.test.ts         # P1 - Search features
│   ├── 03-settings.test.ts       # P1 - Configuration
│   ├── 04-people.test.ts         # P2 - Advanced features
│   ├── 05-workflows.test.ts      # P2 - Complex workflows
│   ├── 06-preview-drawer.test.ts # P1 - UI components
│   ├── 07-dependencies.test.ts   # P2 - System checks
│   └── 08-integration.test.ts    # P2 - Full integration
├── helpers/
├── page-objects/
└── playwright.config.ts
```

## Conditional Test Execution

Tests automatically skip when dependencies are unavailable:

```typescript
// Skipped if face search not available
test('@P2 @requires-face-search searches photos by person', async () => {
  // Test implementation
});

// Skipped if models not loaded
test('@P2 @requires-models semantic search with embeddings', async () => {
  // Test implementation
});
```

## Performance Targets

| Test Level | Target Time | Max Time |
|------------|------------|----------|
| P0 (CI)    | 10s        | 15s      |
| P1         | 3min       | 5min     |
| P2         | 10min      | 15min    |
| Full Suite | 20min      | 30min    |

## Running Tests

### Quick P0 Tests (CI)
```bash
# Run only critical tests
npx playwright test --grep @P0

# CI configuration
npx playwright test --config=playwright.config.ci.ts
```

### Feature Development
```bash
# Run specific test file
npx playwright test e2e/02-search.test.ts

# Run with UI mode for debugging
npx playwright test --ui

# Run specific test
npx playwright test -g "performs basic text search"
```

### Full Test Suite
```bash
# All tests, all browsers
npx playwright test

# With specific browser
npx playwright test --project=chromium

# In headed mode
npx playwright test --headed
```

## Adding New Tests

1. **Determine Priority**:
   - P0: Critical user journey, blocks release
   - P1: Important feature, should work
   - P2: Nice to have, edge cases

2. **Add Appropriate Tags**:
   ```typescript
   test('@P0 critical feature', async () => {});
   test('@P1 important feature', async () => {});
   test('@P2 @requires-ocr OCR text extraction', async () => {});
   ```

3. **Follow Patterns**:
   - Use page objects for reusability
   - Mock external dependencies in P0 tests
   - Keep P0 tests fast and focused

## Monitoring & Reporting

- **CI Dashboard**: Check GitHub Actions for P0 test results
- **Nightly Reports**: Available as artifacts in GitHub Actions
- **Local Reports**: `npx playwright show-report`

## Best Practices

1. **P0 Tests Must**:
   - Run in < 15 seconds each
   - Not depend on external services
   - Cover critical user paths only
   - Use mocked data when possible

2. **Test Data**:
   - P0: Use mocked responses
   - P1/P2: Use test fixtures
   - Never use production data

3. **Stability**:
   - P0 tests should have 0% flakiness
   - Use explicit waits, not timeouts
   - Mock external dependencies