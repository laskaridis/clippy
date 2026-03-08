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

```bash
cd infra/docker
docker compose up -d
```

### Tearing down the stack 

```bash
cd infra/docker
docker compose down
```

To remove all volumes too:

```bash
cd infra/docker
docker compose down -v
```

## Next Services

This compose file is intentionally minimal and is the base for adding local app services (for example, backend container) as deployment assets are introduced.
