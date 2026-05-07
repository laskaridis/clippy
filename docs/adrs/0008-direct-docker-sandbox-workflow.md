# 0008: Adopt direct Docker sandbox lifecycle for local development

- Status: Accepted
- Date: 2026-05-07

## Context

ADR 0006 and ADR 0007 captured the earlier local-development model built around
Dev Containers plus an isolated cloned workspace. The repository has since
removed `.devcontainer/` in favor of a simpler checked-in Docker sandbox under
`.sandbox/`.

The current implementation no longer relies on Dev Containers to launch or
attach to the sandbox. Instead, the repository provides direct wrapper scripts
for startup, shell access, and teardown while preserving the same core runtime
shape: `dev-sandbox` remains the implementation container, PostgreSQL stays on
the Compose network, and `/workspace` remains a per-sandbox cloned repository.

## Decision

This ADR supersedes the Dev Containers launcher assumptions in ADR 0006 and ADR
0007 for day-to-day local development.

Specifically:

1. `.sandbox/bin/start` is the supported entrypoint for starting the local
   Docker sandbox.
2. `.sandbox/bin/bash` is the supported entrypoint for opening an interactive
   shell in `dev-sandbox`.
3. `.sandbox/bin/teardown` is the supported entrypoint for tearing the sandbox
   down, including the named workspace volume.
4. `.sandbox/docker-compose.yml` is the canonical launcher config for the local
   sandbox stack.
5. `GIT_AUTH_TOKEN`, `SANDBOX_ID`, and `SANDBOX_REPO_URL` are explicit startup
   inputs for the current sandbox contract.

## Consequences

### Positive

- Local startup is simpler and more transparent because it uses direct Docker
  wrapper scripts instead of Dev Containers orchestration.
- The repository keeps the isolated `/workspace` clone model without requiring
  editor-specific container tooling.
- The local workflow is easier to document because startup, shell access, and
  teardown each have a single checked-in command.

### Negative

- A fresh sandbox now requires a manual dependency bootstrap step such as
  `make all-init`.
- The startup contract currently depends on explicitly providing
  `SANDBOX_REPO_URL` rather than deriving it automatically.

### Neutral

- ADR 0006 remains the historical record for the original containerized local
  runtime direction.
- ADR 0007 remains the historical record for why `/workspace` is an isolated
  per-sandbox clone.
