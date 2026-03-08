# Implement Quick Search with PostgreSQL Full-Text and Trigram Ranking

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

After this change, an authenticated user can type into one free-text input on the clips page and immediately see at most five top relevant results grouped as clipped text hits, label hits, and website hits. Results update while the user types. Website hits are based on the exact stored clip URL path (`Clip.url` exact value), not only by domain. Clicking a clipped text result opens the clip detail page, clicking a label result opens the clips list filtered by that label UUID, and clicking a website result opens the clips list filtered by that exact URL.

This feature is intentionally scoped to the web UI and backend for now. The browser extension is out of scope for this feature.

A reviewer can verify behavior by signing in with sample data, typing valid queries, seeing grouped live results, and confirming each result link lands on the expected destination.

## Progress

- [x] (2026-02-28 11:41Z) Created initial ExecPlan with architecture, API/UI flow, tests, acceptance checks, and recovery guidance.
- [x] (2026-02-28 12:01Z) Revised plan constraints from stakeholder feedback: exact URL matching, query validation rules, latency target, accessibility requirements, label UUID filtering, and explicit web-only scope.
- [x] (2026-02-28 12:08Z) Selected Option 2 tech direction: PostgreSQL full-text + trigram search for ranking and performance.
- [x] (2026-02-28 12:19Z) Added `Label.uuid`, created migration `0002_label_uuid_quick_search_support`, added `(user, url)` clip index, and added PostgreSQL `pg_trgm` + trigram/FTS index setup in migration hooks.
- [x] (2026-02-28 12:29Z) Implemented `apps.clips.services.quick_search` with strict decoded-query validation, user-scoped clip/label/exact-url candidate generation, PostgreSQL ranking, deterministic tie-breaks, and global top-five grouping.
- [x] (2026-02-28 12:34Z) Added Milestone 1 tests (`test_models` + new `test_quick_search`) and validated them on both SQLite and PostgreSQL.
- [x] (2026-02-28 12:37Z) Ran full backend regression (`python manage.py test`) on both SQLite and PostgreSQL after Milestone 1 changes.
- [x] (2026-03-08 12:10Z) Implemented Milestone 2 API endpoint (`GET /api/clips/quick-search/`), serializer validation, URL wiring, and OpenAPI contract updates.
- [ ] Add web quick-search input, dynamic grouped results, and accessibility behavior.
- [x] (2026-03-08 12:10Z) Added/updated backend API tests for Milestone 2 behavior: 401 auth guard, 400 invalid `q`, user scoping, grouped `hits` keys, and max-five cap; added regression coverage for encoded whitespace rejection and literal percent-escape preservation.
- [ ] Add or update backend tests for web milestone behavior (remaining: Milestone 3 web/filter coverage).
- [x] (2026-03-08 12:10Z) Ran Milestone 2 validation commands in PostgreSQL-backed runtime: `python manage.py test apps.clips.tests.test_api`, `python manage.py test apps.clips.tests.test_quick_search apps.clips.tests.test_api`, and full `python manage.py test`.
- [x] (2026-02-28 12:34Z) Updated living sections with implementation progress, decisions, and observed surprises.

## Surprises & Discoveries

- Observation: The repository does not currently contain `specs/001-quick-search/spec.md`; the latest tracked spec is `specs/001-web-clipping-app/spec.md`.
  Evidence: `find specs -maxdepth 3 -type f` lists only `specs/001-web-clipping-app/*` files.

- Observation: `Label` currently uses an integer primary key and does not expose a UUID identifier.
  Evidence: `backend/apps/clips/models.py` defines `Label` without a UUID field.

- Observation: `docs/plans/` existed with no prior plans; this feature is the first tracked plan there.
  Evidence: `ls -la docs/plans` previously returned only `.` and `..`.

- Observation: `makemigrations` cannot run non-interactively when adding a unique UUID field with callable default directly, so the UUID rollout required a two-phase migration.
  Evidence: `python manage.py makemigrations clips` prompted for interactive selection and raised `EOFError` in non-interactive execution.

- Observation: Docker CLI is available locally, but Docker daemon is not running; PostgreSQL verification required a local `initdb`/`pg_ctl` instance instead of a container.
  Evidence: `docker run ...` failed with `Cannot connect to the Docker daemon at unix:///var/run/docker.sock`.

- Observation: Django detected an index-name drift for the new `(user, url)` index until the model declared an explicit name matching the migration.
  Evidence: `python manage.py makemigrations --check --dry-run` initially proposed `0003_rename_clips_clip_user_id_3effdd_idx...` before model index naming was aligned.

## Decision Log

- Decision: Return at most five results total across all hit types, then group selected items by type in response and UI.
  Rationale: The feature requires both grouped presentation and a single global top-five cap.
  Date/Author: 2026-02-28 / Codex

- Decision: Treat website hits as exact URL matches based on stored `Clip.url` values (including path), not domain-only aggregation.
  Rationale: Stakeholder clarified that website results must represent exact URL path matches.
  Date/Author: 2026-02-28 / Codex

- Decision: Enforce query validation as: URL-encoded input, no whitespace, minimum length 3, maximum length 50.
  Rationale: Stakeholder-provided input contract and security hardening.
  Date/Author: 2026-02-28 / Codex

- Decision: Filter clips by label UUID in navigation URLs (`/clips?label=<uuid>`), which requires adding a UUID field to `Label`.
  Rationale: Stakeholder selected UUID-based label filters.
  Date/Author: 2026-02-28 / Codex

- Decision: Accessibility requirements are first-class for this feature (keyboard support, semantic roles, screen-reader feedback).
  Rationale: Stakeholder explicitly prioritized accessibility.
  Date/Author: 2026-02-28 / Codex

- Decision: Feature scope is backend + web UI only; extension changes and extension tests are out of scope for this milestone.
  Rationale: Stakeholder constrained scope to web retrieval only.
  Date/Author: 2026-02-28 / Codex

- Decision: Performance target is p56 response time <= 500ms for quick-search endpoint under representative local dataset conditions.
  Rationale: Stakeholder-specified non-functional target.
  Date/Author: 2026-02-28 / Codex

- Decision: Use PostgreSQL-native search features (`SearchVector`, `SearchRank`, `TrigramSimilarity`, and GIN indexes) as the primary implementation approach for quick-search.
  Rationale: Stakeholder selected Option 2 for stronger relevance and performance while staying within Django/DRF architecture.
  Date/Author: 2026-02-28 / Codex

- Decision: Treat PostgreSQL as required for environments where this feature is validated and released (local implementation/testing and non-local deployments).
  Rationale: Option 2 depends on PostgreSQL capabilities that SQLite does not provide.
  Date/Author: 2026-02-28 / Codex

- Decision: Implement `Label.uuid` with a two-phase migration (`null=True` add, data backfill, then `unique=True` + non-null default) instead of a single direct unique-add migration.
  Rationale: Avoided unsafe/interactive migration generation behavior and ensured deterministic backfill for existing rows.
  Date/Author: 2026-02-28 / Codex

- Decision: Create PostgreSQL search prerequisites (extension and trigram/FTS indexes) via vendor-guarded migration functions.
  Rationale: Kept SQLite-based local test flows functional while enabling required PostgreSQL optimizations where supported.
  Date/Author: 2026-02-28 / Codex

- Decision: Keep a non-PostgreSQL fallback path in `quick_search` while preserving PostgreSQL full-text/trigram ranking as the primary path.
  Rationale: Maintains repo-wide testability in default SQLite setups without changing the production/stakeholder PostgreSQL direction.
  Date/Author: 2026-02-28 / Codex

## Outcomes & Retrospective

Milestone 1 and Milestone 2 are implemented and validated. Completed scope now includes label UUID support, migration-level PostgreSQL search prerequisites, reusable quick-search service behavior, and authenticated API delivery at `GET /api/clips/quick-search/` with strict input validation and OpenAPI-aligned grouped results. Milestone 2 review feedback was incorporated by centralizing query decoding behavior (avoiding duplicate decode paths) and adding regression coverage for encoded whitespace rejection and literal percent-escape query preservation. Remaining work is Milestone 3 (web UX/accessibility and list filters), with the main follow-on risk being API/UI contract drift during frontend integration.

## Context and Orientation

The backend is a Django modular monolith and clipping logic lives in `backend/apps/clips/`. Current web retrieval is `ClipListView` in `backend/apps/clips/views.py` with template `backend/apps/clips/templates/clips/list.html`. Current API endpoints are in `backend/apps/clips/api/views.py` and enforce ownership through `get_queryset()` scoped to `request.user`.

`backend/webclippings/settings.py` already supports PostgreSQL through `DATABASE_URL` and falls back to SQLite when unset. This plan uses PostgreSQL mode for quick-search implementation and verification so full-text and trigram behavior is available.

`Clip` already stores full URL values in `Clip.url`. `Label` currently has an integer primary key and no UUID identifier; this plan adds a UUID field for stable user-facing filter URLs.

For this plan, “quick search” means a debounced client-side query loop that calls a backend endpoint while typing and renders grouped, clickable suggestions without full page reload.

Key files in scope:

`backend/apps/clips/models.py` (add label UUID field and search indexes where applicable), `backend/apps/clips/migrations/*` (new migration including Postgres extension/index setup), `backend/apps/clips/services.py` (search service using `django.contrib.postgres.search`), `backend/apps/clips/api/views.py` and `backend/apps/clips/api/serializers.py` (endpoint + validation), `backend/apps/clips/api/urls.py` (route), `backend/apps/clips/views.py` (label/url filtering in list view), `backend/apps/clips/templates/clips/list.html` (search UI + accessibility wiring), and `specs/001-web-clipping-app/contracts/openapi.yaml` (contract update).

## Milestones

### Milestone 1: Data model update and backend quick-search service

At the end of this milestone, labels expose a UUID field for URL-safe filtering, and the backend has a reusable service that returns grouped top-five search hits scoped to one user.

Implementation narrative: add `uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)` to `Label` in `backend/apps/clips/models.py` and create a migration. In the same milestone, add PostgreSQL search prerequisites in migrations (including `pg_trgm` extension enablement and appropriate GIN/trigram indexes for queryable clip/label text). Implement `quick_search` in `backend/apps/clips/services.py` to evaluate clip hits, label hits, and exact URL hits from only the current user’s data using `SearchVector`/`SearchRank` and `TrigramSimilarity`, with deterministic tie-breaks. Website hits should be grouped by exact `Clip.url` value and carry a clip count for that exact URL.

The service must enforce query constraints before searching: after URL decoding, reject any whitespace, reject length <3, reject length >50.

Acceptance for this milestone: model tests confirm label UUID uniqueness and migration success on PostgreSQL; service tests confirm user scoping, max-five global cap, exact URL grouping behavior, deterministic ordering, and validation failures for invalid `q` values.

### Milestone 2: API endpoint, validation, and contract

At the end of this milestone, authenticated clients can call a quick-search endpoint and receive grouped JSON results aligned with OpenAPI.

Implementation narrative: add `GET /api/clips/quick-search/?q=<query>` in `backend/apps/clips/api/views.py` and `backend/apps/clips/api/urls.py`. Keep the view thin: validate query via serializer, call service, return a `hits` payload grouped by result type. Validation rules are mandatory and explicit: `q` required, URL-encoded by client, no whitespace allowed, minimum 3 chars, maximum 50 chars. Invalid input returns HTTP 400 with actionable validation text. Ensure ranking fields exposed by the API are derived from the PostgreSQL search query path (not re-ranked in Python without reason).

Acceptance for this milestone: API tests confirm 401 for anonymous requests, 400 for invalid `q`, user-scoped results only, `hits` keys (`clips`, `labels`, `websites`), and max five total hits.

### Milestone 3: Web quick-search UX, accessibility, and navigation filters

At the end of this milestone, the clips page has a live quick-search experience with accessibility behavior and correct click-through destinations.

Implementation narrative: update `backend/apps/clips/templates/clips/list.html` to add a search input and grouped result panel. Use debouncing (~200ms), stale-request cancellation (`AbortController`), and `encodeURIComponent` when building `q` requests. If input is invalid (contains whitespace, <3 chars, >50 chars), skip request and show inline accessible guidance.

Accessibility requirements in this milestone:

- Keyboard navigation for results (`ArrowDown`, `ArrowUp`, `Enter`, `Escape`).
- Focus management that keeps tab order predictable.
- Semantic labeling (`role`, `aria-expanded`, `aria-controls`, and status announcements for result count changes).
- No color-only state signaling.

Update `ClipListView.get_queryset()` to support:

- `label=<uuid>` filter using `Label.uuid`.
- `url=<url-encoded-exact-url>` filter against exact `Clip.url`.

Acceptance for this milestone: manual test proves dynamic updates while typing, grouped results, max-five cap, keyboard-accessible navigation, and correct link destinations (`/clips/<clip-uuid>/`, `/clips?label=<label-uuid>`, `/clips?url=<encoded-exact-url>`).

## Plan of Work

Start with model changes because label UUID filtering is a required interface contract and PostgreSQL indexing must exist before search tuning can be validated. Add the UUID field, Postgres search migration(s), then update existing label serializers if needed to expose UUID where the quick-search payload requires it.

Implement quick-search business logic in `backend/apps/clips/services.py` to keep view layers orchestration-only. Build matching in this order: clip text/title/url, label name, and exact URL website grouping, then merge ranked items and truncate globally to five. Use PostgreSQL full-text and trigram scoring as primary relevance signals, and preserve ownership by filtering every candidate queryset by user.

Add API endpoint and strict input validation in serializers. Ensure error responses are explicit and user-safe (no internals, no raw sensitive payload echoes).

Then implement web UI behavior in `list.html`: input, result list, loading and empty states, accessibility attributes, and keyboard controls. Build links using the new filter contract (`label` UUID and exact `url`).

Finally, extend list filtering in `ClipListView` and add filter badges plus clear-filter links so navigated pages are self-explanatory.

## Concrete Steps

From repository root `/Users/e.laskaridis/Projects/sandbox/webclippings`, implement and verify in this order:

1. Configure PostgreSQL for the backend runtime used in implementation and tests.

   - Set `DATABASE_URL` to a PostgreSQL DSN before running migration/test commands for this feature.

2. Add label UUID field and migration, then implement service and tests.

   - Edit: `backend/apps/clips/models.py`, add migration in `backend/apps/clips/migrations/`, add `backend/apps/clips/services.py`, add `backend/apps/clips/tests/test_quick_search.py`.
   - Command:

     cd /Users/e.laskaridis/Projects/sandbox/webclippings/backend
     python manage.py test apps.clips.tests.test_models apps.clips.tests.test_quick_search

3. Add quick-search API endpoint and validation.

   - Edit: `backend/apps/clips/api/views.py`, `backend/apps/clips/api/serializers.py`, `backend/apps/clips/api/urls.py`, `backend/apps/clips/tests/test_api.py`.
   - Command:

     cd /Users/e.laskaridis/Projects/sandbox/webclippings/backend
     python manage.py test apps.clips.tests.test_api

4. Add web quick-search UI, accessibility controls, and list-view filters.

   - Edit: `backend/apps/clips/views.py`, `backend/apps/clips/templates/clips/list.html`, optionally `backend/webclippings/static/js/quick-search.js`.
   - Command:

     cd /Users/e.laskaridis/Projects/sandbox/webclippings/backend
     python manage.py test apps.clips.tests.test_views

5. Update API contract.

   - Edit: `specs/001-web-clipping-app/contracts/openapi.yaml`.

6. Run full backend regression for this feature scope.

   - Command:

     cd /Users/e.laskaridis/Projects/sandbox/webclippings/backend
     python manage.py test

Note on scope: extension test commands are intentionally excluded because this feature does not change `extension/` behavior.

## Validation and Acceptance

Behavioral acceptance requires all items below to pass:

An authenticated user on `/clips/` sees one quick-search input.

Valid input (`q` length 3-50, no whitespace) returns dynamic grouped results without full page reload.

Invalid input (whitespace, length <3, length >50) does not submit search request and shows an inline accessible validation message.

The response and UI present grouped `clips`, `labels`, and `websites` hits with a global maximum of five items.

Results include only the authenticated user’s data.

Clicking a clip hit opens `/clips/<clip-uuid>/`.

Clicking a label hit opens `/clips?label=<label-uuid>` and list results are filtered to that label.

Clicking a website hit opens `/clips?url=<url-encoded-exact-url>` and list results are filtered to clips with that exact URL.

Keyboard interaction works (`ArrowUp/Down`, `Enter`, `Escape`) and screen readers receive result count updates.

Non-functional acceptance:

Under representative local PostgreSQL test data, quick-search endpoint p56 response time is <= 500ms.

## Idempotence and Recovery

Code edits are additive and safe to reapply. Test commands can be rerun without side effects.

If migration rollout is interrupted, rerun `python manage.py migrate` after resolving schema conflicts, then rerun affected tests.

If quick-search UI scripts fail, keep list page functional by hiding suggestions panel and preserving normal list behavior.

If performance target is missed, keep correctness and security behavior, then record an explicit follow-up in `docs/TECH_DEBT_BACKLOG.md` with measured timings and concrete next actions.

## Artifacts and Notes

Detailed contract draft for review: `docs/plans/quick-search-api-draft.md`.

Expected quick-search response shape:

    {
      "query": "python",
      "total": 5,
      "hits": {
        "clips": [
          {
            "type": "clip",
            "clip_id": "<clip-uuid>",
            "title": "...",
            "snippet": "...",
            "url": "https://docs.python.org/3/library/pathlib.html",
            "score": 98,
            "target_url": "/clips/<clip-uuid>/"
          }
        ],
        "labels": [
          {
            "type": "label",
            "label_uuid": "<label-uuid>",
            "name": "python",
            "clip_count": 4,
            "score": 92,
            "target_url": "/clips?label=<label-uuid>"
          }
        ],
        "websites": [
          {
            "type": "website",
            "url": "https://docs.python.org/3/library/pathlib.html",
            "clip_count": 3,
            "score": 88,
            "target_url": "/clips?url=https%3A%2F%2Fdocs.python.org%2F3%2Flibrary%2Fpathlib.html"
          }
        ]
      }
    }

Expected validation errors:

    HTTP 400 for q="ab" -> "Ensure this field has at least 3 characters."
    HTTP 400 for q="python notes" -> "Whitespace is not allowed."
    HTTP 400 for q length > 50 -> "Ensure this field has no more than 50 characters."

## Interfaces and Dependencies

By the end of implementation, the following interfaces must exist.

In `backend/apps/clips/models.py`, update `Label` with:

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)

In `backend/apps/clips/services.py`, define:

    from typing import TypedDict
    from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity

    class QuickSearchResult(TypedDict):
        query: str
        total: int
        hits: dict[str, list[dict]]

    def quick_search(*, user, query: str, limit: int = 5) -> QuickSearchResult:
        """Return grouped top-N quick-search hits scoped to one user with strict query validation."""

In `backend/apps/clips/api/views.py`, define a read-only endpoint class (for example `QuickSearchView`) with:

- `authentication_classes = [CsrfExemptSessionAuthentication]`
- `permission_classes = [permissions.IsAuthenticated]`
- `get(self, request, *args, **kwargs)` reading `q`, validating constraints, invoking `quick_search`, returning JSON.

In `backend/apps/clips/api/urls.py`, add route:

    path("clips/quick-search/", QuickSearchView.as_view(), name="clip-quick-search")

In `backend/apps/clips/views.py`, extend `ClipListView.get_queryset()` to support:

- `label` query param as label UUID (`Label.uuid`).
- `url` query param as exact `Clip.url` value.

Dependencies and constraints:

- Use Django ORM and existing module boundaries.
- Use PostgreSQL-native capabilities (`django.contrib.postgres.search`, `pg_trgm`, GIN indexes) for ranking and performance.
- Require PostgreSQL-backed execution for feature development/testing and release validation.
- Keep ownership enforcement in every queryset and object lookup.
- Keep API and web behavior consistent for authentication and authorization.

## Change Note

2026-02-28: Updated this ExecPlan with confirmed stakeholder constraints: exact URL search targets, strict query validation (`3..50`, no whitespace, URL-encoded), p56 <= 500ms target, accessibility requirements, label UUID filtering contract, explicit web-only scope (extension out of scope), and PostgreSQL full-text/trigram implementation direction (Option 2).
2026-02-28: Updated this ExecPlan during Milestone 1 implementation to capture completed model/migration/service work, test evidence (SQLite + PostgreSQL), migration strategy decisions, and execution surprises (Docker daemon unavailable, index-name drift, and UUID migration prompt behavior).
