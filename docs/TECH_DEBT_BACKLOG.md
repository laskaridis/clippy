# Tech Debt Backlog

This file tracks intentionally deferred technical debt discovered during delivery.
Keep entries actionable and current.

## Update Rules

- Add entries in the branch where debt is identified.
- Prefer updating existing entries instead of creating duplicates.
- Keep status accurate (`Open`, `In progress`, `Blocked`, `Resolved`).
- Link related GitHub issue(s) and PR(s) when available.

## Entry Template

### TD-000: Short description
- Scope: backend|extension|docs|infra|process|etc
- Impact: Why it matters
- Status: Open
- Created: YYYY-MM-DD
- Related: #issue, #pr
- Next actions: Concrete next action

## Backlog

### TD-005: Add a reusable sandbox validation harness for launcher, clone, and auth flows
- Scope: infra
- Impact: The isolated sandbox work repeatedly had to rediscover operational facts during manual smoke tests, especially around sandbox inputs, container reachability, clone persistence, and Git auth behavior after startup. That makes future launcher changes slower and easier to regress.
- Status: Open
- Created: 2026-05-08
- Related: `docs/plans/devcontainers/spec.md`, `docs/plans/devcontainers/ralph.txt`
- Next actions: Add one canonical automated smoke harness that verifies preflight input validation, first clone, same-`SANDBOX_ID` reopen, parallel sandbox isolation, and post-start `git fetch`/`git push` against a local authenticated test remote.

### TD-006: Make extension bootstrap fully non-interactive when stale `node_modules` exists
- Scope: extension
- Impact: Sandbox startup can appear hung when `pnpm install` prompts to replace an incompatible `extension/node_modules` tree. That is operationally brittle and easy to misdiagnose.
- Status: Open
- Created: 2026-05-08
- Related: `docs/plans/devcontainers/ralph.txt` task-21 learnings
- Next actions: Update the extension install path so bootstrap stays non-interactive in the presence of stale dependency trees, then add a regression check for that startup case.

### TD-007: Provide a canonical host-side test env path for backend verification
- Scope: testing
- Impact: Several verification steps depended on ad hoc host-shell setup for `DATABASE_URL` and related sandbox env, which makes reproduction noisy and increases the chance of false failures outside the active sandbox.
- Status: Open
- Created: 2026-05-08
- Related: `docs/plans/devcontainers/ralph.txt` task-20 and task-08b learnings
- Next actions: Add one supported host-side test invocation path for backend validation, either via a Make target or a checked-in helper, that injects the required database/runtime env consistently without reviving the old runtime bootstrap model.

### TD-002: Remove unused Clip `(user, domain)` index
- Scope: backend
- Impact: The `(user, domain)` index appears unused by current product query paths; keeping it adds unnecessary write/storage overhead and schema complexity.
- Status: Open
- Created: 2026-02-28
- Related: Clip model index review (models.Index(fields=["user", "domain"]))
- Next actions: Validate with query plans/usage telemetry, then create migration to drop `clips_clip_user_id_680d9b_idx` and remove the corresponding model index declaration.

### TD-003: Decide UUID-to-slug compatibility window for label filters
- Scope: backend
- Impact: Label filtering now relies on slugs; without a transitional UUID fallback, legacy `?label=<uuid>` links will not resolve if such links ever exist after release.
- Status: Open
- Created: 2026-03-16
- Related: PR #54, review thread `discussion_r2939153392`
- Next actions: Before first public release that includes slug filtering, decide whether to add a UUID fallback path in label resolution or explicitly reject invalid legacy filters with a visible user message.

### TD-004: Resolve overlapping `Escape` handlers in clips list UI
- Scope: backend
- Impact: `Escape` key handling can close both quick search and drawer layers in one keypress, causing surprising keyboard UX and potential state inconsistency when multiple overlays are open.
- Status: Open
- Created: 2026-03-24
- Related: `docs/plans/label-filter-sidebar/code-review-findings-2026-03-24.md` (ISSUE-01)
- Next actions: Update `backend/apps/clips/static/clips/js/list.js` to enforce top-layer-first Escape behavior (e.g., stop propagation in quick search Escape handler and/or guard document-level drawer Escape handler when quick search is open), then add/extend tests for overlay keyboard interaction.
