# Development Workflow

## Development workflow

Upon a request from the user the coding agent ALWAYS follows the following steps
in-order:

1. Create a feature branch from latest `master`.
2. Create a git worktree for that branch under `.worktrees`.
3. Implement changes and run relevant tests.
4. Review your code locally and fix any issues (make sure all tests pass).
5. Open a pull request into `master`.

### Enforced preflight gate

Before editing code, run:

```bash
scripts/agent-preflight.sh
```

This command fails unless all hard gates are met:
- branch is `feature/<slug>`
- current working directory is under `.worktrees/<name>`

For a one-command compliant task bootstrap, use:

```bash
scripts/start-worktree-task.sh <task-slug> [base-branch]
```

This creates a compliant worktree/branch.

### Orchestrated multi-agent workflow

For complex feature delivery, use an ORCHESTRATOR-led loop with strict role boundaries:

1. ORCHESTRATOR delegates to CODER.
2. CODER implements code + automated tests in the assigned worktree.
3. ORCHESTRATOR delegates to VERIFICATION.
4. VERIFICATION reviews against request scope and quality gates (functionality, test coverage, bugs, code quality, security, and a11y when applicable).
5. If VERIFICATION fails, ORCHESTRATOR delegates back to CODER with prioritized findings.
6. Repeat CODER -> VERIFICATION until VERIFICATION passes, or up to 3 failed cycles.
7. If 3 failed cycles are reached, ORCHESTRATOR escalates to the user with blocker summary and recommended options.
8. Once VERIFICATION passes, ORCHESTRATOR delegates to SHIPPING.
9. SHIPPING creates or updates the PR and reports status.
10. If the user requests PR fixes, ORCHESTRATOR restarts CODER -> VERIFICATION -> SHIPPING.

Hard rules:

- ORCHESTRATOR never implements code directly.
- VERIFICATION is mandatory between CODER and SHIPPING.
- SHIPPING runs only after VERIFICATION pass.
- Work must always remain in a dedicated `.worktrees/*` worktree on `feature/<slug>`.
- Multiple features may be handled in parallel only by using separate worktrees and independent orchestrators.

### Emergency bypass policy

Use bypasses only for urgent incidents and always create immediate follow-up work.

- Narrow bypass (preferred): set `SKIP_FEATURE_BRANCH_CHECK=1` for a single commit.
- Broad bypass (last resort): `git commit --no-verify`.

Hard requirements when using either bypass:
- include the incident/ticket reference in the commit message
- open (or link) follow-up remediation work before end of day
- open a PR that restores full workflow compliance
- do not continue regular feature development under bypass mode

## Git branch policy

Treat all the following as **hard gates**:
- All work must be done on a dedicated feature branch, NEVER directly on the
  mainline (i.e. `master`).
- Feature branch naming MUST follow `feature/<short-description-of-feature>`
- Use lowercase letters, numbers, and hyphens in the short description 
  (example: `feature/add-clipping-tags`).
- Run `./scripts/setup-git-hooks.sh` once per clone to enforce this rule via git
  hooks.
- The pre-commit hook now runs `scripts/agent-preflight.sh` to enforce branch +
  worktree hard gates before any commit.

## Git worktree development

We use a multi-agent development workflow based on git worktrees to isolate 
work across agents working in parallel. When working on multiple features in
parallel with `git worktree`, each worktree must be able to boot the backend
and extension independently.

Consider all the following as **hard gates**:
- Every task assigned to an agent MUST be executed in a dedicated git worktree
  under `.worktrees/` on a non-`master` branch.
- If an agent is not operating in a dedicated worktree and preparing a PR, it 
  MUST stop and fail the task as non-compliant with workflow policy.
- Git worktrees for this repository MUST be created under the repository-local
  `.worktrees/` directory (for example, `<repo>/.worktrees/<worktree-name>`).
- Do NOT create project worktrees outside `.worktrees/`.
- Run exactly one backend server instance per worktree at a time. If the server
  must pick up changes, restart that instance instead of starting an additional
  runserver process on another port.
- Do NOt delete any worktree unless the task is explicitly confirmed complete
  by the user and the user explicitly asks for worktree deletion.

Guidelines to work with the codebase effectively in a worktreee: 
- Use `backend/scripts/bootsrap.sh` to start Django in local development.
- Treat `backend/scripts/bootsrap.sh` as the single backend lifecycle contract 
  for local tooling/tests (bootstrap, migrations/admin setup, runtime metadata,
  and runserver).
- Backend server entrypoints (preferred for local development):
  - Start: `cd backend && ./scripts/start-server.sh`
  - Stop: `cd backend && ./scripts/stop-server.sh`
  - Check running status/url: `cd backend && ./scripts/check-server.sh`
- If `DATABASE_URL` is not set, the script bootstraps a deterministic
  per-worktree PostgreSQL container via `infra/docker/docker-compose.yml`
  (isolated compose project, db name, and db port).
- The script derives a deterministic per-worktree default backend port and
  automatically falls forward to the next free backend port in range when
  needed.
- The script also derives a deterministic per-worktree host/base URL and writes
  a per-worktree env file (`backend/.local/worktree-env-<worktree-id>.env`) plus
  runtime JSON metadata (`--print-json`) for tooling integration.
- If Docker daemon is unavailable, set `DATABASE_URL` to a reachable PostgreSQL
  instance explicitly.
- The script ensures an admin user exists before startup (defaults: `admin` / 
  `admin`; override with `DJANGO_ADMIN_USERNAME`, `DJANGO_ADMIN_EMAIL`, 
  `DJANGO_ADMIN_PASSWORD`) using Django auth APIs. It is disabled when 
  `DJANGO_ENV=production` (or `ENVIRONMENT=production`) to avoid accidental 
  production bootstrap.
- You can still override defaults with environment variables:
  - `DJANGO_DEV_PORT` (or `PORT`) for runserver port
  - `DJANGO_DEV_HOST` for runserver host identity (used for extension 
     auth/session isolation)
  - `DJANGO_DEV_BASE_URL` for explicit backend origin
  - `DJANGO_DEV_DB_PORT`/`POSTGRES_PORT`, `DJANGO_DEV_DB_NAME`/`POSTGRES_DB`, 
    `DJANGO_DEV_DB_USER`/`POSTGRES_USER`, `DJANGO_DEV_DB_PASSWORD`/`POSTGRES_PASSWORD` for per-worktree postgres values
- For the extension in each worktree:
  - Run `cd extension && pnpm run build:worktree`.
  - Load the generated unpacked extension from `extension/.local/worktrees/<worktree-id>/chrome`.
  - E2E uses the generated runtime metadata `extension/.local/worktree-runtime-<worktree-id>.json`.
- Convenience entrypoints:
  - Full local stack (extension build + backend run): `./scripts/run_worktree_stack.sh`
  - Full test run (backend + extension unit + extension e2e): `./scripts/test_worktree.sh`
- Keep local environment values worktree-scoped where possible (for example, avoid sharing one mutable database across worktrees).

## Work hand-off

Treat the following as **hard gates**:

- Every coding agent's task must be handed off via a pull request; direct branch
  hand-off without a PR is NOT allowed.

## Release policy

- Releases are 
- `master` must remain in a releasable state at all times.
- Create release tags from `master` only.
- Do not tag releases from non-`master` branches.

# Definition of done checklist 

Before handing work back ensure all the following is ture:
[ ] Code compiles/runs.
[ ] Relevant tests pass locally.
[ ] Work was completed in a dedicated `.worktrees/` worktree (not in the user's active directory).
[ ] A pull request is opened (or ready to open) as the required sign-off path for the task.
[ ] Edge cases for auth and ownership are covered.
[ ] Migrations are included if needed.
[ ] Docs/specs are updated for behavior changes.
[ ] If an existing ExecSpec plan exists under `docs/plans/` for this task, its progress/living sections are updated before handoff (do not create a new plan just for this checklist item).
[ ] No unrelated files were changed.
