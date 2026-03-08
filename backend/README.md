# WebClippings Backend

Backend application publishing an API and a web application to manage clippings.

## Directory

- `backend/apps/clips/` models, HTML views, API serializers/views, tests
- `backend/apps/accounts/` auth views/templates/tests
- `backend/webclippings/` settings, URL routing, auth class

## Prerequisites

- Python 3.11+
- `pip`

## Install dependencies

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configure current git environment 

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
./scripts/bootsrap.sh
```

Default URL: `http://127.0.0.1:8000`

Also ensures that the current environment is confitured (similarly to `--bootstrap-only`)

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
Here, <worktree-id> is the SHA1 hash of the worktree root directory
(also emitted by `--print-json` option)

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

Run backend tests:

```bash
cd backend
./scripts/bootsrap.sh --bootstrap-only
source ./scripts/env.sh --setup
python manage.py test
```
