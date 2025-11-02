# Git Hooks

This directory contains git hooks that help maintain code quality and consistency.

## Available Hooks

### `pre-commit`

Runs before every commit to ensure code quality and prevent debug code from being committed.

**Checks performed:**

#### Frontend (`.ts`, `.tsx`, `.js`, `.jsx` files in `frontend/src/`)
- ❌ **Blocks**: `console.log()` statements (suggests using logger instead)
- ❌ **Blocks**: `debugger` statements
- ✅ **Runs**: ESLint on staged files
- ✅ **Runs**: TypeScript type checking

#### Backend (`.py` files in `backend/`)
- ⚠️  **Warns**: `print()` statements (suggests using logger instead)
- ❌ **Blocks**: `breakpoint()` or `pdb` debugger statements
- ✅ **Runs**: Ruff linter

**Example output when blocked:**
```
❌ Found console.log statements:
   frontend/src/components/Example.tsx:15:  console.log('debug message');

💡 Use the logger utility instead: import { logger } from '@/utils/logger'
```

### `pre-push`

Runs before pushing tags to ensure version consistency across all package files.

**Checks performed:**
- Verifies `package.json` version matches the git tag
- Verifies `backend/pyproject.toml` version matches the git tag
- Blocks push if versions are out of sync

## Installation

Git hooks are automatically installed when you run:

```bash
pnpm install
```

This runs the `postinstall` script which calls `scripts/setup-hooks.sh`.

### Manual Installation

If you need to reinstall hooks manually:

```bash
bash scripts/setup-hooks.sh
```

This will:
1. Copy `scripts/git-hooks/pre-commit` → `.git/hooks/pre-commit`
2. Copy `scripts/git-hooks/pre-push` → `.git/hooks/pre-push`
3. Make both hooks executable

## Bypassing Hooks (Not Recommended)

In rare cases where you need to bypass hooks:

```bash
# Skip pre-commit hook
git commit --no-verify

# Skip pre-push hook
git push --no-verify
```

⚠️ **Warning**: Only bypass hooks when absolutely necessary, as they prevent bugs and maintain code quality.

## Best Practices

### Frontend Development

✅ **DO** use the logger utility:
```typescript
import { logger } from '@/utils/logger';

logger.debug('Debug message');
logger.info('Info message');
logger.warn('Warning message');
logger.error('Error message');
```

❌ **DON'T** use console.log:
```typescript
console.log('debug'); // Will be blocked by pre-commit hook
```

✅ **DO** use console for legitimate logging:
```typescript
console.error('Critical error'); // Allowed
console.warn('Important warning'); // Allowed
```

### Backend Development

✅ **DO** use the logging module:
```python
from src.core.logging_config import get_logger

logger = get_logger(__name__)

logger.debug('Debug message')
logger.info('Info message')
logger.warning('Warning message')
logger.error('Error message')
```

❌ **DON'T** use print statements (will warn):
```python
print('debug')  # Hook will warn but not block
```

❌ **DON'T** use debugger statements (will block):
```python
breakpoint()  # Blocked
import pdb; pdb.set_trace()  # Blocked
```

## Troubleshooting

### Hook not running

1. Verify hooks are installed:
   ```bash
   ls -la .git/hooks/pre-commit .git/hooks/pre-push
   ```

2. Reinstall hooks:
   ```bash
   bash scripts/setup-hooks.sh
   ```

### pnpm not found

The hooks require pnpm to be installed. If not available, you'll see:
```
⚠️  pnpm not found, skipping ESLint
⚠️  pnpm not found, skipping backend linting
```

Install pnpm:
```bash
npm install -g pnpm@10.18.1

# Then install project dependencies
pnpm install
```

### TypeScript errors

If the hook fails on TypeScript type checking:

1. Run locally to see errors:
   ```bash
   npm run typecheck:frontend
   ```

2. Fix the type errors before committing

### Permission errors

If you get permission denied errors:

```bash
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/pre-push
```

## Customization

To modify hook behavior, edit the source files in `scripts/git-hooks/` and reinstall:

1. Edit `scripts/git-hooks/pre-commit` or `scripts/git-hooks/pre-push`
2. Run `bash scripts/setup-hooks.sh`
3. Test your changes

## Performance

The pre-commit hook is optimized to only check **staged files**, not the entire codebase:

- Only runs ESLint on staged `.ts`/`.tsx` files
- Only runs Ruff on staged `.py` files
- TypeScript check is full project (required for type correctness)

Typical execution time: **2-5 seconds** depending on number of staged files.
