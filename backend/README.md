# WebClippings Backend

Backend application publishing an API and a web application to manage clippings.

## Directory

- `backend/apps/clips/` models, HTML views, API serializers/views, tests
- `backend/apps/accounts/` auth views/templates/tests
- `backend/webclippings/` settings, URL routing, auth class

## Prerequisites

- Python 3.12+
- `pip`

## Install dependencies

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configure current worktree environment

```bash
cd backend
./scripts/bootsrap.sh --bootstrap-only
```

Resolves deterministic per-worktree defaults for:
- PostgreSQL runtime via `infra/docker/docker-compose.yml` (when `DATABASE_URL` is not already set)
- backend port (with automatic fallback to the next free port in range)
- backend host/base URL
- a shared per-worktree env file: `backend/.local/worktree-env-<worktree-id>.env`

## Run server

```bash
cd backend
./scripts/start-server.sh
```

Resolved URL is worktree-specific and deterministic (port can fall forward if busy).
Check the active URL with:

```bash
cd backend
./scripts/check-server.sh
```

This also ensures that the current environment is configured (similarly to `--bootstrap-only`).

Stop server:

```bash
cd backend
./scripts/stop-server.sh
```

Check server status:

```bash
cd backend
./scripts/check-server.sh
```

## Local environment introspection

You can inspect resolved runtime values without starting Django:

```bash
cd backend
./scripts/bootsrap.sh --print-json
```

You can print the resolved env-file path:

```bash
cd backend
./scripts/bootsrap.sh --print-env-path
```

Alternatively, you can resolve runtime values by inspecting the runtime
metadata for the worktree environment:
```bash
cd backend
cat ./.local/worktree-runtime-<worktree-id>.json
```
Here, `<worktree-id>` is `<worktree-basename>-<sha1-prefix>` derived from the
worktree root directory path (also emitted by the `--print-json` option).

For full options:

```bash
cd backend
./scripts/bootsrap.sh --help
```

## Source local environment variables 

```bash
cd backend
source ./scripts/env.sh --setup
```

For more options:

```bash
./scripts/env.sh --help
```

## Tests

Run backend non-E2E tests (default local backend test path):

```bash
make backend-test-unit
```

Run backend browser E2E tests (Playwright):

```bash
make backend-test-e2e
```

Run all backend checks (tests + lint + typecheck + format check):

```bash
make backend-verify
```

## API behavior notes

The authenticated clips list endpoint (`/api/clips/`) supports:

- repeated `label` query parameters (AND semantics across selected labels)
- `url` query parameter for exact URL filtering

The authenticated quick search endpoint (`/api/clips/quick-search/`) supports:

- required `q` query parameter
- `q` length between 3 and 50 characters
- grouped result payload (`clips`, `labels`, `websites`) with top-ranked hits

The label catalog endpoint (`/api/labels/`) returns a flat user-scoped list of:

- `name`
- `slug`
- `color`

Filtering/query parameters are ignored for label catalog listing.

For direct script usage without Make targets:

```bash
cd backend
./scripts/test.sh
./scripts/test-e2e.sh
```
