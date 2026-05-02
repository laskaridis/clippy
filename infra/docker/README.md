# Docker setup for local development

This directory contains container assets for local development.

## Stack

The local stack is defined in `infra/docker/docker-compose.yml` and supports
the `dev-sandbox` devcontainer service plus the shared `postgres` service.

- `dev-sandbox` as the idle development sandbox started through Dev Containers
- `postgres` with persistent volume and healthchecks

### How to configure the local environment

Dev Containers tooling is the supported lifecycle entrypoint for local worktree
sandboxes. Use the `dev-sandbox` service defined under `.devcontainer/` for
implementation work, then run project commands from inside that container.
The only host-visible backend contract is the `DJANGO_DEV_PORT` exposed by the
devcontainer; PostgreSQL stays on the compose network and does not publish a
host port.

## Next Services

This compose file is intentionally minimal and is the base for adding local app
services as deployment assets are introduced.
