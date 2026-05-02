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

## Run server

Inside the devcontainer, start Django directly with:

```bash
make backend-run
```

That command runs migrations, ensures the local admin user exists, and starts
`python manage.py runserver 0.0.0.0:${DJANGO_DEV_PORT}` from `backend/`.

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
