# Execution Tasks

## Assumptions
- This plan covers only `backend/` front-end assets and templates; `extension/` remains untouched.
- Existing Django template/static roots stay unchanged, and refactor work is limited to introducing `layouts/`, `pages/`, and `components/` sub-structure under current roots.
- Existing route URLs, views, form POST targets, auth/ownership checks, and API endpoints are preserved; this is a structural refactor with behavioral parity.
- Current user-facing pages in scope include `home`, all `accounts` auth templates, and `clips` pages (`list`, `detail`, `labels`) with current interactions (theme toggle, quick search, filters, delete flow, label form flows).
- Validation commands from the spec are treated as mandatory completion gates (`make backend-test-unit`, `make backend-lint`, `make backend-typecheck`, and `make all-verify` before handoff).

## Task T001
- Task id: T001
- Task description: Establish migration inventory and target modular map for every current backend template/static asset, including route-to-page mapping and interaction ownership boundaries.
- Priority: P0
- Acceptance criteria:
  - A checked-in migration matrix lists each existing template and asset with its target destination (`layouts`, `pages`, `components`, `js/pages`, `js/components`, `css/components`, global `tokens/base`).
  - Every route/page in scope is mapped to exactly one page entrypoint under `templates/.../pages/`.
  - Every existing interaction (theme toggle, quick search, filters, delete clip, labels CRUD forms, auth forms) is assigned to page-level orchestration or component-level ownership.
- Status: COMPLETED
- Dependencies:
  - None
- Notes:
  - Treat this as the source of truth for batch migration sequencing and parity verification.

## Task T002
- Task id: T002
- Task description: Create global modular scaffold under `backend/webclippings/templates` and `backend/static` (layouts/components, design tokens, and component/page JS/CSS directories) without behavior changes.
- Priority: P0
- Acceptance criteria:
  - Global directories exist per spec (`templates/layouts`, `templates/components`, `static/js/components`, `static/css/components`, `static/css/tokens.css`).
  - `tokens.css` and global `base.css` loading order is defined and applied consistently.
  - No runtime regressions occur from scaffold introduction alone.
- Status: COMPLETED
- Dependencies:
  - T001
- Notes:
  - Keep root paths unchanged; do not migrate Django `settings.py` template/static configuration in this phase.

## Task T003
- Task id: T003
- Task description: Modularize global base shell into explicit layout and reusable global components, and remove inline JS/CSS from migrated templates.
- Priority: P0
- Acceptance criteria:
  - `base.html` responsibilities are split into layout + included global components (for example nav, footer, theme toggle control, authenticated quick-search shell) using `{% include %}`.
  - Migrated templates contain no inline `<script>` or `<style>` blocks/attributes requiring dedicated component CSS/JS extraction.
  - Each new component template includes the required header contract comment (`component`, `inputs`, `actions`).
- Status: COMPLETED
- Dependencies:
  - T002
- Notes:
  - Keep `{% extends %}` only for page-to-layout inheritance; components must not extend templates.

## Task T004
- Task id: T004
- Task description: Introduce app-level modular structure for `clips` and `accounts` templates/static assets and move existing pages into `pages/` with app layouts/components directories.
- Priority: P0
- Acceptance criteria:
  - `backend/apps/clips/templates/clips/pages`, `components`, `layouts` and `backend/apps/clips/static/clips/js/components`, `js/pages`, `css/components` exist and are wired.
  - `backend/apps/accounts/templates/accounts/pages`, `components`, `layouts` exist and auth templates are migrated to page files.
  - All migrated pages render from `pages/` paths with no route breakage.
- Status: COMPLETED
- Dependencies:
  - T001
  - T003
- Notes:
  - Use component naming triplets with matching kebab-case base names.

## Task T005
- Task id: T005
- Task description: Decompose clips list page template into focused reusable components with explicit input contracts and include-context usage.
- Priority: P0
- Acceptance criteria:
  - `clips` list page is split into page template + component partials (filter sidebar, filter drawer, selected filters/pills, clip card/list item, empty states).
  - Component include call sites pass explicit context via `with`; no hidden ambient variable dependencies beyond documented contracts.
  - Rendered UI structure and visible behavior for list route remains parity-equivalent.
- Status: COMPLETED
- Dependencies:
  - T004
- Notes:
  - Keep one component per responsibility; avoid oversized partials that mix unrelated concerns.

## Task T006
- Task id: T006
- Task description: Split clips list JavaScript into page entrypoint orchestration plus component-scoped modules using stable `data-component` ownership boundaries.
- Priority: P0
- Acceptance criteria:
  - Current `clips/static/clips/js/list.js` logic is partitioned into `js/pages/<page>.js` (page orchestration) and `js/components/<component>.js` modules.
  - Component JS only reads/mutates DOM within `[data-component="<component-name>"]` roots.
  - Cross-component coordination uses DOM events and/or URL/query state, avoiding tight direct imports where possible.
  - Existing interactions remain functional: quick search, label filtering (sidebar/drawer/search/show-more), selected-label operations, and clip delete flow.
- Status: COMPLETED
- Dependencies:
  - T005
- Notes:
  - Preserve current keyboard and accessibility behavior for quick-search and filter controls.

## Task T007
- Task id: T007
- Task description: Decompose clips list CSS into component-scoped styles and move shared constants to tokens/base layers.
- Priority: P1
- Acceptance criteria:
  - Existing `clips/static/clips/css/list.css` rules are split by component into `css/components/<component>.css` files.
  - Component styles are scoped via root class or `[data-component="<component-name>"]` selectors and avoid global element overrides.
  - Any shared visual constants are promoted to `static/css/tokens.css` (and referenced from component styles/base).
- Status: COMPLETED
- Dependencies:
  - T005
  - T006
- Notes:
  - Preserve responsive behavior and no-horizontal-scroll constraints on clips list layouts.

## Task T008
- Task id: T008
- Task description: Modularize remaining clips pages (`detail`, `labels`) into page/component architecture and externalize any inline styling to scoped CSS components.
- Priority: P0
- Acceptance criteria:
  - `clips/detail` and `clips/labels` templates are moved under `templates/clips/pages/` and decomposed into reusable components where beneficial.
  - Inline style currently present in clips detail content block is removed and represented in component/base CSS.
  - Labels create/update/delete forms and detail label editing workflows preserve current behavior and permissions.
- Status: COMPLETED
- Dependencies:
  - T004
- Notes:
  - Keep forms server-rendered and progressively enhanced only where needed.

## Task T009
- Task id: T009
- Task description: Modularize accounts and home UI templates into page/component/layout structure while preserving current auth UX and form behavior.
- Priority: P1
- Acceptance criteria:
  - All accounts templates (login/register/password reset/activation flows) are represented as page templates under `templates/accounts/pages/` with reusable components for repeated auth-card/form patterns.
  - `home` page is migrated to page/component structure and continues to render authenticated/anonymous CTAs correctly.
  - No auth flow regressions (sign-in, register, password reset, activation) are introduced.
- Status: COMPLETED
- Dependencies:
  - T003
  - T004
- Notes:
  - Keep messaging and validation/error rendering parity with existing templates.

## Task T010
- Task id: T010
- Task description: Add automated and manual parity verification coverage for migrated routes/components, including regression tests for clips ownership-sensitive behavior.
- Priority: P0
- Acceptance criteria:
  - Automated tests are added/updated for any behavior affected by template/JS refactor, especially clips list interactions and auth-sensitive clips access.
  - Manual smoke checklist is executed for each migrated route: load success, primary action path, mobile/desktop sanity, no new console errors.
  - No auth or ownership regression is observed on clips pages.
- Status: COMPLETED
- Dependencies:
  - T006
  - T007
  - T008
  - T009
- Notes:
  - Keep test changes focused on behavior; avoid overfitting to internal template structure.

## Task T011
- Task id: T011
- Task description: Run required quality gates and finalize compliance documentation for handoff.
- Priority: P0
- Acceptance criteria:
  - `make backend-test-unit`, `make backend-lint`, and `make backend-typecheck` pass for migration batches.
  - `make all-verify` passes before handoff.
  - Plan artifacts are updated with final status/progress and any intentionally deferred debt is captured in `docs/TECH_DEBT_BACKLOG.md`.
- Status: COMPLETED
- Dependencies:
  - T010
- Notes:
  - Treat any failing gate as a blocker; do not hand off without resolution or explicit documented defer decision.

## Task T012
- Task id: T012
- Task description: Replace component CSS selector coupling with explicit BEM class contracts for all currently styled components.
- Priority: P0
- Acceptance criteria:
  - Component CSS no longer uses `[data-component="..."]` selectors as the styling anchor.
  - Component CSS selectors use explicit BEM block/element/modifier class names.
  - Component CSS selectors do not rely on ids or tag-based selectors for component styling.
  - Styled component roots expose one canonical BEM block class each.
- Status: COMPLETED
- Dependencies:
  - T011
- Notes:
  - Primary areas to migrate:
    - `backend/apps/clips/static/clips/css/components/clip-card.css`
    - `backend/apps/clips/static/clips/css/components/detail-content-card.css`
    - `backend/apps/clips/static/clips/css/components/filter-drawer.css`
    - `backend/apps/clips/static/clips/css/components/filter-sidebar.css`
    - `backend/apps/clips/static/clips/css/components/label-filter-options.css`
    - `backend/apps/clips/static/clips/css/components/list-page-layout.css`
    - `backend/apps/clips/static/clips/css/components/selected-label-pills.css`
    - `backend/static/css/components/global-auth-quick-search.css`
    - `backend/static/css/components/global-nav.css`

## Task T013
- Task id: T013
- Task description: Align component templates with BEM root/element/modifier classes to match migrated CSS contracts.
- Priority: P0
- Acceptance criteria:
  - Templates for styled components include canonical BEM root classes on component roots.
  - Element class names in templates follow `<block>__<element>` where component styles target them.
  - Modifier classes follow `<block>--<modifier>` or `<block>__<element>--<modifier>` and are always paired with their base class.
  - `data-*` attributes remain available for JavaScript hooks but are not required for CSS targeting.
- Status: COMPLETED
- Dependencies:
  - T012
- Notes:
  - Primary template areas to migrate:
    - `backend/apps/clips/templates/clips/components/clip-card.html`
    - `backend/apps/clips/templates/clips/components/detail-content-card.html`
    - `backend/apps/clips/templates/clips/components/filter-drawer.html`
    - `backend/apps/clips/templates/clips/components/filter-sidebar.html`
    - `backend/apps/clips/templates/clips/components/label-filter-options.html`
    - `backend/apps/clips/templates/clips/components/selected-label-pills.html`
    - `backend/apps/clips/templates/clips/pages/list.html`
    - `backend/webclippings/templates/components/global-auth-quick-search.html`
    - `backend/webclippings/templates/components/global-nav.html`

## Task T014
- Task id: T014
- Task description: Update JavaScript class/state handling to use BEM modifiers and preserve interaction parity after template/CSS class migration.
- Priority: P0
- Acceptance criteria:
  - JS toggles BEM modifier classes instead of legacy state classes (for example `is-collapsed`, `.active`, `is-selected`) where those classes are component styling state.
  - Component JS keeps using `data-*` selectors for ownership/behavior hooks.
  - Existing clips list interactions keep parity (filter panel toggle, drawer open/close, selected labels behavior, quick search keyboard navigation, delete flow).
- Status: COMPLETED
- Dependencies:
  - T013
- Notes:
  - Primary JS areas to update:
    - `backend/apps/clips/static/clips/js/components/label-filters.js`
    - `backend/static/js/components/global-auth-quick-search.js`
    - Any affected component module that sets/removes presentational classes.

## Task T015
- Task id: T015
- Task description: Extend component header contracts to include BEM metadata (`block`, `elements`, `modifiers`) across migrated component templates.
- Priority: P1
- Acceptance criteria:
  - Every migrated component template header includes `component`, `inputs`, `actions`, `block`, `elements`, and `modifiers`.
  - Header metadata reflects the actual class contract used in template/CSS.
  - Components with no modifiers explicitly document `modifiers: none`.
- Status: COMPLETED
- Dependencies:
  - T013
- Notes:
  - Apply to migrated component templates under:
    - `backend/webclippings/templates/components/`
    - `backend/apps/clips/templates/clips/components/`
    - `backend/apps/accounts/templates/accounts/components/`

## Task T016
- Task id: T016
- Task description: Re-run verification and manual BEM compliance checks for migrated routes/components.
- Priority: P0
- Acceptance criteria:
  - Required gates pass: `make backend-test-unit`, `make backend-lint`, `make backend-typecheck`.
  - Final gate passes before handoff: `make all-verify`.
  - Manual checks confirm no regressions on home, accounts auth pages, and clips list/detail/labels flows.
  - Spot audit confirms component styling is class-based BEM and not `[data-component]` anchored.
- Status: COMPLETED
- Dependencies:
  - T014
  - T015
- Notes:
  - Include desktop/mobile sanity and browser console error checks for each migrated route.

## Task T017
- Task id: T017
- Task description: Align clips list JS component module naming and ownership boundaries with template component naming triplets.
- Priority: P0
- Acceptance criteria:
  - Clips list component JS files use basenames that match their corresponding template component names and responsibilities.
  - Reusable component behavior is implemented in `backend/apps/clips/static/clips/js/components/<component-name>.js`; page orchestration remains in `backend/apps/clips/static/clips/js/pages/list-page.js`.
  - `backend/apps/clips/templates/clips/pages/list.html` script includes/import usage reflect the renamed/split modules without stale references.
  - Existing clips list interactions (filtering, selected labels operations, clip delete flow) remain parity-equivalent after module alignment.
- Status: COMPLETED
- Dependencies:
  - T016
- Notes:
  - Address review finding `ISSUE-01` from `docs/plans/modular-front-end/pr62-review-findings.md`.

## Task T018
- Task id: T018
- Task description: Refactor component JS initialization to be rooted per component instance instead of document-global selectors.
- Priority: P0
- Acceptance criteria:
  - `backend/apps/clips/static/clips/js/components/clip-card.js` initializes from component roots and only queries descendants within each root.
  - `backend/apps/clips/static/clips/js/components/label-filter-options.js` initializes from explicit component roots and removes broad document/root selection during setup.
  - `backend/static/js/components/global-auth-quick-search.js` initializes quick-search behavior from its component root instead of global ID-only lookup.
  - Cross-component behavior remains orchestrated at page-entrypoint level, and component modules maintain encapsulated ownership boundaries.
- Status: COMPLETED
- Dependencies:
  - T017
- Notes:
  - Address review finding `ISSUE-02` from `docs/plans/modular-front-end/pr62-review-findings.md`.

## Task T019
- Task id: T019
- Task description: Add regression coverage and re-run verification after PR #62 review fixes.
- Priority: P0
- Acceptance criteria:
  - Automated coverage is added/updated for any behavior touched by T017-T018, including multi-instance/component-root initialization paths.
  - Required gates pass: `make backend-test-unit`, `make backend-lint`, `make backend-typecheck`.
  - Final release gate passes before handoff: `make all-verify`.
  - `docs/plans/modular-front-end/pr62-review-findings.md` findings are fully addressed with no remaining blocking items.
- Status: COMPLETED
- Dependencies:
  - T018
- Notes:
  - Keep validation focused on behavioral parity and modular ownership guarantees.

## Task T020
- Task id: T020
- Task description: Restore CSRF context propagation for labels page form components included with `{% include ... only %}`.
- Priority: P0
- Acceptance criteria:
  - `backend/apps/clips/templates/clips/pages/labels.html` passes `csrf_token` explicitly to each included partial that renders POST forms while using `only`.
  - Include chains used by labels create/update/delete forms preserve CSRF token rendering in browser requests.
  - Labels create/update/delete POST flows no longer fail CSRF validation due to missing token context.
- Status: COMPLETED
- Dependencies:
  - T019
- Notes:
  - Addresses PR #62 review comment `https://github.com/laskaridis/clippy/pull/62#discussion_r3000886882`.
  - Follow Django partial rule from `AGENTS.md`: include `csrf_token` explicitly through `with ... only` chains.

## Task T021
- Task id: T021
- Task description: Forward CSRF context to clip detail labels panel include to keep label edit POSTs valid.
- Priority: P0
- Acceptance criteria:
  - `backend/apps/clips/templates/clips/pages/detail.html` passes `csrf_token` to the `detail-labels-panel` include when using `only`.
  - `backend/apps/clips/templates/clips/components/detail-labels-panel.html` renders a valid CSRF hidden input on POST forms in real browser responses.
  - Label edit/save flow on clip detail no longer fails with CSRF 403 caused by include context isolation.
- Status: COMPLETED
- Dependencies:
  - T020
- Notes:
  - Addresses PR #62 review comment `https://github.com/laskaridis/clippy/pull/62#discussion_r3000886885`.

## Task T022
- Task id: T022
- Task description: Add CSRF regression coverage for labels/detail form partial includes and re-run required quality gates.
- Priority: P0
- Acceptance criteria:
  - Automated tests are added or updated to cover labels page and detail page POST form flows that depend on CSRF token rendering through include chains.
  - Required gates pass after fixes: `make backend-test-unit`, `make backend-lint`, `make backend-typecheck`.
  - Final release gate passes before handoff: `make all-verify`.
- Status: COMPLETED
- Dependencies:
  - T021
- Notes:
  - Validate both template render output (token present) and behavior-level POST success for authenticated owners.

## Task T023
- Task id: T023
- Task description: Canonicalize component root contracts and remove redundant root-level aliases.
- Priority: P0
- Acceptance criteria:
  - Redundant root aliases are removed: `data-clip-row`, `data-filter-drawer`, `data-filter-sidebar-shell`, `data-filter-drawer-backdrop`.
  - Canonical root hooks remain in place: `data-component="clip-card"`, `data-component="filter-drawer"`, `data-component="filter-sidebar"`, `data-component="filter-drawer-backdrop"`.
  - Temporary legacy class/state aliases are removed once canonical BEM classes/modifiers fully cover behavior (`clip-title`, `clip-preview`, `clip-source-link`, `label-filter-*`, `is-*` aliases).
  - Clips list behavior remains parity-equivalent (clip delete removes one card; drawer/backdrop and sidebar interactions unchanged).
- Status: COMPLETED
- Dependencies:
  - T022
- Notes:
  - Migrated from `docs/plans/modular-front-end/code-review-findings.md` task `CRF-001`.
  - Reconfirm there are no remaining direct consumers of removed root aliases before deletion.

## Task T024
- Task id: T024
- Task description: Remove unused non-root hooks and eliminate CSS styling coupled to `data-*` attributes.
- Priority: P0
- Acceptance criteria:
  - Unused non-root hooks are removed where there are no active JS/CSS/test consumers (`data-results-region`, `data-selected-labels`, `data-drawer-clear-all`, `data-visible-limit`, `data-label-empty-state`).
  - CSS selectors that target `data-*` hooks are replaced with canonical class-based BEM selectors.
  - Actively used interaction hooks remain intact (`data-action="clear-label-filters"`, `data-filter-drawer-trigger`, `data-filter-drawer-close`, `data-filter-panel-toggle`, and label toggle/search hooks).
  - Affected tests are updated only as needed for removed hook assertions.
- Status: COMPLETED
- Dependencies:
  - T023
- Notes:
  - Migrated from `docs/plans/modular-front-end/code-review-findings.md` task `CRF-002`.
  - Reconfirm zero usage across JS/CSS/tests before deleting each hook.

## Task T025
- Task id: T025
- Task description: Refactor clips list JS ownership boundaries by moving page orchestration to the page entrypoint and aligning hook contracts.
- Priority: P0
- Acceptance criteria:
  - Page-level coordination behavior is moved from component modules to `backend/apps/clips/static/clips/js/pages/list-page.js` (drawer/sidebar wiring, cross-component orchestration, URL/panel synchronization, shared keyboard handling).
  - Component modules remain scoped to their own root and internal behavior.
  - Hook contracts touched in this refactor are standardized toward `data-action` / `data-role`.
  - Component template header comments include explicit `hooks` entries aligned with actual JS consumers.
  - Clips list interactions remain parity-equivalent after refactor.
- Status: COMPLETED
- Dependencies:
  - T024
- Notes:
  - Migrated from `docs/plans/modular-front-end/code-review-findings.md` task `CRF-003`.
