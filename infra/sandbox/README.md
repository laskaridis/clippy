# Sandbox Environment

This directory contains the Docker sandbox assets for the multi-instance local
development environment described in
`docs/plans/development-sandbox-environment/spec.md`.

The sandbox operating model is intentionally narrow:

- Start or resume a named sandbox from the repository root with
  `make sandbox-start name=<id>`.
- Remove a named sandbox with `make sandbox-destroy name=<id>`.
- Develop inside the sandbox over SSH or VS Code Remote-SSH.
- Open the backend from the host browser.
- Load the unpacked Chrome extension from a host-visible export directory.

The implementation in this directory is introduced incrementally:

- `Dockerfile` will define the sandbox image and pinned toolchain.
- `entrypoint.sh` will handle idempotent first-boot and restart bootstrap.
- `.env.example` documents the host-side secrets the sandbox consumes.

At this stage the directory is only the canonical skeleton for later tasks.
