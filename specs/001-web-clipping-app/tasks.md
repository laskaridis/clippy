# Tasks: Web Clipping and Reference Application

**Input**: Design documents from `specs/001-web-clipping-app/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- All descriptions include at least one exact file path

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize repository structure and core directories so later phases have a consistent layout.

- [x] T001 Create Django project skeleton for backend in backend/manage.py and backend/webclippings/settings.py
- [x] T002 [P] Create feature app scaffolds in backend/apps/clips/__init__.py and backend/apps/accounts/__init__.py
- [x] T003 [P] Create backend test directory structure in backend/tests/unit/__init__.py, backend/tests/api/__init__.py, and backend/tests/integration/__init__.py
- [x] T004 [P] Create Chrome extension skeleton directories and placeholder files in extension/chrome/manifest.json and extension/chrome/src/content/clipper.js
- [x] T005 [P] Create infrastructure directory skeleton in infra/docker/README.md, infra/k8s/README.md, and infra/ci/github/README.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend infrastructure that MUST be complete before any user story implementation.

**⚠️ CRITICAL**: No user story work (US1–US3) can begin until this phase is complete.

- [x] T006 Configure PostgreSQL database settings and environment-based configuration in backend/webclippings/settings.py
- [x] T007 [P] Configure Django authentication setup (including accounts app registration and AUTH_USER_MODEL if customized) in backend/webclippings/settings.py and backend/apps/accounts/apps.py
- [x] T008 [P] Implement core data models for Clip, Label, and ClipLabel in backend/apps/clips/models.py according to specs/001-web-clipping-app/data-model.md
- [x] T009 Generate and apply initial Django migrations for clips and labels using backend/manage.py and migration files under backend/apps/clips/migrations/
- [x] T010 Configure base URL routing for API and web UI in backend/webclippings/urls.py including includes for backend/apps/clips/urls.py and backend/apps/accounts/urls.py
- [x] T011 Configure basic logging and 12-factor environment handling (DJANGO_SECRET_KEY, DATABASE_URL, ALLOWED_HOSTS) in backend/webclippings/settings.py

**Checkpoint**: Backend foundation ready – safe to start user story implementation.

---

## Phase 3: User Story 1 - Capture and revisit a clipping (Priority: P1) 🎯 MVP

**Goal**: A signed-in user can capture selected text from a webpage via the Chrome extension and later see that clipping in the web app with capture time and a link back to the original page.

**Independent Test**: With only this story implemented (plus Setup and Foundational phases), a user can sign in, capture a clipping from Chrome, and see it listed and viewable in the web application.

### Implementation for User Story 1

- [x] T012 [P] [US1] Implement Clip REST API (create, list, retrieve) in backend/apps/clips/api/serializers.py and backend/apps/clips/api/views.py following specs/001-web-clipping-app/contracts/openapi.yaml
- [x] T013 [US1] Add API routing for Clip endpoints under /api/clips/ and /api/clips/{id}/ in backend/apps/clips/urls.py and backend/webclippings/urls.py
- [x] T014 [P] [US1] Implement server-rendered clip list and detail views in backend/apps/clips/views.py and templates/clips/list.html and templates/clips/detail.html
- [x] T015 [US1] Add navigation entry point for "My clips" in a base template such as backend/webclippings/templates/base.html linking to templates/clips/list.html
- [x] T016 [P] [US1] Implement Chrome content script to capture selected text, page title, and URL in extension/chrome/src/content/clipper.js
 - [x] T017 [P] [US1] Implement Chrome background script to send POST /api/clips/ requests to the backend in extension/chrome/src/background/clip_sender.js
 - [x] T018 [US1] Implement minimal Chrome popup UI to trigger clipping and show success/failure in extension/chrome/src/popup/popup.js and extension/chrome/src/popup/popup.html
- [x] T019 [US1] Ensure authenticated session between web app and extension (sign-in via backend/apps/accounts/views.py and use of same-domain cookies in extension/chrome/src/background/clip_sender.js)
 - [ ] T036 [US1] Ensure delete operations on clips are fully implemented and wired in the web UI, removing deleted clips from all lists and searches in backend/apps/clips/api/views.py, backend/apps/clips/views.py, and templates/clips/list.html
 - [ ] T040 [P] Add targeted tests for the Chrome extension’s request payloads and offline queueing behavior in extension/chrome/tests/test_extension_flows.js

**Checkpoint**: User Story 1 is fully functional and independently testable (capture from Chrome, view in web app).

---

## Phase 4: User Story 2 - Organize clippings with labels (Priority: P2)

**Goal**: A user can optionally add, edit, and remove labels on clippings and later filter by those labels in the web application.

**Independent Test**: With this story plus Setup and Foundational phases, a user can create labels, assign them to clippings, change label assignments, and see filtered lists of clippings by label, even if search-by-text or grouping by website is not yet implemented.

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement label CRUD REST API (list, create, update, delete) in backend/apps/clips/api/serializers.py and backend/apps/clips/api/views.py following specs/001-web-clipping-app/contracts/openapi.yaml
- [ ] T021 [US2] Add API routing for Label endpoints under /api/labels/ and /api/labels/{id}/ in backend/apps/clips/urls.py and backend/webclippings/urls.py
- [ ] T022 [P] [US2] Enforce per-user label uniqueness and Clip–Label relationships in backend/apps/clips/models.py consistent with specs/001-web-clipping-app/data-model.md
- [ ] T023 [US2] Add web UI for viewing and editing labels associated with a clip in templates/clips/detail.html and form handling in backend/apps/clips/views.py
- [ ] T024 [P] [US2] Add a simple "Labels" management page (list and create/update/delete) in backend/apps/clips/views.py and templates/clips/labels.html
- [ ] T025 [US2] Extend Chrome popup to allow specifying label names when creating a clip in extension/chrome/src/popup/popup.js so labels are sent in the POST /api/clips/ payload

**Checkpoint**: User Stories 1 and 2 both work independently (capture/revisit and label organization).

---

## Phase 5: User Story 3 - Browse and search clippings by label or website (Priority: P3)

**Goal**: A user can quickly find clippings by searching text, filtering by label, and grouping or filtering by source website in the web application.

**Independent Test**: With this story plus Setup and Foundational phases, a user with many clippings can reliably locate a specific clipping using search and filters without needing label editing or extension changes to be reimplemented.

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement query parameters q, label, domain, and date-range (for example, from/to capture dates) on the Clip list API in backend/apps/clips/api/views.py as described in specs/001-web-clipping-app/contracts/openapi.yaml
- [ ] T027 [US3] Add search input and label/domain/date-range filter controls to the clip list template in templates/clips/list.html and corresponding handling in backend/apps/clips/views.py
- [ ] T028 [P] [US3] Implement grouping or display of clippings by source website (domain) in templates/clips/list.html using the domain field from backend/apps/clips/models.py
- [ ] T029 [US3] Ensure default ordering (most recent first) and reasonable pagination or limit behavior in backend/apps/clips/api/views.py and templates/clips/list.html to satisfy specs/001-web-clipping-app/spec.md success criteria

**Checkpoint**: All three user stories are independently functional and provide end-to-end value.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Hardening, operations, and deployment readiness that affect multiple user stories.

- [ ] T030 [P] Add Dockerfile for the Django app in infra/docker/Dockerfile and ensure it runs backend/manage.py commands correctly
- [ ] T031 [P] Add docker-compose.yml for local orchestration of backend and PostgreSQL in infra/docker/docker-compose.yml aligned with specs/001-web-clipping-app/quickstart.md
- [ ] T032 [P] Add GitHub Actions CI workflow to run tests and build Docker images in .github/workflows/ci.yml
- [ ] T033 Implement structured logging and basic request/clip event metrics in backend/webclippings/settings.py and any logging helpers in backend/webclippings/logging.py
- [ ] T034 [P] Add high-level API and extension contract checks for core journeys in tests/contract/test_clips_contract.py, including filtered searches (by label, domain, and date range) and deletion flows
- [ ] T035 Validate implementation against success criteria SC-001–SC-005 and update specs/001-web-clipping-app/spec.md and specs/001-web-clipping-app/quickstart.md where behavior differs
 - [ ] T041 [P] Add end-to-end tests for the “clip → persist → search (including time range) → open original → delete” journey in backend/tests/integration/test_core_journeys.py
 - [ ] T037 [US1] Add a simple user-facing help or “How it works” page describing how to install/use the Chrome extension, how to find clippings (including filters and time range), and how to delete clippings or manage labels in backend/apps/clips/views.py and templates/help.html
 - [ ] T038 [P] [US1] Implement basic offline queueing for clipping requests in extension/chrome/src/background/clip_sender.js so that clippings attempted while offline are retried when connectivity returns
 - [ ] T039 [US2] Ensure label list UI and API surface the per-label clip_count (number of clippings associated with each label) in backend/apps/clips/api/serializers.py, backend/apps/clips/views.py, and templates/clips/labels.html

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies – must complete before Foundational work that assumes the directory layout.
- **Foundational (Phase 2)**: Depends on Setup – configures Django, Postgres, models, and routing; **blocks all user stories** until complete.
- **User Story 1 (Phase 3)**: Depends on Foundational – can start only after T006–T011 are done.
- **User Story 2 (Phase 4)**: Depends on Foundational – can start after Phase 2 and, ideally, after core Clip API from T012–T013 exists.
- **User Story 3 (Phase 5)**: Depends on Foundational – can start once Clip list endpoints (T012–T013) and label support (T020–T022) exist, but does not require Chrome extension changes.
- **Polish (Phase 6)**: Depends on all required user stories (at least US1 as MVP, optionally US2–US3) being complete.

### User Story Dependencies

- **US1 (P1)**: Independent once backend foundation is in place; provides the core "clip and revisit" journey.
- **US2 (P2)**: Builds on US1 data model but is independently testable: label management and label-based filtering work even if search-by-text is not implemented.
- **US3 (P3)**: Builds on US1 and US2 data and APIs but is independently testable: search and grouping features can be evaluated with pre-existing clips and labels.

### Within Each User Story

- Complete backend model and API changes before UI or extension changes that depend on them (e.g., T012 before T016–T018; T020–T022 before T023–T025; T026 before T027–T029).
- Avoid cross-story coupling in code: keep US1 behaviors working even if US2+US3 are not yet implemented.
- Use Phase 6 tasks only after user-story-specific behavior is stable.

---

## Parallel Opportunities

- **Setup**: T002–T005 can be done in parallel after T001 establishes the backend project.
- **Foundational**: T007–T008 and T010–T011 can run in parallel as long as they coordinate changes in backend/webclippings/settings.py and backend/apps/clips/models.py.
- **User Story 1**: T012, T014, T016, T017, and T018 can largely proceed in parallel once T010 has established routing; developers should coordinate on shared files (e.g., backend/apps/clips/api/views.py and templates/clips/list.html).
- **User Story 2**: T020, T022, and T024–T025 can be parallelized as long as model and API contracts are agreed upfront.
- **User Story 3**: T026 and T028 can proceed in parallel, with T027 and T029 depending on basic API behavior.
- **Polish**: T030–T034 are excellent parallel tasks across different parts of the stack (Docker, CI, logging, contract tests).

---

## Parallel Example: User Story 1

Example of safe parallelization once Phase 2 (Foundational) is complete:

- Run in parallel:
  - Task T012 [P] [US1] Implement Clip REST API in backend/apps/clips/api/serializers.py and backend/apps/clips/api/views.py
  - Task T014 [P] [US1] Implement server-rendered clip list and detail views in backend/apps/clips/views.py and templates/clips/list.html and templates/clips/detail.html
  - Task T016 [P] [US1] Implement Chrome content script in extension/chrome/src/content/clipper.js
  - Task T017 [P] [US1] Implement Chrome background script in extension/chrome/src/background/clip_sender.js

After those tasks complete:

- Finish T013 (routing) and T018–T019 (popup UI and auth wiring) to integrate all pieces into a single, testable flow.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup) and Phase 2 (Foundational).
2. Implement Phase 3 (User Story 1) tasks T012–T019.
3. Manually verify that a user can clip text from Chrome and see it in the web app.
4. Optionally implement only the most essential Polish tasks (e.g., T030–T032) before first external demo.

### Incremental Delivery

1. **MVP**: Phases 1–3 (US1) – deliver capture and revisit.
2. **Iteration 2**: Phase 4 (US2) – deliver label organization while keeping US1 intact.
3. **Iteration 3**: Phase 5 (US3) – deliver search and grouping without breaking US1–US2.
4. **Hardening**: Phase 6 – Dockerization, CI/CD, logging, and contract checks.

### Parallel Team Strategy

With multiple developers:

- Developer A focuses on backend tasks (T006–T013, T020–T022, T026–T029, T030–T031, T033–T035).
- Developer B focuses on web UI templates and views (T014–T015, T023–T024, T027–T029).
- Developer C focuses on the Chrome extension (T004, T016–T018, T025).
- A fourth developer can focus on infra and CI/CD (T005, T030–T032, T034).

Each developer can work largely independently as long as API contracts from specs/001-web-clipping-app/contracts/openapi.yaml and data rules from specs/001-web-clipping-app/data-model.md remain the single source of truth.
