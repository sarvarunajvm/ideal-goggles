# Frontend Test Coverage Improvement Plan

## Current State Analysis

### Overall Coverage
- **Current Coverage**: 58.93% (Need to reach 90%)
- **Gap to Target**: 31.07%
- **Test Success Rate**: ~85% (some failing tests need fixes)

### Coverage Breakdown by Category

#### Critical Files (0% Coverage) - Priority 1
1. **src/main.tsx** (0%, 55 lines) - Application entry point
2. **src/utils/logger.ts** (0%, 389 lines) - Logging utility
3. **src/types/global.d.ts** (0%) - Type definitions

#### Low Coverage Components - Priority 2
1. **src/pages/PeoplePage.tsx** (32.25%, ~300 lines uncovered)
2. **src/pages/SearchPage.tsx** (48.24%, ~250 lines uncovered)
3. **src/pages/SettingsPage.tsx** (51.13%, ~200 lines uncovered)

#### Components Needing Improvement - Priority 3
1. **src/components/StatusBar.tsx** (12.5%, 28 lines uncovered)
2. **src/components/SearchResults.tsx** (56.72%, ~170 lines uncovered)
3. **src/components/SearchFilters.tsx** (55.78%, ~65 lines uncovered)
4. **src/components/SearchInput.tsx** (66.07%, 38 lines uncovered)

#### UI Components - Priority 4
1. **src/components/ui/use-toast.ts** (77.19%, needs improvement)
2. **src/components/ui/checkbox.tsx** (87.5%)
3. **src/components/ui/switch.tsx** (85.71%)
4. **src/components/ui/card.tsx** (96.15%)
5. **src/components/ui/toast.tsx** (96.87%)

### Failing Tests to Fix
1. **logger.test.ts** - Request ID generation test
2. **osIntegration.test.ts** - Clipboard mock issues (5 tests)
3. **App.test.tsx** - Router warnings

## Git Worktree Strategy

### Worktree Structure
```
ideal-goggles/
├── (main branch) - Fix failing tests
├── frontend-tests-pages/      - Page components (PeoplePage, SearchPage, SettingsPage)
├── frontend-tests-components/ - Component tests (SearchResults, SearchFilters, StatusBar)
├── frontend-tests-utils/      - Utils & services (logger, apiClient, osIntegration)
├── frontend-tests-ui/         - UI components (toast, checkbox, switch, etc.)
└── frontend-tests-integration/ - Integration & E2E tests
```

## Execution Plan

### Phase 1: Setup & Fix Existing Tests (Main Branch)
**Target: Fix all failing tests**
1. Fix logger.test.ts - Request ID generation
2. Fix osIntegration.test.ts - Clipboard mocking
3. Fix App.test.tsx - Router configuration
4. Ensure 100% pass rate for existing tests

### Phase 2: Create Worktrees
```bash
git branch frontend-tests-pages
git branch frontend-tests-components
git branch frontend-tests-utils
git branch frontend-tests-ui
git branch frontend-tests-integration

git worktree add frontend-tests-pages frontend-tests-pages
git worktree add frontend-tests-components frontend-tests-components
git worktree add frontend-tests-utils frontend-tests-utils
git worktree add frontend-tests-ui frontend-tests-ui
git worktree add frontend-tests-integration frontend-tests-integration
```

### Phase 3: Parallel Test Development

#### Worktree 1: Pages (frontend-tests-pages)
**Target: +20% coverage**
- [ ] PeoplePage.test.tsx (comprehensive)
- [ ] SearchPage.test.tsx (comprehensive)
- [ ] SettingsPage.test.tsx (comprehensive)
- Mock API calls, state management, user interactions
- Test error boundaries and loading states

#### Worktree 2: Components (frontend-tests-components)
**Target: +10% coverage**
- [ ] StatusBar.test.tsx
- [ ] SearchResults.test.tsx (improve)
- [ ] SearchFilters.test.tsx (improve)
- [ ] SearchInput.test.tsx (improve)
- [ ] PersonCard.test.tsx
- [ ] PhotoGrid.test.tsx

#### Worktree 3: Utils & Services (frontend-tests-utils)
**Target: +8% coverage**
- [ ] logger.test.ts (complete coverage)
- [ ] apiClient.test.ts (improve)
- [ ] osIntegration.test.ts (fix & improve)
- [ ] Add utility helper tests

#### Worktree 4: UI Components (frontend-tests-ui)
**Target: +5% coverage**
- [ ] use-toast.test.ts (improve hooks)
- [ ] checkbox.test.tsx
- [ ] switch.test.tsx
- [ ] Complex UI interaction tests

#### Worktree 5: Integration (frontend-tests-integration)
**Target: +3% coverage**
- [ ] main.tsx test
- [ ] App integration tests
- [ ] Router navigation tests
- [ ] Context provider tests

## Test Writing Guidelines

### 1. Testing Library Setup
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
```

### 2. Mock Patterns
```typescript
// API mocking
vi.mock('@/services/apiClient', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

// Component mocking
vi.mock('@/components/SomeComponent', () => ({
  default: vi.fn(() => <div data-testid="mock-component" />)
}))
```

### 3. Test Structure
```typescript
describe('Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render correctly', () => {})
  })

  describe('User Interactions', () => {
    it('should handle click events', async () => {})
  })

  describe('API Integration', () => {
    it('should fetch data on mount', async () => {})
  })

  describe('Error Handling', () => {
    it('should display error state', () => {})
  })
})
```

### 4. Coverage Focus Areas
- Component mounting and unmounting
- User interactions (click, type, hover)
- API call handling (success, error, loading)
- State management
- Edge cases and error boundaries
- Accessibility attributes

## Commands for Parallel Execution

```bash
# Terminal 1 - Fix existing tests
pnpm test:watch

# Terminal 2 - Pages
cd frontend-tests-pages
pnpm test:watch src/pages

# Terminal 3 - Components
cd frontend-tests-components
pnpm test:watch src/components

# Terminal 4 - Utils
cd frontend-tests-utils
pnpm test:watch src/utils src/services

# Terminal 5 - UI Components
cd frontend-tests-ui
pnpm test:watch src/components/ui

# Terminal 6 - Integration
cd frontend-tests-integration
pnpm test:watch src/main.tsx src/App.tsx
```

## Success Metrics
- [ ] Overall coverage ≥ 90%
- [ ] All tests passing (100% success rate)
- [ ] No console errors or warnings
- [ ] Tests complete in < 30 seconds
- [ ] Each file has ≥ 80% coverage

## Timeline Estimate
- Phase 1 (Fix existing): 30 minutes
- Phase 2 (Setup): 10 minutes
- Phase 3 (Parallel development): 2-3 hours
- Phase 4 (Merge & verify): 20 minutes
- **Total: 3-4 hours**

## Key Testing Libraries
- **Vitest**: Test runner
- **@testing-library/react**: React testing utilities
- **@testing-library/user-event**: User interaction simulation
- **@vitest/ui**: Visual test runner
- **@testing-library/jest-dom**: Additional matchers

## Coverage Report Commands
```bash
# Run tests with coverage
pnpm test:coverage

# Open HTML coverage report
pnpm coverage

# Watch mode with coverage
pnpm test:watch --coverage
```