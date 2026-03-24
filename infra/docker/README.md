# Docker setup for local development

This directory contains container assets for local development.

## Stack

The local stack is defined in `infra/docker/docker-compose.yml` and includes:

- `postgres` with persistent volume and healthchecks

### How to configure the local environment

Use the worktree-aware bootstrap flow from repository root.
`make local-env-start` resolves deterministic per-worktree runtime metadata through `backend/scripts/bootsrap.sh`.
You can inspect the resolved runtime directly from `backend/`:
```bash
cd backend
./scripts/bootsrap.sh --print-json
./scripts/bootsrap.sh --print-env-path
```

### Starting the stack

Preferred (worktree-aware) command from repository root:

```bash
make local-env-start
```

### Stopping the stack

Preferred (worktree-aware) command from repository root:

```bash
make local-env-stop
```

### Checking stack status

Preferred (worktree-aware) command from repository root:

```bash
make local-env-status
```

### Tearing down the stack

Preferred (worktree-aware, destructive) command from repository root:

```bash
make local-env-teardown
```

This command is destructive for the local database because it removes compose
volumes for the active worktree.

## Next Services

This compose file is intentionally minimal and is the base for adding local app services (for example, backend container) as deployment assets are introduced.
