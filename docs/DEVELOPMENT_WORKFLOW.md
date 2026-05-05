# Development Workflow

This repository uses a devcontainer-first local workflow. Separate git worktrees still provide branch isolation on the host, but the `dev-sandbox` container is the place where implementation and verification commands run. The host checkout launches Dev Containers; `/workspace` inside `dev-sandbox` is the cloned repo for the active sandbox.

## Standard Sequence

1. Create or reuse a worktree under `.worktrees/`.
2. Export the sandbox inputs for that checkout and let Dev Containers generate the local env file:

   ```bash
   export GIT_AUTH_TOKEN=...
   export SANDBOX_ID=your-sandbox-id
   ```

   If the host checkout has no usable `origin` remote, or if you need to override an SSH remote with an HTTPS clone URL for the sandbox, also export `SANDBOX_REPO_URL=https://github.com/your-org/your-repo.git`.

3. Open the checkout in Dev Containers. `initializeCommand` writes `.devcontainer/.env` from `.devcontainer/.env.example` plus the sandbox inputs, and `COMPOSE_PROJECT_NAME` comes from `SANDBOX_ID`.
4. Set a unique `DJANGO_DEV_PORT` in the generated `.devcontainer/.env` if another sandbox may be running at the same time. Keep `ALLOWED_HOSTS` localhost-oriented.
5. Work inside `dev-sandbox`. The container should start idle and stay available for manual commands.
6. Start a live backend only when you need it:

   ```bash
   make backend-run
   ```

7. Verify from the host browser against `http://localhost:<DJANGO_DEV_PORT>/accounts/login/` when you need to confirm backend reachability.
8. Run the relevant test targets, then finish with the full verification gate before shipping.

## Commands

Use `make help` to see the canonical project command surface.

Common commands from inside `dev-sandbox`:

```bash
make backend-run
make backend-test-unit
make backend-test-e2e
make extension-test-unit
make extension-test-e2e
make extension-test-a11y
make all-test
make all-verify
```

## Practical Rules

- Dev Containers tooling is the supported lifecycle entrypoint for local sandbox startup.
- `initializeCommand` generates `.devcontainer/.env`; do not hand-create that file from `.env.example`.
- `GIT_AUTH_TOKEN` and `SANDBOX_ID` are required host-side inputs before opening Dev Containers.
- `SANDBOX_REPO_URL` is optional as an explicit override; otherwise `initializeCommand` derives it from the current checkout's `origin` remote and normalizes common SSH Git URLs to HTTPS for token-backed sandbox clone auth.
- `make backend-run` starts Django only when you call it explicitly.
- When two sandboxes run in parallel, each one needs its own `DJANGO_DEV_PORT`.
- The backend is verified from the host browser on `localhost`, not through worktree-specific hostnames.
- The unpacked Chrome extension loads directly from `extension/chrome`.
