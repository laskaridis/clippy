# Modular Front-End Migration Matrix (T001)

## Scope
- Backend web templates and frontend static assets only.
- No changes to `extension/`.
- Root Django template/static settings paths stay unchanged in this phase.

## Route To Target Page Entrypoint Map

| Route name | Current route pattern | Current template | Target page entrypoint |
| --- | --- | --- | --- |
| `home` | `/` | `backend/webclippings/templates/home.html` | `backend/webclippings/templates/pages/home.html` |
| `clips_web:list` | `/clips/` | `backend/apps/clips/templates/clips/list.html` | `backend/apps/clips/templates/clips/pages/list.html` |
| `clips_web:detail` | `/clips/<uuid:pk>/` | `backend/apps/clips/templates/clips/detail.html` | `backend/apps/clips/templates/clips/pages/detail.html` |
| `clips_web:labels` | `/clips/labels/` | `backend/apps/clips/templates/clips/labels.html` | `backend/apps/clips/templates/clips/pages/labels.html` |
| `accounts:login` | `/accounts/login/` | `backend/apps/accounts/templates/accounts/login.html` | `backend/apps/accounts/templates/accounts/pages/login.html` |
| `accounts:register` | `/accounts/register/` | `backend/apps/accounts/templates/accounts/register.html` | `backend/apps/accounts/templates/accounts/pages/register.html` |
| `accounts:activate` | `/accounts/activate/<uidb64>/<token>/` | `backend/apps/accounts/templates/accounts/activation_complete.html` | `backend/apps/accounts/templates/accounts/pages/activation-complete.html` |
| `accounts:password_reset` | `/accounts/password-reset/` | `backend/apps/accounts/templates/accounts/password_reset_form.html` | `backend/apps/accounts/templates/accounts/pages/password-reset-form.html` |
| `accounts:password_reset_done` | `/accounts/password-reset/done/` | `backend/apps/accounts/templates/accounts/password_reset_done.html` | `backend/apps/accounts/templates/accounts/pages/password-reset-done.html` |
| `accounts:password_reset_confirm` | `/accounts/password-reset/<uidb64>/<token>/` | `backend/apps/accounts/templates/accounts/password_reset_confirm.html` | `backend/apps/accounts/templates/accounts/pages/password-reset-confirm.html` |
| `accounts:password_reset_complete` | `/accounts/password-reset/complete/` | `backend/apps/accounts/templates/accounts/password_reset_complete.html` | `backend/apps/accounts/templates/accounts/pages/password-reset-complete.html` |

## Template Inventory To Target Destination

| Current template asset | Type | Target destination category | Target destination |
| --- | --- | --- | --- |
| `backend/webclippings/templates/base.html` | global layout template | `templates/layouts` + global components | `backend/webclippings/templates/layouts/base.html` + includes in `backend/webclippings/templates/components/` |
| `backend/webclippings/templates/home.html` | global page template | `templates/pages` | `backend/webclippings/templates/pages/home.html` |
| `backend/apps/clips/templates/clips/list.html` | clips page template | `templates/clips/pages` + clips components | `backend/apps/clips/templates/clips/pages/list.html` + `backend/apps/clips/templates/clips/components/` |
| `backend/apps/clips/templates/clips/detail.html` | clips page template | `templates/clips/pages` + clips components | `backend/apps/clips/templates/clips/pages/detail.html` + `backend/apps/clips/templates/clips/components/` |
| `backend/apps/clips/templates/clips/labels.html` | clips page template | `templates/clips/pages` + clips components | `backend/apps/clips/templates/clips/pages/labels.html` + `backend/apps/clips/templates/clips/components/` |
| `backend/apps/accounts/templates/accounts/login.html` | accounts page template | `templates/accounts/pages` + accounts components | `backend/apps/accounts/templates/accounts/pages/login.html` + `backend/apps/accounts/templates/accounts/components/` |
| `backend/apps/accounts/templates/accounts/register.html` | accounts page template | `templates/accounts/pages` + accounts components | `backend/apps/accounts/templates/accounts/pages/register.html` + `backend/apps/accounts/templates/accounts/components/` |
| `backend/apps/accounts/templates/accounts/activation_complete.html` | accounts page template | `templates/accounts/pages` + accounts components | `backend/apps/accounts/templates/accounts/pages/activation-complete.html` + `backend/apps/accounts/templates/accounts/components/` |
| `backend/apps/accounts/templates/accounts/password_reset_form.html` | accounts page template | `templates/accounts/pages` + accounts components | `backend/apps/accounts/templates/accounts/pages/password-reset-form.html` + `backend/apps/accounts/templates/accounts/components/` |
| `backend/apps/accounts/templates/accounts/password_reset_done.html` | accounts page template | `templates/accounts/pages` + accounts components | `backend/apps/accounts/templates/accounts/pages/password-reset-done.html` + `backend/apps/accounts/templates/accounts/components/` |
| `backend/apps/accounts/templates/accounts/password_reset_confirm.html` | accounts page template | `templates/accounts/pages` + accounts components | `backend/apps/accounts/templates/accounts/pages/password-reset-confirm.html` + `backend/apps/accounts/templates/accounts/components/` |
| `backend/apps/accounts/templates/accounts/password_reset_complete.html` | accounts page template | `templates/accounts/pages` + accounts components | `backend/apps/accounts/templates/accounts/pages/password-reset-complete.html` + `backend/apps/accounts/templates/accounts/components/` |
| `backend/apps/accounts/templates/accounts/password_reset_email.txt` | accounts email template | non-page templates (retain under accounts root) | `backend/apps/accounts/templates/accounts/password_reset_email.txt` (no page/component split) |
| `backend/apps/accounts/templates/accounts/password_reset_subject.txt` | accounts email template | non-page templates (retain under accounts root) | `backend/apps/accounts/templates/accounts/password_reset_subject.txt` (no page/component split) |

## Static Asset Inventory To Target Destination

| Current static asset | Type | Target destination category | Target destination |
| --- | --- | --- | --- |
| `backend/static/js/theme-controller.js` | global behavior JS | `static/js/components` | `backend/static/js/components/theme-toggle.js` |
| `backend/static/css/base.css` | global CSS | `static/css/tokens.css` + `static/css/base.css` | keep `backend/static/css/base.css`; move shared visual constants to `backend/static/css/tokens.css` |
| `backend/apps/clips/static/clips/js/list.js` | clips page orchestration + component behavior JS | `clips/js/pages` + `clips/js/components` | `backend/apps/clips/static/clips/js/pages/list.js` + `backend/apps/clips/static/clips/js/components/*.js` |
| `backend/apps/clips/static/clips/css/list.css` | clips page + component CSS | `clips/css/components` (+ global tokens/base for shared constants) | `backend/apps/clips/static/clips/css/components/*.css` with shared constants in `backend/static/css/tokens.css`/`base.css` |

## Interaction Ownership Boundaries

| Interaction | Current source | Target ownership | Planned target module |
| --- | --- | --- | --- |
| Theme toggle (icon + aria + localStorage theme persistence) | `backend/static/js/theme-controller.js` + base nav markup | Component-level (global) | `backend/static/js/components/theme-toggle.js` + `backend/webclippings/templates/components/theme-toggle.html` |
| Authenticated quick search input/panel, keyboard navigation, API fetch to `/api/clips/quick-search/` | `backend/apps/clips/static/clips/js/list.js` + nav markup in `base.html` | Component-level (global) | `backend/static/js/components/quick-search-nav.js` + `backend/webclippings/templates/components/quick-search-nav.html` |
| Label filter sidebar expand/collapse + search + show more/less | `backend/apps/clips/static/clips/js/list.js` + `clips/list.html` | Component-level (clips) | `backend/apps/clips/static/clips/js/components/label-filter-sidebar.js` |
| Label filter drawer open/close + backdrop + escape behavior (mobile) | `backend/apps/clips/static/clips/js/list.js` + `clips/list.html` | Component-level (clips) | `backend/apps/clips/static/clips/js/components/label-filter-drawer.js` |
| Label toggling/query mutation + selected label pills + clear-all behavior | `backend/apps/clips/static/clips/js/list.js` + links/buttons in `clips/list.html` | Page-level orchestration for URL state; component-level for trigger UI | Page: `backend/apps/clips/static/clips/js/pages/list.js`; component hooks in label filter and selected-filters components |
| Clip delete flow (`DELETE` request, row removal, forbidden/error handling) | `backend/apps/clips/static/clips/js/list.js` + clip row buttons | Component-level (clips list item) | `backend/apps/clips/static/clips/js/components/clip-list-item.js` initialized by clips list page entrypoint |
| Labels CRUD forms on labels page (create/update/delete POST forms) | `backend/apps/clips/templates/clips/labels.html` server-rendered forms | Page-level server form flow (no JS required) | `backend/apps/clips/templates/clips/pages/labels.html` + form components |
| Clip detail label edit form (comma-separated labels POST) | `backend/apps/clips/templates/clips/detail.html` server-rendered form | Page-level server form flow (no JS required) | `backend/apps/clips/templates/clips/pages/detail.html` + detail form component |
| Auth flows (sign in/register/password reset/activation) | accounts templates + Django auth views | Page-level server form flow (no JS required) | `backend/apps/accounts/templates/accounts/pages/*.html` + reusable auth card/form components |

## Migration Sequencing Notes
- T002: create global scaffold (`layouts/components`, `tokens.css`, component directories) first.
- T003: split base shell and extract global components (theme toggle + quick search shell).
- T004+: move route templates to page entrypoints and progressively split clips/accounts/home into app/global components.
