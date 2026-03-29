# Stimulus Migration Inventory (T026)

## Purpose

Define the in-scope interactive backend components for the Stimulus migration,
their owning controllers, and the explicit coordination contracts needed to
remove page-global orchestration and legacy `window.*` APIs.

## In-Scope Interactive Components

The interactive backend surface for this migration is exactly:

| Component | Current primary template root | Current behavior source |
| --- | --- | --- |
| `global-theme-toggle` | `backend/webclippings/templates/components/global-theme-toggle.html` | `backend/static/js/theme-controller.js` |
| `global-auth-quick-search` | `backend/webclippings/templates/components/global-auth-quick-search.html` | `backend/static/js/controllers/global-auth-quick-search-controller.js` |
| `clip-card` | `backend/apps/clips/templates/clips/components/clip-card.html` | `backend/static/js/controllers/clip-card-controller.js` |
| `label-filter-options` | `backend/apps/clips/templates/clips/components/label-filter-options.html` | `backend/static/js/controllers/label-filter-options-controller.js` |
| `filter-sidebar` | `backend/apps/clips/templates/clips/components/filter-sidebar.html` | `backend/static/js/controllers/filter-sidebar-controller.js` |
| `filter-drawer` | `backend/apps/clips/templates/clips/components/filter-drawer.html` | `backend/static/js/controllers/filter-drawer-controller.js` |
| `filter-trigger-row` | `backend/apps/clips/templates/clips/pages/list.html` | `backend/static/js/controllers/filter-trigger-row-controller.js` |

## Controller Ownership Map

| Controller identifier | Owns | Root contract | Responsibilities | Replaces legacy dependency |
| --- | --- | --- | --- | --- |
| `global-theme-toggle` | Global theme toggle button behavior only | Theme toggle component root | Read current document theme, update toggle icon state, update accessible label, persist selection to local storage after connect | `backend/static/js/theme-controller.js` post-paint toggle behavior |
| `global-auth-quick-search` | Authenticated quick-search component only | `[data-component="global-auth-quick-search"]` | Input debounce, request cancellation, results rendering, active descendant state, keyboard navigation, escape close, click-away close | `window.GlobalAuthQuickSearchComponent` |
| `clip-card` | Single clip card delete flow only | `[data-component="clip-card"]` | Delete request, CSRF header use, success removal, error/forbidden messaging | `window.ClipCardComponent` |
| `label-filter-options` | Label options list behavior only | `[data-component="label-filter-options"]` | Search filtering, show more/less state, selected-state sync from URL, selected-row reordering, label URL mutation helpers dispatched from local actions | `window.LabelFilterOptionsComponent` and `window.ClipsListLabelFilters` label mutation helpers |
| `filter-sidebar` | Desktop sidebar expand/collapse behavior only | `[data-component="filter-sidebar"]` | Toggle panel visibility and synchronize `panel=expanded|collapsed` URL state | `list-page.js` sidebar orchestration |
| `filter-drawer` | Mobile drawer behavior only | `[data-component="filter-drawer"]` | Open/close state, backdrop visibility, escape handling, focus entry/return, synchronize `panel=open|closed` URL state | `list-page.js` drawer orchestration |
| `filter-trigger-row` | Drawer trigger outside drawer root only | `[data-component="filter-trigger-row"]` | Dispatch open intent to the drawer controller when the mobile trigger remains outside the drawer root | `list-page.js` trigger wiring |

`filter-trigger-row` exists only because the mobile drawer open button currently
lives in `clips/pages/list.html`, outside the `filter-drawer` root. If that
button is moved inside the drawer-owned root in a later task, its controller can
be collapsed into `filter-drawer`.

## Coordination Contracts

### URL state is the source of truth

- Selected labels continue to be derived from repeated `label` query params.
- Panel state continues to be derived from the `panel` query param.
- Controllers that change filter or panel state update the URL directly rather
  than calling page-level orchestration helpers.

### DOM event contracts

| Event | Emitter | Consumer | Purpose |
| --- | --- | --- | --- |
| `clips:filter-drawer:state` | `filter-drawer` | `filter-trigger-row` | Keep the mobile trigger `aria-expanded` state synchronized with drawer visibility. |
| `clips:filter-drawer:open` | `filter-trigger-row` | `filter-drawer` | Open the mobile drawer without requiring direct controller reach-through. |

These events are emitted on `document` so controllers can coordinate without
introducing direct imports or `window.*` global APIs.

## Runtime Migration Boundaries

- `global-theme-toggle` keeps a minimal pre-paint bootstrap outside Stimulus for
  initial theme restoration before first paint.
- The remaining interactive behavior runs through one shared Stimulus
  application entrypoint and registered controllers loaded from
  `backend/static/js/backend-app.js`.
- `backend/apps/clips/static/clips/js/pages/list-page.js` is removed once
  `filter-sidebar`, `filter-drawer`, and `filter-trigger-row` own the remaining
  list-page coordination directly and label add/remove/clear affordances rely on
  their server-rendered navigation targets.
- No controller should expose a `window.*` API after the migration tasks are
  complete.
