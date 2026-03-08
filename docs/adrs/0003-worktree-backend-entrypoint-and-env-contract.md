# 0003: Standardize worktree backend lifecycle on a single entrypoint + shared env artifacts

- Status: Accepted
- Date: 2026-02-28

## Context

Backend lifecycle logic became fragmented across scripts, extension tooling, E2E tests, and CI steps. Multiple places ran intermediate steps (database readiness checks, migrations, runtime resolution), which increased drift risk and made worktree behavior harder to reason about.

The project also needs deterministic per-worktree isolation while allowing parallel worktrees to run concurrently with different settings.

## Decision

Adopt `backend/scripts/bootsrap.sh` as the single backend lifecycle contract for local and automation workflows.

Specifically:

1. The script is responsible for runtime resolution, database readiness, migrations/bootstrap, and backend startup.
2. Tooling that depends on backend runtime state (extension worktree prep, E2E startup) must use this script instead of reproducing bootstrap steps.
3. The script must emit shared per-worktree artifacts under `backend/.local/`:
   - `worktree-runtime-<worktree-id>.json`
   - `worktree-env-<worktree-id>.env`
4. Worktree-specific settings are derived deterministically (ports/host/db identifiers) and can still be overridden via environment variables.

## Consequences

### Positive

- Backend startup semantics are centralized and consistent across local and CI usage.
- Worktree isolation is explicit via generated runtime/env artifacts.
- Extension/E2E tooling can consume one stable backend contract instead of duplicating migration/readiness logic.

### Negative

- The backend launcher script becomes a critical integration point and must remain backward-compatible for existing tooling.
- Some commands that previously looked lightweight (runtime resolution) may now validate/start database dependencies to avoid stale contracts.

### Neutral

- Per-worktree `.local` artifacts are expected and intentionally ephemeral.
- Existing environment override knobs remain available for advanced local setups.
