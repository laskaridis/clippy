# Development Workflow

This repository uses a devcontainer-first local workflow. Separate git worktrees still provide branch isolation, but the `dev-sandbox` container is the place where implementation and verification commands run.

## Standard Sequence

1. Create or reuse a worktree under `.worktrees/`.
2. Create the local env file for that checkout:

   ```bash
   cp .devcontainer/.env.example .devcontainer/.env
   ```

3. Set a unique `DJANGO_DEV_PORT` in `.devcontainer/.env` if another worktree may be running at the same time. Keep `ALLOWED_HOSTS` localhost-oriented.
4. Open the worktree in Dev Containers. The `dev-sandbox` service should start idle and stay available for manual commands.
5. Do implementation work inside `dev-sandbox`.
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
- `make backend-run` starts Django only when you call it explicitly.
- When two worktrees run in parallel, each one needs its own `DJANGO_DEV_PORT`.
- The backend is verified from the host browser on `localhost`, not through worktree-specific hostnames.
- The unpacked Chrome extension loads directly from `extension/chrome`.
