# Code Review Findings

## Task CRF-001

- Status: `MIGRATED`
- Short description: Canonicalize component root contracts and remove redundant root-level aliases.
- Reason for change: Duplicated root selectors and temporary alias contracts create drift risk; one canonical root contract per component keeps template/JS/CSS ownership clear.
- Affected files:
  - `backend/apps/clips/templates/clips/components/clip-card.html`
  - `backend/apps/clips/templates/clips/components/filter-drawer.html`
  - `backend/apps/clips/templates/clips/components/filter-sidebar.html`
  - `backend/apps/clips/templates/clips/components/label-filter-options.html`
  - `backend/apps/clips/templates/clips/pages/list.html`
  - `backend/apps/clips/static/clips/js/components/clip-card.js`
  - `backend/apps/clips/static/clips/js/pages/list-page.js`
  - `backend/apps/clips/static/clips/css/components/clip-card.css`
  - `backend/apps/clips/static/clips/css/components/filter-drawer.css`
  - `backend/apps/clips/static/clips/css/components/filter-sidebar.css`
  - `backend/apps/clips/static/clips/css/components/label-filter-options.css`
  - `backend/apps/clips/tests/views/test_clip_views.py` (assertion updates if required)
- Implementation notes:
  - Remove redundant root aliases: `data-clip-row`, `data-filter-drawer`, `data-filter-sidebar-shell`, `data-filter-drawer-backdrop`.
  - Keep canonical root hooks: `data-component="clip-card"`, `data-component="filter-drawer"`, `data-component="filter-sidebar"`, `data-component="filter-drawer-backdrop"`.
  - Remove temporary legacy class/state aliases once canonical BEM classes/modifiers fully cover behavior (`clip-title`, `clip-preview`, `clip-source-link`, `label-filter-*`, `is-*` aliases).
  - Preserve behavior parity: clip delete removes one card; drawer/backdrop and sidebar interactions remain unchanged.
  - Validate there are no remaining direct consumers of removed root aliases before deleting them.
  - Tracked in execution plan as `T023` in `docs/plans/modular-front-end/tasks.md`.

## Task CRF-002

- Status: `MIGRATED`
- Short description: Remove unused non-root hooks and eliminate CSS styling coupled to `data-*` attributes.
- Reason for change: Dead hooks and CSS coupling to JS selectors inflate complexity and blur ownership between structure/behavior/styling contracts.
- Affected files:
  - `backend/apps/clips/templates/clips/pages/list.html`
  - `backend/apps/clips/templates/clips/components/filter-drawer.html`
  - `backend/apps/clips/templates/clips/components/label-filter-options.html`
  - `backend/apps/clips/static/clips/css/components/filter-drawer.css`
  - `backend/apps/clips/static/clips/css/components/filter-sidebar.css`
  - `backend/apps/clips/static/clips/css/components/label-filter-options.css`
  - `backend/apps/clips/static/clips/css/components/list-page-layout.css`
  - `backend/apps/clips/tests/views/test_clip_views.py` (assertion updates if required)
- Implementation notes:
  - Removal candidates: `data-results-region`, `data-selected-labels`, `data-drawer-clear-all`, `data-visible-limit`, `data-label-empty-state`.
  - Replace CSS selectors that target `data-*` hooks (for example focus styles) with canonical BEM class selectors.
  - Reconfirm zero usage across JS/CSS/tests before removal.
  - Keep actively used interaction hooks unchanged (for example `data-action="clear-label-filters"`, `data-filter-drawer-trigger`, `data-filter-drawer-close`, `data-filter-panel-toggle`, and label toggle/search hooks).
  - Tracked in execution plan as `T024` in `docs/plans/modular-front-end/tasks.md`.

## Task CRF-003

- Status: `MIGRATED`
- Short description: Refactor clips list JS ownership boundaries by moving page orchestration to the page entrypoint and aligning hook contracts.
- Reason for change: Page-level behavior currently lives in component code, which couples reusable components to one route and makes future refactors riskier.
- Affected files:
  - `backend/apps/clips/static/clips/js/components/label-filter-options.js`
  - `backend/apps/clips/static/clips/js/pages/list-page.js`
  - `backend/apps/clips/templates/clips/components/filter-drawer.html`
  - `backend/apps/clips/templates/clips/components/filter-sidebar.html`
  - `backend/apps/clips/templates/clips/components/label-filter-options.html`
  - `backend/apps/clips/templates/clips/components/clip-card.html`
  - `backend/apps/clips/static/clips/js/components/clip-card.js`
- Implementation notes:
  - Move page-level coordination behavior from component modules to `static/.../js/pages/list-page.js` (drawer/sidebar state wiring, cross-component interaction orchestration, page URL/panel synchronization, shared keyboard handling).
  - Keep component modules scoped to their own root and internal behavior only.
  - Include finding 3 scope in this refactor by standardizing interactive/internal hooks toward `data-action` and `data-role` semantics where contracts are touched.
  - Add explicit `hooks` documentation to component header comments and keep hook docs synchronized with actual JS consumers.
  - Tracked in execution plan as `T025` in `docs/plans/modular-front-end/tasks.md`.
