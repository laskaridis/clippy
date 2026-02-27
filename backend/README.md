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

## Run migrations

```bash
cd backend
python manage.py migrate
```

## Run (standard)

```bash
cd backend
python manage.py runserver
```

Default URL: `http://127.0.0.1:8000`

## Run for git worktree development

Use the worktree-aware launcher:

```bash
cd backend
./scripts/runserver_worktree.sh
```

This script resolves deterministic per-worktree defaults for:
- SQLite DB path
- backend port (with automatic fallback to the next free port in range)
- backend host/base URL

You can inspect resolved runtime values without starting Django:

```bash
cd backend
./scripts/runserver_worktree.sh --print-json
```

Alternatively, you can resolve runtime values by inspecting the runtime
metadata for the worktree environment:
```bash
cd backend
cat ./local/worktree-runtime-<worktree-id>.json
```
Here, <worktree-id> is the SHA1 hash of the worktree root directory
(also emitted by `--print-json` option)

For full options:

```bash
cd backend
./scripts/runserver_worktree.sh --help
```

## Tests

Run backend tests:

```bash
cd backend
python manage.py test
```
