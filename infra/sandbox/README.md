# Sandbox Environment

This directory contains the Docker sandbox assets for the multi-instance local
development environment described in
`docs/plans/development-sandbox-environment/spec.md`.

## Operating model

- Start or resume a named sandbox from the repository root with
  `make sandbox-start name=<id>`.
- Remove a named sandbox with `make sandbox-destroy name=<id>`.
- Develop inside the sandbox over SSH or VS Code Remote-SSH.
- Open the backend from the host browser at the printed
  `http://localhost:<web-port>` URL.
- Load the unpacked Chrome extension from the printed host path
  `.local/sandboxes/<id>/exports/extension`.

Each sandbox publishes the same deterministic web port both inside and outside
the container. The sandbox login environment exports `DJANGO_DEV_PORT`,
`DJANGO_DEV_BASE_URL`, and related backend runtime variables so existing
commands such as `make all-run` and `pnpm run build:worktree` target the host
reachable `localhost` origin without additional flags.

## Extension export flow

Build the extension inside the sandbox as usual:

```bash
cd /workspace/webclippings/extension
pnpm run build:worktree
```

The sandbox entrypoint runs a small background sync loop that mirrors the
generated unpacked extension from
`extension/.local/worktrees/<worktree-id>/chrome` inside the sandbox to the
host-visible export directory mounted at `.local/sandboxes/<id>/exports/extension`.
Load that exported directory in host Chrome.

## Files

- `Dockerfile` defines the sandbox image and pinned toolchain.
- `entrypoint.sh` handles idempotent first-boot and restart bootstrap.
- `.env.example` documents the host-side secrets the sandbox consumes.
