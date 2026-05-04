# WebClippings Backend

Backend application publishing an API and a web application to manage clippings.

## Directory

- `backend/apps/clips/` models, HTML views, API serializers/views, tests
- `backend/apps/accounts/` auth views/templates/tests
- `backend/webclippings/` settings, URL routing, auth class

## Local development

Create or reuse the worktree on the host, export `SANDBOX_REPO_URL`,
`GIT_AUTH_TOKEN`, and `SANDBOX_ID`, and open the checkout in Dev Containers.
`initializeCommand` generates `.devcontainer/.env` from the tracked example
file plus those sandbox inputs. The `dev-sandbox` service is the sandbox for
implementation work, and `/workspace` inside it is the cloned repo for the
active sandbox rather than the host checkout.

## Run server

Inside the devcontainer, start Django directly with:

```bash
make backend-run
```

That command runs migrations, ensures the local admin user exists, and starts
`python manage.py runserver 0.0.0.0:${DJANGO_DEV_PORT}` from `backend/`.

From the host browser, verify the login page at:

```text
http://localhost:${DJANGO_DEV_PORT}/accounts/login/
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
