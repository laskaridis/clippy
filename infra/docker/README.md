# Docker setup for local development

This directory contains container assets for local development.

## Stack

The local stack is defined in `infra/docker/docker-compose.yml` and supports
the `dev-sandbox` devcontainer service plus the shared `postgres` service.

- `dev-sandbox` as the idle development sandbox started through Dev Containers
- `postgres` with persistent volume and healthchecks

### How to configure the local environment

Dev Containers tooling is the supported lifecycle entrypoint for local
development. The host checkout is launcher-side only: it supplies the
`.devcontainer/` files and docs, but it is not the live workspace for a
running sandbox.

When a sandbox starts, `dev-sandbox` clones the repository into its own
`/workspace` named volume and reuses that clone when the same `SANDBOX_ID` is
reopened. `COMPOSE_PROJECT_NAME=${SANDBOX_ID}` keeps the workspace volume and
other Compose resources isolated per sandbox.

Run project commands from inside `/workspace` in `dev-sandbox`. The only
host-visible backend contract is the `DJANGO_DEV_PORT` exposed by the
devcontainer; PostgreSQL stays on the compose network and does not publish a
host port.

## Next Services

This compose file is intentionally minimal and is the base for adding local app
services as deployment assets are introduced.
