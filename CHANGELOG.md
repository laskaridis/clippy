# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Clips list filtering supports combined label and URL filters with clear-all behavior that preserves non-filter query params.
- Backend quick-search coverage now includes browser E2E tests (`apps.clips.tests.e2e.test_quick_search_e2e`) and a dedicated `backend/scripts/test-e2e.sh` entrypoint.

### Changed
- Label filtering URL state is now canonicalized through shared query utilities (trim/lowercase/deduplicate) so filter links are stable and shareable.
- Backend CI now runs Django test suites in two phases: non-E2E (`--exclude-tag=e2e`) and E2E (`--tag=e2e`).
- Clips backend module structure now uses `apps.clips.views/` and `apps.clips.services/` packages instead of single-file modules.

### Fixed
- Label API list responses now consistently return a flat catalog payload (`name`, `slug`, `color`) for the authenticated user.

### Removed
- Legacy `design-system/` static prototype assets were removed from the repository.

### Deprecated
- None.

### Security
- None.
