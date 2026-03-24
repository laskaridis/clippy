# Docker setup for local development 

This directory contains container assets for local development.

## Stack

The local stack is defined in `infra/docker/docker-compose.yml` and includes:

- `postgres` with persistent volume and healthchecks

### Configuring a local environment

Copy the example env file and adjust values accordingly:

```bash
cd infra/docker
cp .env.example .env
```

### Starting the stack

Preferred (worktree-aware) command from repository root:

```bash
make local-env-start
```

Direct compose invocation (fallback):

```bash
cd infra/docker
docker compose up -d
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

Direct compose invocation (fallback):

```bash
cd infra/docker
docker compose down -v
```

## Next Services

This compose file is intentionally minimal and is the base for adding local app services (for example, backend container) as deployment assets are introduced.
