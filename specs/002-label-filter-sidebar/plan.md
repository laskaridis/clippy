# Implementation Plan: Label-Based Clip Filtering

**Branch**: `002-label-filter-sidebar` | **Date**: 2026-03-14 | **Spec**: [specs/002-label-filter-sidebar/spec.md](specs/002-label-filter-sidebar/spec.md)
**Input**: Feature specification from [specs/002-label-filter-sidebar/spec.md](specs/002-label-filter-sidebar/spec.md)

**Note**: This plan is maintained by the `/speckit.plan` workflow and should stay in sync with the feature spec, research, data model, quickstart, and contracts.

## Summary

Deliver a fully accessible label-filtering experience on the clips list page with multi-select AND matching, repeated `label=<slug>` query-string persistence, selected-label pills with individual removal and clear-all actions, and responsive filter controls that switch from a collapsible left sidebar to an off-canvas drawer at viewport widths of 1024px and below.

The implementation keeps the current modular-monolith architecture and extends the existing clips web interface using server-rendered Django templates plus focused vanilla JavaScript for interaction behavior (drawer open/close, focus return, client-side label list search filtering from the initial payload, and query-string updates).

## Technical Context

**Language/Version**: Python 3.12 (Django backend), HTML templates, CSS (Bootstrap-based), vanilla JavaScript (ES2019+)  
**Primary Dependencies**: Django 5.2, Django REST Framework (parity behavior where relevant), Bootstrap 5, Django auth/session stack  
**Storage**: PostgreSQL via Django ORM (`Clip`, `Label`, `ClipLabel`); introduce canonical per-user `Label.slug` for URL filters  
**Testing**: Django `TestCase` suites for views/models/API behavior, targeted JS behavior checks where applicable, and regression coverage for filter semantics + accessibility attributes  
**Target Platform**: Server-rendered web UI in modern desktop and mobile browsers; authenticated Django web session flows  
**Project Type**: Web application (backend-rendered UI + backend APIs + extension coexistence)  
**Performance Goals**: Maintain responsive filtering on representative datasets (>=100 labels) and keep filter interactions subjectively immediate (target sub-second server render for typical filtered list requests)  
**Constraints**: Preserve existing architecture boundaries; no new frontend framework; enforce per-user data isolation; support viewport <=1024px without clipped controls or horizontal scrolling; preserve keyboard/screen-reader operation  
**Scale/Scope**: Clip list filtering flow only (labels + panel state + pills + responsive drawer), with no new non-label filter types and no label authoring workflow expansion

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Pre-Research Gate Status**: PASS

- **Simplicity & Architecture**: PASS. The plan stays within the existing Django modular monolith and existing clips module, adding no new service tier or framework.
- **Engineering Quality & Testing**: PASS. The plan maps behavior changes to automated Django tests covering AND filtering, query-string restoration, unknown slug handling, pill removal, clear-all, and responsive/drawer accessibility states.
- **Consistent UX**: PASS. The plan keeps canonical terminology as "label" and aligns filters with existing clips page patterns while introducing a documented responsive drawer variant for small screens.
- **Security & Privacy**: PASS. All label resolution and clip filtering stay user-scoped; invalid/unowned slugs are ignored without leaking cross-user metadata.

## Project Structure

### Documentation (this feature)

```text
specs/002-label-filter-sidebar/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── openapi.yaml
└── tasks.md                  # Generated and maintained by /speckit.tasks
```

### Source Code (repository root)

```text
backend/
├── apps/
│   └── clips/
│       ├── models.py                 # Label slug and constraints
│       ├── views.py                  # ClipListView filtering + panel state
│       ├── urls.py
│       ├── templates/clips/list.html # Sidebar/drawer/pills/filter controls
│       ├── static/clips/js/list.js   # Drawer + URL + focus behavior
│       ├── static/clips/css/list.css # Responsive + truncation + drawer styles
│       ├── api/
│       │   ├── views.py              # Optional parity filtering behavior
│       │   └── serializers.py        # Contextual counts if API-aligned
│       └── tests/
│           ├── test_views.py
│           ├── test_api.py
│           └── test_models.py
└── webclippings/
    └── settings.py
```

**Structure Decision**: Use the existing `apps.clips` bounded context as the single implementation surface for model, query, template, JS, CSS, and test changes. Keep behavior parity between HTML and API surfaces where practical, without introducing new projects or service boundaries.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | N/A | N/A |

## Constitution Check (Post-Design Re-check)

**Post-Design Gate Status**: PASS

- **Simplicity & Architecture**: PASS. Design uses existing list endpoint and clips module artifacts; no additional backend service/component introduced.
- **Engineering Quality & Testing**: PASS. Design artifacts define explicit regression coverage across query parsing, AND semantics, contextual counts, panel-state restoration, and accessibility interactions.
- **Consistent UX**: PASS. Desktop and small-screen variants expose the same filter capabilities and terminology; clear-all and removable pills remain consistent across breakpoints.
- **Security & Privacy**: PASS. Contract and data model keep user ownership constraints and graceful handling of invalid label values.
