# Phase 0 Research: Label-Based Clip Filtering

**Feature**: [specs/002-label-filter-sidebar/spec.md](specs/002-label-filter-sidebar/spec.md)  
**Plan**: [specs/002-label-filter-sidebar/plan.md](specs/002-label-filter-sidebar/plan.md)  
**Date**: 2026-03-14

This document resolves technical decisions for multi-select label filtering, URL persistence, responsive drawer behavior, and accessibility requirements for the clips list experience.

---

## Query-String Filter Shape

Decision: Use repeated `label` query parameters with canonical label slugs, plus a separate `panel` parameter for filter-panel visibility state.

Rationale:
- Repeated parameters match the feature specification and remain bookmarkable/shareable.
- Slugs are human-readable and stable for URLs.
- Separating label state (`label`) and panel state (`panel`) keeps behavior explicit and avoids accidental coupling.

Alternatives considered:
- Comma-separated labels in one parameter: rejected because parsing/escaping is more error-prone and less aligned with clarified requirements.
- JSON-encoded filter object in query string: rejected because URLs become less readable and less interoperable.

---

## Canonical Label Identifier Strategy

Decision: Add a per-user canonical `slug` field on `Label` and filter by slug values in query strings; keep UUID parsing only as a short transitional compatibility path if needed.

Rationale:
- Current web filter links use label UUIDs; the new specification requires slug URLs.
- A dedicated slug field avoids deriving slugs repeatedly at runtime and supports stable links.
- Per-user uniqueness on slug preserves ownership boundaries and avoids cross-user collisions.

Alternatives considered:
- Continue using UUIDs in URLs: rejected due to explicit requirement for slug-based URLs.
- Derive slug on every request from label name: rejected because renames would break old links and runtime derivation is less predictable.

---

## Multi-Select AND Filtering Semantics

Decision: Parse selected labels with `request.GET.getlist("label")`, normalize (`strip`, lowercase, dedupe), resolve user-owned labels, ignore unknown/invalid slugs, and apply AND semantics by chaining label filters.

Rationale:
- Chained Django ORM filters on M2M relationships naturally express AND behavior.
- Ignoring unknown or unavailable slugs satisfies graceful-degradation requirements.
- User-scoped label lookup prevents cross-user leakage.

Alternatives considered:
- OR semantics (`any selected label`): rejected because the specification explicitly requires AND logic.
- Returning empty results for any invalid slug: rejected because requirements call for graceful ignore behavior.

---

## Contextual (Faceted) Label Counts

Decision: Compute counts with query annotations against the currently filtered clip set so each label shows a contextual count under active filters, with selected labels always rendered first and always visible.

Rationale:
- Contextual counts communicate the effect of current filters and potential next selections.
- Annotation-based counting avoids N+1 `obj.clips.count()` behavior.
- Keeping selected labels visible even at zero supports clear state awareness and easy removal.

Alternatives considered:
- Static total counts only: rejected because requirements call for contextual/faceted counts.
- Client-side count calculation from preloaded clips: rejected because it is less reliable for larger datasets and duplicates backend logic.

---

## Responsive Filter Container Pattern

Decision: Use a desktop/tablet-left collapsible sidebar above 1024px and an off-canvas drawer at 1024px and below, opened by a visible Filters trigger above results.

Rationale:
- Directly matches breakpoint and interaction requirements.
- Keeps results full width on smaller screens.
- Preserves full feature parity across breakpoints.

Alternatives considered:
- Always-visible sidebar on all widths: rejected because it can crowd small viewports and violates requirements.
- Separate mobile-only filter page: rejected because it adds navigation friction and breaks parity with immediate filter interactions.

---

## Accessibility and Interaction Handling

Decision: Implement drawer interactions with explicit focus management and dismiss controls: open moves focus into drawer, close returns focus to trigger, dismiss via backdrop/Escape/Close action, and label toggles apply immediately without auto-closing drawer.

Rationale:
- Satisfies keyboard and assistive-technology requirements for predictable focus flow.
- Ensures dismiss gestures do not mutate selected labels.
- Supports continuous filtering workflows on small screens.

Alternatives considered:
- Auto-close drawer after each label selection: rejected by explicit requirement.
- Escape-only dismissal: rejected because explicit Close and backdrop dismissal are also required.

---

## Long Label Rendering and Assistive Text

Decision: Render long label text and selected pills on one line with CSS ellipsis, while keeping full label text available to assistive tech and discoverable via accessible naming.

Rationale:
- Prevents clipped/overlapping controls on small screens.
- Preserves comprehensibility for screen-reader users.
- Aligns with truncation and accessibility requirements.

Alternatives considered:
- Multi-line wrapping for labels and pills: rejected because it destabilizes dense filter layouts and conflicts with one-line truncation requirement.
- Hard truncation of source strings server-side: rejected because it discards semantic content.

---

## Test Strategy for This Feature

Decision: Cover this feature with Django view/model/API tests focused on filter semantics and state restoration, plus interaction-level checks for drawer accessibility and responsive behavior.

Rationale:
- Existing clips test suites already validate list behavior and ownership boundaries; extending them is low risk.
- Requirements are behavior-heavy (query persistence, focus return, clear-all consistency), so regression tests must target those flows directly.
- Keeps quality gates aligned with constitution testing discipline.

Alternatives considered:
- Manual QA only: rejected because success criteria require consistent behavior across many flows and breakpoints.
- Large new frontend test harness first: rejected as unnecessary complexity for this incremental feature.
