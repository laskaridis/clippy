# 0006: Adopt devcontainer-first local runtime orchestration for worktree development

- Status: Accepted
- Date: 2026-05-02

## Context

ADR 0003 standardized a worktree backend entrypoint and generated per-worktree env artifacts. That decision reflected the repository's earlier local-development model, where host-side scripts coordinated backend startup and runtime isolation.

The project has since moved to a devcontainer-first workflow. Each worktree should act as its own development sandbox, with local runtime orchestration handled through Dev Containers tooling rather than through host-side bootstrap scripts or generated runtime files.

## Decision

This ADR supersedes `0003-worktree-backend-entrypoint-and-env-contract` for local development.

Specifically:

1. `dev-sandbox` is the idle development sandbox container for implementation and verification work.
2. `DJANGO_DEV_PORT` is the host-visible differentiator for parallel worktrees.
3. PostgreSQL stays on the compose network and is not published on a host port by default.
4. The extension loads directly from `extension/chrome` during local development.

## Consequences

### Positive

- The local workflow becomes simpler and more explicit: worktree, devcontainer, sandbox, backend command.
- Parallel worktrees can run without host-port collisions as long as they use distinct `DJANGO_DEV_PORT` values.
- The extension workflow no longer depends on generated worktree runtime artifacts.

### Negative

- Developers must manage the backend port explicitly when running multiple worktrees in parallel.
- Local extension configuration may be rewritten in place for the active worktree.

### Neutral

- ADR 0003 remains as a historical record of the earlier runtime contract.
- Compose-managed isolation still depends on starting each worktree through Dev Containers tooling.
