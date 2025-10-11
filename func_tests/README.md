# Functional Tests

End-to-end and performance tests for the Ideal Goggles application using Playwright.

## Structure

```
func_tests/
├── e2e/                    # End-to-end test suites
│   ├── 00-p0-critical.test.ts    # P0 critical path tests
│   ├── 01-smoke.test.ts          # Smoke tests
│   ├── 02-search.test.ts         # Search functionality
│   ├── 03-settings.test.ts       # Settings page
│   ├── 04-people.test.ts         # People/face detection
│   ├── 05-workflows.test.ts      # User workflows
│   ├── 06-preview-drawer.test.ts # Preview drawer UI
│   ├── 07-dependencies.test.ts   # Dependency checks
│   ├── 08-integration.test.ts    # Integration tests
│   ├── 09-lightbox.test.ts       # Lightbox component
│   └── 10-onboarding.test.ts     # Onboarding flow
├── performance/            # Performance tests
│   └── virtual-scroll-perf.test.ts
├── page-objects/          # Page Object Model
│   ├── BasePage.ts        # Base page with common functionality
│   ├── SearchPage.ts      # Search page interactions
│   ├── SettingsPage.ts    # Settings page interactions
│   ├── PeoplePage.ts      # People page interactions
│   └── index.ts           # Barrel exports
├── helpers/               # Test utilities
│   ├── api-client.ts      # API client for backend calls
│   ├── test-data.ts       # Test data management
│   ├── global-setup.ts    # Global test setup
│   ├── global-teardown.ts # Global test teardown
│   └── index.ts           # Barrel exports
├── fixtures/              # Test fixtures and assets
│   └── images/            # Test images
├── playwright.config.ts   # Playwright configuration
├── test-config.ts         # Test feature flags and config
├── test-suites.json       # Test suite organization
└── tsconfig.json          # TypeScript configuration
```

## Prerequisites

- Node.js 18+
- pnpm
- Python 3.11+
- Backend and frontend dependencies installed

## Installation

```bash
# Install Playwright and dependencies
pnpm install
pnpm exec playwright install chromium
```

## Running Tests

### All Tests

```bash
pnpm run e2e
```

### Smoke Tests Only

```bash
pnpm run e2e:smoke
```

### Specific Test File

```bash
pnpm exec playwright test e2e/01-smoke.test.ts
```

### With UI Mode (Interactive)

```bash
pnpm exec playwright test --ui
```

### Debug Mode

```bash
pnpm exec playwright test --debug
```

### With Existing Server

If you already have the app running:

```bash
USE_EXISTING_SERVER=1 pnpm run e2e
```

## Test Configuration

Tests support various feature flags and environment variables:

### Environment Variables

- `CI` - Running in CI environment (affects retries, parallelization)
- `USE_EXISTING_SERVER` - Use already running servers instead of starting new ones
- `REUSE_EXISTING_SERVER` - Reuse servers between test runs
- `SKIP_HEAVY_TESTS` - Skip performance-intensive tests
- `SKIP_INTEGRATION_TESTS` - Skip integration tests

### Feature Flags

Tests automatically detect available features:
- OCR support
- Face search
- Semantic search
- Image search
- Model dependencies

## Test Suites

Tests are organized into logical suites (see `test-suites.json`):

- **smoke** - Basic functionality verification
- **core** - Essential features (search, settings)
- **advanced** - Features requiring additional setup (people/faces)
- **integration** - End-to-end workflows
- **ui** - User interface components
- **system** - System and dependency tests

## Writing Tests

### Using Page Objects

```typescript
import { test, expect } from '@playwright/test';
import { SearchPage } from '../page-objects';

test('search functionality', async ({ page }) => {
  const searchPage = new SearchPage(page);
  await searchPage.goto('/');
  await searchPage.performTextSearch('vacation photos');
  expect(await searchPage.hasSearchResults()).toBe(true);
});
```

### Using Test Config

```typescript
import { getTestConfig, skipIfFeatureUnavailable } from '../test-config';

test('semantic search', async ({ page }) => {
  const config = await getTestConfig();
  skipIfFeatureUnavailable(test, 'semanticSearch', config);

  // Test code runs only if semantic search is available
});
```

## Test Reports

After running tests, view reports:

```bash
# HTML report (auto-opens on failure)
pnpm exec playwright show-report

# Or manually open
open playwright-report/index.html
```

### Report Types Generated

- **HTML Report** - `playwright-report/` (interactive UI)
- **JSON Report** - `test-results/results.json` (for CI)
- **JUnit XML** - `test-results/junit.xml` (for CI integration)
- **Blob Report** - `blob-report/` (for merging parallel runs)

## Debugging

### Screenshots and Videos

Failed tests automatically capture:
- Screenshots (`screenshot: 'only-on-failure'`)
- Videos (`video: 'retain-on-failure'`)
- Traces (`trace: 'on-first-retry'`)

### Viewing Traces

```bash
pnpm exec playwright show-trace test-results/path-to-trace.zip
```

### Browser Console

Enable console logs in tests:

```typescript
page.on('console', msg => console.log(msg.text()));
```

## Best Practices

1. **Use Page Objects** - Encapsulate page interactions in page objects
2. **Stable Selectors** - Prefer `data-testid` over CSS classes
3. **Wait Strategies** - Use built-in waiting, avoid hard timeouts
4. **Test Independence** - Each test should be runnable in isolation
5. **Clean State** - Tests should clean up after themselves
6. **Meaningful Names** - Use descriptive test and step names
7. **Error Messages** - Provide clear assertion messages

## Continuous Integration

Tests are configured for CI with:
- Reduced parallelization (`workers: 1`)
- Automatic retries (`retries: 2`)
- Longer timeouts (`timeout: 120000`)
- No server reuse
- Only smoke and core suites by default

## Troubleshooting

### Tests Timing Out

- Check if backend/frontend servers started properly
- Increase timeout in `playwright.config.ts`
- Check network tab for stuck requests

### Flaky Tests

- Use proper wait strategies instead of `waitForTimeout`
- Check for race conditions
- Verify test data is consistent

### CI Failures

- Check CI logs for server startup issues
- Verify all dependencies are installed
- Ensure database is initialized properly

## Contributing

When adding new tests:

1. Follow the existing naming convention (`XX-description.test.ts`)
2. Create page objects for new pages
3. Update `test-suites.json` if adding new suite
4. Add test data to `helpers/test-data.ts`
5. Document any new environment variables
