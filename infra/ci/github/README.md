# GitHub CI assets for WebClippings

This directory documents GitHub Actions CI behavior used by this repository.

## Current workflow

Workflow file: `.github/workflows/ci.yml`

Quality jobs:

- `backend-quality`: Ruff, Black check, mypy (Python 3.12)
- `extension-quality`: ESLint, Prettier check, TypeScript check (Node 20 + pnpm)

Backend tests:

- `backend-tests`: `python manage.py test --exclude-tag=e2e`
- `backend-e2e-tests`: installs Playwright Chromium and runs `python manage.py test --tag=e2e`

Extension tests:

- `extension-unit-tests`: `pnpm test`
- `extension-e2e-tests`: `pnpm run test:e2e` with Playwright browser cache

## Database service

PostgreSQL 16 is provisioned as a workflow service for jobs that require backend/database access.

## Trigger and concurrency

- Triggers on all branch pushes and pull requests targeting `master` (plus wildcard branch matching).
- Uses per-ref workflow concurrency to cancel superseded in-progress runs.
