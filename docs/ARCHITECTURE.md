# Architecture Guidelines

## Architecture Style

The backend uses a modular monolith:
- one deployable Django application
- strongly separated feature modules under `backend/apps/`
- explicit dependency direction to keep low coupling and high cohesion

## Main Architectural Components

### Backend Components

1. `webclippings` (composition root)
- Responsibility: project wiring only (settings, URL composition, auth plumbing, global middleware/config).
- Must not contain feature business logic.
- Interactions: routes requests to feature modules.

2. `apps.accounts` (identity module)
- Responsibility: authentication and account lifecycle flows.
- Owns account-facing templates/views/tests in its bounded context.
- Dependencies: Django auth framework and shared platform services.
- Interactions: consumed by users and by other modules only through auth/session state, not direct feature coupling.

3. `apps.clips` (clipping domain module)
- Responsibility: clip/label domain model, business rules, API + HTML interfaces, and tests.
- Owns invariants for clip ownership, label ownership, and clip-label relations.
- Dependencies: Django/DRF and shared platform services.
- Interactions: serves `/clips/*` and `/api/*` flows; uses authenticated user context from accounts/session.

4. Database (PostgreSQL/SQLite via Django ORM)
- Responsibility: persistence and hard integrity guarantees.
- Interactions: all writes/reads go through module-owned models and query boundaries.

5. Chrome Extension (`extension/chrome/src`)
- Responsibility: capture browser content and call backend APIs.
- Internal components:
  - content script: capture selection/page metadata only
  - popup: user interaction/status
  - background worker: API/network orchestration
  - shared: message/config/error primitives
- Interactions: sends authenticated requests to backend API endpoints.

## Backend Layering Rules (Per Module)

Use this dependency direction inside each module:
1. Interface layer (`views.py`, `api/views.py`, serializers/forms/template adapters)
2. Application layer (`services.py` or `use_cases/`)
3. Domain layer (`models.py`, domain policies/validators)
4. Infrastructure adapters (optional; external integrations)

Rules:
- Interface -> application/domain is allowed.
- Application -> domain is allowed.
- Domain -> interface is not allowed.
- Keep business rules in application/domain, not in project wiring files.

## Dependency and Interaction Rules

- No circular dependencies across modules.
- Do not import another module's interface layer (`views`, `api/views`, templates).
- Cross-module business interactions should go through explicit service/use-case APIs.
- Keep cross-module data exchange narrow (IDs/DTO-like payloads preferred over passing ORM objects).
- Keep API and HTML interfaces behaviorally consistent for auth/ownership semantics.
- Use `transaction.atomic()` for multi-write use cases.
- Preserve invariants with DB constraints first, application checks second.

## Domain Invariants

Preserve these invariants unless behavior changes are explicitly requested and tests/docs are updated:

- Data isolation: users must only access their own clips/labels.
- Label uniqueness: label names are unique per user.
- Clip-label ownership: a clip can only be linked to labels owned by the same user.
- Clip ordering: lists default to most recent first (`-created_at`).
- Clip normalization: `normalized_text` is derived from `raw_content` (whitespace-normalized, lowercased).
- URL/domain integrity: `domain` is derived from `url`.

## Implementation Rules (Django + DRF)

- Keep query scoping in `get_queryset()` and always filter by `request.user`.
- Keep validation and request-shape mapping in serializers; keep views thin.
- Reuse model constraints for data integrity; do not duplicate partial logic in templates.
- Keep HTML routes (`apps.clips.views`) and API routes (`apps.clips.api.views`) behaviorally consistent for ownership and authorization.
- Use `select_related`/`prefetch_related` when returning related data to avoid N+1 queries.
- If models change, create migrations and update affected tests.

## Evolution Guidance

When refactoring existing backend code:
1. Keep behavior stable.
2. Move non-trivial logic out of views/serializers into module application services.
3. Keep interfaces orchestration-only.
4. Add or adjust tests for module behavior and boundary contracts before further refactors.
