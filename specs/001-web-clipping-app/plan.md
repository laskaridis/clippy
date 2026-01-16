# Implementation Plan: Web Clipping and Reference Application

**Branch**: `001-web-clipping-app` | **Date**: 2026-01-16 | **Spec**: [specs/001-web-clipping-app/spec.md](specs/001-web-clipping-app/spec.md)
**Input**: Feature specification from `specs/001-web-clipping-app/spec.md`

**Note**: This plan is maintained by the `/speckit.plan` workflow and should stay in sync with the feature spec, research, and contracts.

## Summary

Build an end-to-end WebClippings MVP consisting of a Chrome extension, a Django + Django REST Framework backend, and a simple web UI that lets signed-in users capture selected text from web pages, store it as clips, organize clips with labels, and search or filter by label, website, and time range.

For user convenience, the clip creation API (`POST /api/clips/`) accepts optional labels in the same request: the client may send an array of label names, and the backend will associate existing labels for that user or implicitly create new labels when names do not yet exist. Labels remain editable later via clip update and label management endpoints.

## Technical Context

**Language/Version**: Python 3.11+ (targeting 3.12 where available), JavaScript for the Chrome extension  
**Primary Dependencies**: Django 5.x, Django REST Framework, Django auth/session middleware, Jest (or equivalent) for extension tests  
**Storage**: PostgreSQL as primary datastore; Django ORM models for `User`, `Clip`, `Label`, and `ClipLabel`  
**Testing**: Django/pytest-style tests for models, APIs, and search/filter behavior; JavaScript unit tests for extension content/background scripts and configuration helpers; contract tests aligned with `contracts/openapi.yaml`  
**Target Platform**: Linux server (or containerized environment) for backend + PostgreSQL; Google Chrome (current stable) for the extension; modern desktop browsers for the web UI  
**Project Type**: Web application with backend API, Chrome extension frontend, and minimal server-rendered web UI  
**Performance Goals**: For typical users (up to ~1,000 clips), list and search responses should complete within ≈2 seconds end-to-end (browser to rendered UI) in line with success criteria SC-005  
**Constraints**: Keep architecture to a single Django project + PostgreSQL + Chrome extension; avoid additional services unless required. Extension must minimize permissions and handle intermittent connectivity (queueing clip requests client-side when offline).  
**Scale/Scope**: Initial focus on single-user experience with private clips; design data model and API so that scaling to tens of thousands of users and higher clip counts primarily affects indexing and infrastructure, not feature semantics.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Simplicity & Architecture**: The plan keeps to the constitution’s baseline architecture: a single Django backend (including web UI and API), PostgreSQL for storage, and a Chrome extension as the primary capture surface. Allowing labels to be provided in the same API request as clip creation does not add new components; it is implemented as logic in the existing clip serializer/service that upserts label records as needed.
- **Engineering Quality & Testing**: Core journeys (clip via extension → `POST /api/clips/` with optional labels → persistence and label upsert → listing/searching clips by label or domain) will be covered by Django tests exercising the API contract, plus JavaScript tests ensuring the extension builds the correct payload. CI via GitHub Actions will run these tests on each change.
- **Consistent UX**: The term "label" is used consistently across spec, backend API (e.g., `labels` field accepting label names), web UI, and extension. The behavior that labels can be added during creation or later edit is documented in the spec and quickstart; there is no separate "tag" concept.
- **Security & Privacy**: All clip and label operations are scoped to the authenticated user. Session-based auth and CSRF protections are reused for both the web UI and the extension. Label-on-create behavior enforces that labels are always created within the user’s own namespace; no cross-user sharing is introduced. Logging avoids storing sensitive clip content while still recording key events.

## Project Structure

### Documentation (this feature)

```text
specs/001-web-clipping-app/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output: runtime, API style, storage, CI
├── data-model.md        # Phase 1 output: User, Clip, Label, ClipLabel
├── quickstart.md        # Phase 1 output: how to run backend + extension
├── contracts/           # Phase 1 output: OpenAPI contract for auth, clips, labels
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── manage.py
├── db.sqlite3                 # Local dev DB (PostgreSQL planned for cloud)
├── apps/
│   ├── accounts/              # Authentication and login views
│   └── clips/                 # Clip and label models, APIs, and templates
│       ├── api/               # DRF serializers, viewsets, API URLs
│       ├── migrations/
│       ├── templates/clips/   # Basic list/detail views
│       └── tests/             # Django tests for models, views, and API
└── webclippings/              # Django project settings, URLs, WSGI/ASGI

extension/
├── package.json               # JS tooling and tests for the extension
├── chrome/
│   ├── manifest.json
│   └── src/
│       ├── api/               # clipClient and related helpers
│       ├── background/        # context menu + message handling
│       ├── content/           # selection capture and messaging
│       └── popup/             # popup UI scripts and HTML
└── shared/                    # Shared config, error handling, and messages

infra/
└── ci/                        # CI and infrastructure docs and (later) configs
```

**Structure Decision**: Treat `backend/` as the single Django project hosting both the web UI and REST API, with the `clips` app responsible for clip and label persistence and search. The `extension/` directory contains the Chrome extension that talks to the backend via the documented API, including sending labels in the clip creation payload. `specs/` and `infra/` hold design docs and deployment/CI assets, respectively.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | N/A | N/A |
