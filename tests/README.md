# Integration Tests for Photo Search Application

Comprehensive Playwright-based integration tests for the Photo Search and Navigation System.

## 📋 Prerequisites

- Node.js 18+ installed
- Python 3.11+ with backend dependencies
- Playwright browsers installed

## 🚀 Quick Start

```bash
# Install dependencies
pnpm install

# Install Playwright browsers
pnpm run install

# Run all tests
pnpm test

# Run specific test suites
pnpm run test:smoke      # Quick smoke tests
pnpm run test:search     # Search functionality
pnpm run test:settings   # Settings & configuration
pnpm run test:people     # People management
pnpm run test:workflows  # End-to-end workflows
```

## 📁 Test Structure

```
tests/
├── e2e/                    # Test files
│   ├── 01-smoke.test.ts   # Basic functionality tests
│   ├── 02-search.test.ts  # Search feature tests
│   ├── 03-settings.test.ts # Settings & indexing tests
│   ├── 04-people.test.ts  # People management tests
│   └── 05-workflows.test.ts # Complex workflow tests
├── page-objects/           # Page Object Models
│   ├── BasePage.ts        # Common page functionality
│   ├── SearchPage.ts      # Search page interactions
│   ├── SettingsPage.ts    # Settings page interactions
│   └── PeoplePage.ts      # People page interactions
├── helpers/                # Test utilities
│   ├── api-client.ts      # Direct API testing
│   ├── test-data.ts       # Test data generation
│   ├── global-setup.ts    # Test environment setup
│   └── global-teardown.ts # Test cleanup
└── fixtures/               # Test images and data
```

## 🎯 Test Coverage

### Smoke Tests
- Application loading
- Backend connectivity
- Navigation functionality
- Responsive design
- Error handling

### Search Tests
- Text search with queries
- Semantic search with natural language
- Image similarity search
- Search filters and pagination
- Search mode switching

### Settings Tests
- Root folder management
- Indexing controls
- Feature toggles (OCR, Face Search, Semantic)
- Performance settings
- Configuration persistence

### People Tests
- Person enrollment with photos
- Editing person details
- Face search integration
- Bulk operations
- Photo management

### Workflow Tests
- Complete indexing and search flow
- Person enrollment and face search
- Configuration optimization
- Error recovery
- Multi-user scenarios
- Data migration
- Performance optimization
- Accessibility

## 🛠️ Running Tests

### Interactive Mode
```bash
# Run tests with UI (great for debugging)
pnpm run test:ui

# Run tests in headed browser
pnpm run test:headed

# Debug specific test
pnpm run test:debug
```

### Different Browsers
```bash
# Chrome only
pnpm run test:chrome

# Firefox only
pnpm run test:firefox

# Safari only
pnpm run test:webkit

# Mobile browsers
pnpm run test:mobile
```

### Performance
```bash
# Run tests in parallel (faster)
pnpm run test:parallel

# Run tests serially (more stable)
pnpm run test:serial
```

## 📊 Test Reports

After running tests, view the HTML report:
```bash
pnpm run test:report
```

Reports include:
- Test results summary
- Screenshots on failure
- Videos of failed tests
- Execution traces

## 🐛 Debugging

### Using Playwright Inspector
```bash
pnpm run test:debug
```

### Generate Test Code
```bash
pnpm run codegen
```

### View Traces
```bash
pnpm run trace trace.zip
```

## ⚙️ Configuration

### Environment Variables
Create a `.env` file for test configuration:
```env
BASE_URL=http://localhost:3000
API_URL=http://localhost:5555
TEST_TIMEOUT=60000
HEADLESS=true
```

### Playwright Config
Edit `playwright.config.ts` to customize:
- Browser settings
- Viewport sizes
- Timeouts
- Parallel execution
- Screenshot/video settings

## 🔄 CI/CD Integration

### GitHub Actions
```yaml
- name: Install dependencies
  run: |
    cd tests
    pnpm ci
    npx playwright install

- name: Run tests
  run: |
    cd tests
    pnpm test

- name: Upload artifacts
  uses: actions/upload-artifact@v3
  if: always()
  with:
    name: playwright-report
    path: tests/playwright-report/
```

## 📝 Writing New Tests

### 1. Create Test File
```typescript
import { test, expect } from '@playwright/test';
import { YourPage } from '../page-objects/YourPage';

test.describe('Feature Name', () => {
  test('should do something', async ({ page }) => {
    const yourPage = new YourPage(page);
    await yourPage.goto();
    // Test implementation
  });
});
```

### 2. Add Page Object
```typescript
export class YourPage extends BasePage {
  constructor(page: Page) {
    super(page);
    // Initialize locators
  }

  async yourMethod() {
    // Page interactions
  }
}
```

### 3. Run Your Test
```bash
pnpm test -- --grep "Feature Name"
```

## 🧪 Best Practices

1. **Use Page Objects**: Keep test logic separate from page interactions
2. **Test Data**: Use `TestData` helper for consistent test data
3. **API Testing**: Use `APIClient` for backend verification
4. **Cleanup**: Always clean up test data in `afterAll` hooks
5. **Assertions**: Use clear, specific assertions
6. **Timeouts**: Set appropriate timeouts for different operations
7. **Screenshots**: Take screenshots for important states
8. **Parallel Safety**: Ensure tests don't interfere with each other

## 🚨 Troubleshooting

### Tests Failing
- Check backend is running: `http://localhost:5555/health`
- Check frontend is running: `http://localhost:3000`
- Clear test data: `rm -rf /tmp/test-*`
- Update Playwright: `pnpm update @playwright/test`

### Slow Tests
- Run in parallel: `pnpm run test:parallel`
- Reduce test data size
- Use headed mode for debugging only
- Check network latency

### Flaky Tests
- Add proper waits: `waitForLoadingComplete()`
- Check for race conditions
- Use `test.serial` for dependent tests
- Increase timeouts if needed

## 📚 Resources

- [Playwright Documentation](https://playwright.dev)
- [Page Object Model](https://playwright.dev/docs/pom)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [CI/CD Guide](https://playwright.dev/docs/ci)