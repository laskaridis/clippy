# Quickstart: Web Clipping and Reference Application (MVP)

**Feature**: [specs/001-web-clipping-app/spec.md](specs/001-web-clipping-app/spec.md)  
**Plan**: [specs/001-web-clipping-app/plan.md](specs/001-web-clipping-app/plan.md)

This quickstart explains how to run the Django backend, PostgreSQL, and the Chrome extension in a devcontainer-first local workflow.

---

## Prerequisites

- Docker and Dev Containers support
- A recent version of Google Chrome
- Git and access to this repository

---

## 1. Clone and Set Up Environment

```bash
git clone <repo-url>
cd webclippings
cp .devcontainer/.env.example .devcontainer/.env
```

Set a unique backend port when another worktree may be running at the same time. Keep the host settings localhost-oriented:

```bash
DJANGO_SECRET_KEY=changeme
DJANGO_DEBUG=true
DJANGO_DEV_PORT=8010
ALLOWED_HOSTS=localhost,127.0.0.1,[::1]
```

---

## 2. Open the Worktree in Dev Containers

Use the checked-in `.devcontainer/` configuration and let the `dev-sandbox` service start idle.

---

## 3. Run Django Backend Locally

Start the backend explicitly from inside `dev-sandbox`:

```bash
make backend-run
```

This runs migrations, ensures the local admin user exists, and starts Django on `0.0.0.0:${DJANGO_DEV_PORT}`.
From the host browser, reach it at `http://localhost:<DJANGO_DEV_PORT>/accounts/login/`.

By default it provisions local credentials `admin` / `admin`. Override admin credentials with `DJANGO_ADMIN_USERNAME`, `DJANGO_ADMIN_EMAIL`, and `DJANGO_ADMIN_PASSWORD`. Set `DJANGO_ENV=production` (or `ENVIRONMENT=production`) to disable this auto-bootstrap.

Optional overrides:

```bash
DJANGO_DEV_PORT=8010 make backend-run
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

1. Run `cd extension && pnpm run prepare:runtime-config`.
2. Open `chrome://extensions` in Chrome.
3. Enable "Developer mode".
4. Click "Load unpacked" and point to the `extension/chrome` directory.
5. Confirm that the extension icon appears in the browser toolbar.

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
