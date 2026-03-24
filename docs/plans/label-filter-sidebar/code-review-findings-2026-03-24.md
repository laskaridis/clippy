# PR Review Template (Agent-Authored)

Use this template to document local code review findings in a consistent, actionable format.

## Review metadata

- Branch: `feature/label-filter-sidebar`
- Review scope (files/areas):
  - Uncommitted changes in current worktree
  - `backend/apps/clips/static/clips/js/list.js`
  - Related UI keyboard interaction behavior (drawer + quick search panel)
- Review date (UTC): `2026-03-24`

## Review verdict

- Blocking issues present: `yes`
- Highest severity found: `High`
- Summary: Found a blocking keyboard-interaction bug where pressing `Escape` can close multiple UI layers at once due to overlapping handlers.

## Severity legend

- `Critical`: Release-blocking correctness/security/data-loss risk
- `High`: High-impact bug or regression risk; should be fixed before merge
- `Medium`: Medium-impact maintainability/behavior risk; fix soon
- `Low`: Low-impact improvement or cleanup

## Findings 

### ISSUE-01 - `Escape` closes the wrong UI layer due to overlapping handlers

- Severity: `High` (**required**)
- Blocking: `yes` (**required**)
- Category: `ux`
- Location:
  - File(s): `backend/apps/clips/static/clips/js/list.js`
  - Line(s) / symbol(s): document-level keydown handler around `291-298`; search input keydown handler around `669-693` (Escape branch around `689-692`)
- Impact: When both quick search panel and drawer are open, pressing `Escape` can trigger both handlers, causing the drawer to close even when the user intends to dismiss only quick search. This creates surprising behavior and can disrupt keyboard workflows.
- Recommended fix: Handle `Escape` with explicit layering. Prefer stopping propagation in the search input handler after closing quick search (`event.stopPropagation()`), and/or guard the document-level drawer handler so it does not run while quick search panel is open.
