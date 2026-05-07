# Development Workflow

This repository uses a Docker sandbox workflow. Separate git worktrees still provide branch isolation on the host, but the `dev-sandbox` container is the place where implementation and verification commands run. `/workspace` inside `dev-sandbox` is the cloned repo for the active sandbox.

## Standard Sequence

1. Create or reuse a worktree under `.worktrees/`.
2. Create a sandbox env file for that checkout before starting the sandbox:

   ```bash
   cp .sandbox/.env.example .sandbox/.env
   ```

   Then edit `.sandbox/.env` for that sandbox and set at least:

   ```dotenv
   GIT_AUTH_TOKEN=...
   SANDBOX_ID=your-sandbox-id
   SANDBOX_REPO_URL=https://github.com/your-org/your-repo.git
   ```

   Use an HTTPS repository URL so the sandbox can clone and authenticate with the token-backed Git helper. Keep any per-sandbox overrides such as `DJANGO_DEV_PORT` in that same `.sandbox/.env` file.

3. Start the sandbox from the repository root:

   ```bash
   .sandbox/bin/start
   ```

4. Open a shell in `dev-sandbox`:

   ```bash
   .sandbox/bin/bash
   ```

5. On a fresh sandbox, install project dependencies from inside `/workspace`:

   ```bash
   make all-init
   ```

6. Work inside `dev-sandbox`. The container starts idle and stays available for manual commands.
7. Start a live backend only when you need it:

   ```bash
   make backend-run
   ```

8. Verify from the host browser against `http://localhost:<DJANGO_DEV_PORT>/accounts/login/` when you need to confirm backend reachability.
9. Run the relevant test targets, then finish with the full verification gate before shipping.
10. Tear the sandbox down when you no longer need it:

   ```bash
   .sandbox/bin/teardown
   ```

## Commands

Use `make help` to see the canonical project command surface.

Common commands from inside `dev-sandbox`:

```bash
make all-init
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

- `.sandbox/bin/start`, `.sandbox/bin/bash`, and `.sandbox/bin/teardown` are the supported lifecycle entrypoints for local sandbox work.
- `GIT_AUTH_TOKEN`, `SANDBOX_ID`, and `SANDBOX_REPO_URL` must be set in the per-sandbox `.sandbox/.env` before startup.
- `.sandbox/.env.example` is the checked-in template. Copy it to local `.sandbox/.env` and keep secrets only in that untracked file.
- `make backend-run` starts Django only when you call it explicitly.
- When two sandboxes run in parallel, each one needs its own `DJANGO_DEV_PORT`.
- The backend is verified from the host browser on `localhost`, not through worktree-specific hostnames.
- The unpacked Chrome extension loads directly from `extension/chrome`.
