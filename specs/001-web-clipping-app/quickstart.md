# Quickstart: Web Clipping and Reference Application (MVP)

**Feature**: [specs/001-web-clipping-app/spec.md](specs/001-web-clipping-app/spec.md)  
**Plan**: [specs/001-web-clipping-app/plan.md](specs/001-web-clipping-app/plan.md)

This quickstart explains how to run the Django backend, PostgreSQL, and (later) the Chrome extension in a local, cloud-native-friendly way.

---

## Prerequisites

- Python 3.11+ (ideally 3.12)
- Docker and Docker Compose
- A recent version of Google Chrome
- Git and access to this repository

---

## 1. Clone and Set Up Environment

```bash
git clone <repo-url>
cd webclippings
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file (or equivalent) with environment variables for local development, for example:

```bash
DJANGO_SECRET_KEY=changeme
DJANGO_DEBUG=true
DATABASE_URL=postgres://webclippings:password@localhost:5432/webclippings
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## 2. Run PostgreSQL (Local via Docker)

```bash
docker run --name webclippings-postgres -e POSTGRES_USER=webclippings \
  -e POSTGRES_PASSWORD=password -e POSTGRES_DB=webclippings \
  -p 5432:5432 -d postgres:16
```

---

## 3. Run Django Backend Locally

Start the backend with the worktree-aware helper script:

```bash
./backend/scripts/bootsrap.sh
```

The script automatically ensures database readiness, runs migrations, ensures an admin user exists, emits worktree runtime/env metadata, and picks deterministic per-worktree backend/database ports so multiple worktrees can run in parallel without collisions.

By default it provisions local credentials `admin` / `admin`. Override admin credentials with `DJANGO_ADMIN_USERNAME`, `DJANGO_ADMIN_EMAIL`, and `DJANGO_ADMIN_PASSWORD`. Set `DJANGO_ENV=production` (or `ENVIRONMENT=production`) to disable this auto-bootstrap.

Optional overrides:

```bash
DJANGO_DEV_PORT=8010 ./backend/scripts/bootsrap.sh
DJANGO_DEV_DB_PORT=16432 ./backend/scripts/bootsrap.sh
```

---

## 4. API Endpoints and Docs

The JSON REST API for clips and labels will be under a prefix such as `/api/`. See:

- OpenAPI contract: [specs/001-web-clipping-app/contracts/openapi.yaml](specs/001-web-clipping-app/contracts/openapi.yaml)

Once implemented, you can use tools like `curl`, HTTPie, or your browser to interact with endpoints like:

- `GET /api/clips/`
- `POST /api/clips/`
- `GET /api/labels/`

---

## 5. Chrome Extension (MVP Flow)

Once the Chrome extension directory exists (see plan structure), you will be able to:

1. Open `chrome://extensions` in Chrome.
2. Enable "Developer mode".
3. Click "Load unpacked" and point to the `extension/chrome` directory.
4. Confirm that the extension icon appears in the browser toolbar.

The extension will:
- Read the current tab’s title, URL, and selected text.
- Send a `POST /api/clips/` request to the backend with the clip data (and optional labels).
- Show a lightweight confirmation when clipping succeeds.

---

## 6. Cloud-Native and CI/CD Overview

- The Django app will be containerized using a `Dockerfile` (to be added under `infra/docker/`).
- A `docker-compose.yml` file will support local orchestration of Django + PostgreSQL.
- GitHub Actions will run workflows defined under `.github/workflows/` (for example, `ci.yml`) to:
  - Install dependencies and run tests.
  - Build and push Docker images to a container registry.
  - Optionally deploy to a staging/production environment via Kubernetes or another orchestrator.

These assets will be iteratively added as the implementation progresses, following the structure in the implementation plan.
