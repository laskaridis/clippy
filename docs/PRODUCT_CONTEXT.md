# Product Context

WebClippings is a personal web reference tool:
- A Chrome extension captures selected text from pages.
- A Django backend stores clips and labels per authenticated user.
- A server-rendered web UI lets users browse clips, edit labels, and delete data.

Primary flows:
- Capture selected text in the browser and save to `/api/clips/`.
- View personal clips in `/clips/` and clip detail pages.
- Manage labels in `/clips/labels/`.
- Authenticate via `/accounts/*`.

## Stack and Layout

- Backend: Django 5.2 + Django REST Framework (`backend/`)
- Extension: Chrome Manifest V3, vanilla JavaScript, Node test runner (`extension/`)
- Specs and API contract: `specs/001-web-clipping-app/`

Important paths:
- `backend/apps/clips/` models, HTML views, API serializers/views, tests
- `backend/apps/accounts/` auth views/templates/tests
- `backend/webclippings/` settings, URL routing, auth class
- `extension/chrome/src/` popup/content/background/shared modules
- `specs/001-web-clipping-app/contracts/openapi.yaml` API contract
