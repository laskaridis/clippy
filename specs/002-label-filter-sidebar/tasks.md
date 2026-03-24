# Tasks: Label-Based Clip Filtering

**Input**: Design documents from `/specs/002-label-filter-sidebar/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**Tests**: This feature explicitly requires automated regression coverage for filter semantics, URL persistence, responsive behavior, and accessibility-critical interactions. Test tasks are included per user story.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story label (`[US1]`, `[US2]`, `[US3]`) for story-phase tasks only
- Every task includes at least one exact file path

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create shared scaffolding for label-filter feature work.

- [x] T001 Create filter-state helper module scaffold in backend/apps/clips/filtering.py
- [x] T002 [P] Add reusable label-filter test fixture helpers in backend/apps/clips/tests/helpers.py
- [x] T003 [P] Add filter sidebar/drawer mount-point containers and data attributes in backend/apps/clips/templates/clips/list.html

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data and query primitives that MUST be complete before user stories.

**⚠️ CRITICAL**: No user story implementation starts before this phase is complete.

- [x] T004 Add Label.slug field and per-user slug uniqueness constraint in backend/apps/clips/models.py
- [x] T005 Create slug backfill and constraint migration in backend/apps/clips/migrations/
- [x] T006 [P] Expose canonical label slug in API serializers and command serializers in backend/apps/clips/api/serializers.py
- [x] T007 [P] Implement repeated-label and panel-state query parsing utilities in backend/apps/clips/filtering.py
- [x] T008 Implement shared queryset builders for AND label filtering and contextual counts in backend/apps/clips/services.py
- [x] T009 [P] Add model regression tests for slug generation, uniqueness, and ownership invariants in backend/apps/clips/tests/test_models.py
- [x] T010 Wire slug-safe label creation/update behavior across web and API entry points in backend/apps/clips/views.py and backend/apps/clips/api/serializers.py

**Checkpoint**: Slug-backed filtering primitives are stable and all user stories can begin.

---

## Phase 3: User Story 1 - Filter Clips By Labels (Priority: P1) 🎯 MVP

**Goal**: Users can select one or more labels and only clips matching all selected labels are shown.

**Independent Test**: Select and de-select labels from the clips page and verify results follow AND semantics with no selected-label fallback to full list.

### Tests for User Story 1

- [x] T011 [P] [US1] Add view tests for repeated label query parameters and AND filtering in backend/apps/clips/tests/test_views.py
- [x] T012 [P] [US1] Add API tests for /api/clips/ repeated label slug filters and invalid-slug handling in backend/apps/clips/tests/test_api.py
- [x] T013 [P] [US1] Add contract-oriented assertions for /clips/ and /api/clips/ label parameter semantics in backend/apps/clips/tests/test_views.py and backend/apps/clips/tests/test_api.py

### Implementation for User Story 1

- [x] T014 [US1] Replace single UUID label filter parsing with repeated slug parsing in backend/apps/clips/views.py
- [x] T015 [US1] Implement AND label filtering for clip list API responses in backend/apps/clips/api/views.py
- [x] T016 [P] [US1] Update label links and filter controls to use repeated label slug parameters in backend/apps/clips/templates/clips/list.html
- [x] T017 [US1] Render clear empty-results state when active labels match zero clips in backend/apps/clips/templates/clips/list.html
- [x] T018 [US1] Ensure list context exposes selected label metadata needed by sidebar controls in backend/apps/clips/views.py

**Checkpoint**: User Story 1 can be validated independently as the MVP.

---

## Phase 4: User Story 2 - Preserve And Manage Filter State (Priority: P2)

**Goal**: Selected labels persist in URL, reload correctly, and can be removed via pills or clear-all actions.

**Independent Test**: Apply labels, reload or share URL, then remove labels via pills and clear-all and verify UI/results/URL remain consistent.

### Tests for User Story 2

- [x] T019 [P] [US2] Add view tests for restoring selected labels from URL and rendering selected-label pills in backend/apps/clips/tests/test_views.py
- [x] T020 [P] [US2] Add regression tests for pill removal and clear-all query-string behavior in backend/apps/clips/tests/test_views.py
- [x] T021 [P] [US2] Add API/view parity tests for graceful ignore of unknown or inaccessible slugs in backend/apps/clips/tests/test_api.py and backend/apps/clips/tests/test_views.py
- [x] T047 [P] [US2] Add regression tests for coexistence with non-label filter-group query parameters during label add/remove/clear in backend/apps/clips/tests/test_views.py and backend/apps/clips/tests/test_api.py

### Implementation for User Story 2

- [x] T022 [US2] Build selected-label pill view models and clear-all state in backend/apps/clips/views.py
- [x] T023 [US2] Render removable selected-label pills and desktop clear-all action above results in backend/apps/clips/templates/clips/list.html
- [x] T024 [US2] Implement URL mutation helpers for add/remove/clear of repeated label params in backend/apps/clips/static/clips/js/list.js
- [x] T025 [US2] Keep web and API slug-ignore behavior aligned for invalid/unowned labels in backend/apps/clips/views.py and backend/apps/clips/api/views.py
- [x] T026 [US2] Preserve non-label and future filter-group query parameters while mutating label filters in backend/apps/clips/filtering.py and backend/apps/clips/static/clips/js/list.js

**Checkpoint**: User Stories 1 and 2 both operate independently with stable shareable URLs.

---

## Phase 5: User Story 3 - Navigate Large Label Sets Efficiently (Priority: P3)

**Goal**: Users can efficiently find labels via search and expansion, and use fully accessible responsive sidebar/drawer interactions.

**Independent Test**: Validate show-more, search, selected-first ordering, panel persistence, and small-screen drawer accessibility at widths <=1024px.

### Tests for User Story 3

- [x] T027 [P] [US3] Add view tests for selected-first ordering, alphabetical remainder, and default visible-limit behavior in backend/apps/clips/tests/test_views.py
- [x] T028 [P] [US3] Add API tests for `/api/labels` flat catalog response (`name`, `slug`, `color`) and ignored legacy params (`label`, `limit`, `expanded`) in backend/apps/clips/tests/test_api.py
- [x] T029 [P] [US3] Add regression tests for panel query-state persistence (expanded/collapsed/open/closed) in backend/apps/clips/tests/test_views.py
- [x] T030 [P] [US3] Add template/accessibility assertions mapped to the Accessibility Verification Checklist (keyboard flow, focus return, accessible naming/state, truncation semantics, and no-horizontal-scroll) in backend/apps/clips/tests/test_views.py
- [x] T043 [P] [US3] Add tests verifying the small-screen Filters trigger displays selected-label count and updates after select, de-select, and Clear all in backend/apps/clips/tests/test_views.py
- [x] T045 [P] [US3] Add accessibility tests ensuring truncated drawer labels and selected pills expose full label text to assistive technologies in backend/apps/clips/tests/test_views.py

### Implementation for User Story 3

- [x] T031 [US3] Implement web-only label dataset pipeline (flat labels + color + contextual counts), with selection/ordering handled in UI, in backend/apps/clips/services.py
- [x] T032 [US3] Simplify `/api/labels` to a selection-agnostic flat catalog response (`name`, `slug`, `color`) in backend/apps/clips/api/views.py and backend/apps/clips/api/serializers.py
- [x] T033 [US3] Add desktop sidebar collapse/expand controls and panel-state wiring in backend/apps/clips/templates/clips/list.html
- [x] T034 [US3] Add small-screen filters trigger, off-canvas drawer, drawer close actions, and drawer clear-all action in backend/apps/clips/templates/clips/list.html
- [x] T044 [US3] Render and synchronize selected-label count in the small-screen Filters trigger in backend/apps/clips/templates/clips/list.html and backend/apps/clips/static/clips/js/list.js
- [x] T035 [US3] Implement drawer open/close, Escape/backdrop dismissal, focus return, and no-auto-close-on-select behavior in backend/apps/clips/static/clips/js/list.js
- [x] T036 [US3] Implement label search, show-more toggle, and selected-label priority rendering behavior in backend/apps/clips/static/clips/js/list.js
- [x] T037 [US3] Add responsive and accessibility-focused styles for drawer, sidebar, one-line ellipsis labels/pills, and focus-visible states in backend/apps/clips/static/clips/css/list.css
- [x] T046 [US3] Ensure truncated drawer labels and selected pills expose full text via accessible naming and metadata in backend/apps/clips/templates/clips/list.html and backend/apps/clips/static/clips/js/list.js
- [x] T038 [US3] Persist filter panel state in query string without mutating label selections in backend/apps/clips/views.py and backend/apps/clips/static/clips/js/list.js

**Checkpoint**: All three user stories are independently functional and accessible across breakpoints.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final hardening, documentation alignment, and release readiness.

- [ ] T039 [P] Validate end-to-end quickstart scenarios and update verification notes in specs/002-label-filter-sidebar/quickstart.md
- [ ] T040 [P] Update implementation plan progress and final decisions in specs/002-label-filter-sidebar/plan.md
- [ ] T041 Run full clips regression suite for models, views, and APIs in backend/apps/clips/tests/test_models.py, backend/apps/clips/tests/test_views.py, and backend/apps/clips/tests/test_api.py
- [ ] T042 Update deferred or resolved feature debt entries in docs/TECH_DEBT_BACKLOG.md
- [ ] T048 [P] Add measurable validation protocol for SC-001 and SC-004 (dataset, timing method, and acceptance recording) in specs/002-label-filter-sidebar/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies; start immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2.
- **Phase 4 (US2)**: Depends on Phase 2 and uses US1 filter primitives.
- **Phase 5 (US3)**: Depends on Phase 2 and builds on US1/US2 filter state behavior.
- **Phase 6 (Polish)**: Depends on completion of selected user stories.

### User Story Dependencies

- **US1 (P1)**: Independent after Foundational phase.
- **US2 (P2)**: Independent after Foundational phase but integrates with US1 filter context.
- **US3 (P3)**: Independent after Foundational phase but composes with US1/US2 URL and state behavior.

### Within Each User Story

- Write tests first and confirm they fail before implementation.
- Implement backend query/state logic before template and JS integration.
- Finalize responsive/accessibility behavior before closing story checkpoints.

---

## Parallel Opportunities

- Phase 1: T002 and T003 can run in parallel after T001.
- Phase 2: T006, T007, and T009 can run in parallel after T004/T005.
- US1: T011-T013 can run in parallel; T016 can run in parallel with T014/T015 once context contract is clear.
- US2: T019-T021 and T047 can run in parallel; T023 and T024 can run in parallel after T022.
- US3: T027-T030 plus T043 and T045 can run in parallel; T035-T037 plus T044 and T046 can run in parallel after T033/T034 and T031/T032 are in place.
- Polish: T039, T040, and T048 can run in parallel before T041/T042 wrap-up.

---

## Parallel Example: User Story 1

- Task T011 [P] [US1] Add view tests for repeated label query parameters and AND filtering in backend/apps/clips/tests/test_views.py
- Task T012 [P] [US1] Add API tests for /api/clips/ repeated label slug filters and invalid-slug handling in backend/apps/clips/tests/test_api.py
- Task T013 [P] [US1] Add contract-oriented assertions for /clips/ and /api/clips/ label parameter semantics in backend/apps/clips/tests/test_views.py and backend/apps/clips/tests/test_api.py

## Parallel Example: User Story 2

- Task T019 [P] [US2] Add view tests for restoring selected labels from URL and rendering selected-label pills in backend/apps/clips/tests/test_views.py
- Task T020 [P] [US2] Add regression tests for pill removal and clear-all query-string behavior in backend/apps/clips/tests/test_views.py
- Task T021 [P] [US2] Add API/view parity tests for graceful ignore of unknown or inaccessible slugs in backend/apps/clips/tests/test_api.py and backend/apps/clips/tests/test_views.py
- Task T047 [P] [US2] Add regression tests for coexistence with non-label filter-group query parameters during label add/remove/clear in backend/apps/clips/tests/test_views.py and backend/apps/clips/tests/test_api.py

## Parallel Example: User Story 3

- Task T027 [P] [US3] Add view tests for selected-first ordering, alphabetical remainder, and default visible-limit behavior in backend/apps/clips/tests/test_views.py
- Task T028 [P] [US3] Add API tests for `/api/labels` flat catalog response (`name`, `slug`, `color`) and ignored legacy params (`label`, `limit`, `expanded`) in backend/apps/clips/tests/test_api.py
- Task T029 [P] [US3] Add regression tests for panel query-state persistence (expanded/collapsed/open/closed) in backend/apps/clips/tests/test_views.py
- Task T030 [P] [US3] Add template/accessibility assertions mapped to the Accessibility Verification Checklist (keyboard flow, focus return, accessible naming/state, truncation semantics, and no-horizontal-scroll) in backend/apps/clips/tests/test_views.py
- Task T043 [P] [US3] Add tests verifying the small-screen Filters trigger displays selected-label count and updates after select, de-select, and Clear all in backend/apps/clips/tests/test_views.py
- Task T045 [P] [US3] Add accessibility tests ensuring truncated drawer labels and selected pills expose full label text to assistive technologies in backend/apps/clips/tests/test_views.py

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1 and Phase 2.
2. Deliver Phase 3 (US1).
3. Validate US1 independently against its test criteria before moving on.

### Incremental Delivery

1. Ship MVP with US1 filtering.
2. Add US2 URL persistence and removal ergonomics.
3. Add US3 large-list navigation and responsive accessibility behaviors.
4. Complete Polish phase for release readiness.

### Parallel Team Strategy

1. One developer owns backend filtering and model/migration work (T004-T010, T014-T015, T031-T032, T038).
2. One developer owns template and CSS work (T003, T016-T017, T023, T033-T034, T037, T044, T046).
3. One developer owns JS interactions and URL-state synchronization (T024, T035-T036, T044, T046).
4. QA-focused developer executes test phases and polish validation (T011-T013, T019-T021, T027-T030, T039-T043, T045, T047-T048).

---

## Notes

- All tasks use strict checklist format with task IDs and explicit paths.
- Story labels appear only in user story phases.
- The first recommended implementation slice for a fast MVP is Phase 3 (US1) after Foundational completion.
