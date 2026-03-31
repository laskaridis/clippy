# Sandbox Environment

This directory contains the Docker sandbox assets for the multi-instance local
development environment described in
`docs/plans/development-sandbox-environment/spec.md`.

## Required host inputs

`make sandbox-start name=<id>` requires only these host secrets:

- `OPENAI_API_KEY`
- `GH_TOKEN`

Optional OpenAI settings:

- `OPENAI_BASE_URL`
- `OPENAI_ORG_ID`
- `OPENAI_PROJECT_ID`

SSH access also assumes the host already has a public key in one of the default
locations checked by the Makefile: `~/.ssh/id_ed25519.pub`,
`~/.ssh/id_ecdsa.pub`, or `~/.ssh/id_rsa.pub`.

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

The sandbox id must contain only lowercase letters, numbers, and hyphens.
`sandbox-start` derives the container name, Docker volumes, SSH port, web port,
and host export path from that id. Reusing the same id reuses the same sandbox
resources.

## Start and connect

From the repository root:

```bash
make sandbox-start name=alpha
```

The command prints the exact access details for that sandbox:

```text
Sandbox: webclippings-sandbox-alpha
SSH: ssh agent@localhost -p <ssh-port>
VS Code Remote-SSH: agent@localhost:<ssh-port>
Web app: http://localhost:<web-port>
Repo: /workspace/webclippings
Extension export: .local/sandboxes/alpha/exports/extension
```

Use those values directly:

- SSH with `ssh agent@localhost -p <ssh-port>`.
- In VS Code Remote-SSH, connect to `agent@localhost:<ssh-port>`.
- Work inside `/workspace/webclippings` after connecting.
- Open the printed `http://localhost:<web-port>` URL in the host browser.

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

## Restart, recovery, and cleanup

`make sandbox-start name=<id>` is idempotent:

- If the named container already exists and is stopped, the command restarts it.
- If the named container is already running, the command keeps using it.
- If the sandbox volumes already exist, the workspace clone, home directory, and
  PostgreSQL data are reused instead of recreated.

If startup fails partway through, fix the underlying problem and rerun the same
`make sandbox-start name=<id>` command. Use `make sandbox-destroy name=<id>`
only when you want to remove that sandbox container, its named Docker volumes,
and its host export directory and start from a clean slate.

Port allocation is deterministic per sandbox id. If the derived SSH or web port
is already in use on the host, `sandbox-start` fails with a message that names
the sandbox id, the port type, and the conflicting port. It does not silently
pick a different port.

## Files

- `Dockerfile` defines the sandbox image and pinned toolchain.
- `entrypoint.sh` handles idempotent first-boot and restart bootstrap.
- `.env.example` documents the host-side secrets the sandbox consumes.
