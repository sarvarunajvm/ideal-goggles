# Contributing to Ideal Goggles

Thanks for your interest in contributing! This guide helps you set up, develop, test, and submit changes consistently.

## Project Layout

- Backend (FastAPI, Python): `backend/src` (API, services, workers)
- Backend tests: `backend/tests` (unit, contract, integration, performance)
- Frontend (React + Vite + Electron): `frontend/src`
- Frontend tests: `frontend/tests` (components, unit); E2E: root `func_tests/` (Playwright)
- Electron main: `frontend/electron/`
- Local runtime data: `backend/data`, `backend/cache`

## Setup

1. Install Node.js 18+ and Python 3.12+
2. Install dependencies:
   - `make install` (backend + frontend + root)
   - `make backend-install` for backend venv
3. Start dev:
   - `pnpm run dev` (backend 5555, frontend 3333, electron)

## Commands

- Backend: `make backend-dev`, `make backend-test`, `make backend-lint`, `make backend-typecheck`, `make backend-format`, `make backend-package`
- Frontend: `pnpm --filter frontend run dev`, `pnpm --filter frontend run test`, `pnpm --filter frontend run lint`, `pnpm --filter frontend run type-check`
- Packaging: `pnpm run build:electron`, `make dist-mac`, `make dist-win`, `make dist-all`

## Coding Standards

- Python: black (88), ruff, mypy relaxed; snake_case modules/functions; PascalCase classes.
- TypeScript/React: ESLint + Prettier; 2-space indent; PascalCase components; camelCase vars/functions.
- Imports: frontend uses `@` alias; backend imports under `src.` package.

## Testing

- Backend: Pytest with markers `contract`, `integration`, `performance`. Example: `pytest -m "not performance"`.
– Frontend: Jest + Testing Library in `frontend/tests`; E2E with Playwright under `func_tests/`.

## Pull Requests

- Write clear PR titles with scope prefix: `backend: ...`, `frontend: ...`, `tooling: ...`.
- Include rationale, screenshots for UI, reproduction steps, and test plan.
- Update docs when applicable: `README.md`, `docs/USER_MANUAL.md`, `docs/DEVELOPER_GUIDE.md`.

## Housekeeping

- Do not commit secrets. Copy `backend/.env.example` to `backend/.env`.
- Keep `backend/data/` and `backend/cache/` out of VCS; they are created at runtime.
- Avoid duplicate tests and backup files. If you find `.bak` or duplicate test names, remove or merge them.

## Branching

- Create feature branches from `main`.
- Rebase onto `main` before merging.

## CI

- Ensure `pnpm test` and `make backend-test` pass locally.
- Run `pnpm lint` and `make backend-lint` before pushing.

Happy contributing!
