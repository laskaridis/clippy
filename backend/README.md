# WebClippings Backend

Quick guide to install, run, and test the Django backend locally.

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
