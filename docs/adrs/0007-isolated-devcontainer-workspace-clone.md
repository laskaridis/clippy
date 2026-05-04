# 0007: Use per-sandbox cloned workspaces for source isolation

- Status: Accepted
- Date: 2026-05-04

## Context

ADR 0006 established the devcontainer-first local runtime model. That decision
still left `/workspace` conceptually tied to the host checkout, which meant a
running sandbox could observe host edits directly.

For isolated sandbox development, each `SANDBOX_ID` needs its own cloned copy
of the repository inside a named Docker volume. The host checkout must remain
launcher-side only: it provides `.devcontainer/` metadata, docs, and launch
context, but it is not the live workspace for a running sandbox.

## Decision

This ADR supersedes the bind-mounted local-workspace assumption from ADR 0006
for sandbox source isolation.

Specifically:

1. `dev-sandbox` mounts a per-sandbox named volume at `/workspace`.
2. The first start for a `SANDBOX_ID` clones `SANDBOX_REPO_URL` into
   `/workspace`, then reuses that clone on reopen.
3. `COMPOSE_PROJECT_NAME=${SANDBOX_ID}` keeps the sandbox volume and related
   Compose resources isolated per sandbox.
4. The live workspace inside the sandbox is the cloned repository, not the host
   checkout.

## Consequences

### Positive

- Host edits no longer mutate the active sandbox workspace.
- Reopening the same `SANDBOX_ID` preserves branch and working-tree state.
- Parallel sandboxes remain isolated through distinct Compose project names and
  workspace volumes.

### Negative

- Startup now depends on an explicit repository URL and sandbox identity.
- The sandbox workspace must be opened and modified inside `dev-sandbox`
  instead of directly from the host checkout.

### Neutral

- ADR 0006 remains the historical record for the broader devcontainer-first
  runtime orchestration model.
- The isolated clone model extends that runtime decision without rewriting the
  earlier record.
