# Development Workflow

This repository follows a branch-based workflow to keep `master` always releasable.

## Branching Rules

- New feature work must be done on a dedicated non-`master` branch.
- Do not implement features directly on `master`.
- Branch naming should follow repository tooling conventions (Speckit-compatible naming).

## Day-to-Day Flow

1. Branch from the latest `master`.
2. Implement changes and run relevant tests.
3. Open a pull request into `master`.
4. Merge only after review and passing checks.
5. Use squash merge for pull requests into `master`.


## Git Worktree Development

When working on multiple features in parallel with `git worktree`, each worktree must be able to boot the backend and extension independently.

- Worktrees for this repository must be created under the repository-local `.worktrees/` directory (for example, `<repo>/.worktrees/<worktree-name>`).
- Do not create project worktrees outside `.worktrees/`.
- Do not delete any worktree unless the task is explicitly confirmed complete by the user and the user explicitly asks for worktree deletion.

- Use `backend/scripts/bootsrap.sh` to start Django in local development.
- Treat `backend/scripts/bootsrap.sh` as the single backend lifecycle contract for local tooling/tests (bootstrap, migrations/admin setup, runtime metadata, and runserver).
- If `DATABASE_URL` is not set, the script bootstraps a deterministic per-worktree PostgreSQL container via `infra/docker/docker-compose.yml` (isolated compose project, db name, and db port).
- The script derives a deterministic per-worktree default backend port and automatically falls forward to the next free backend port in range when needed.
- The script also derives a deterministic per-worktree host/base URL and writes a per-worktree env file (`backend/.local/worktree-env-<worktree-id>.env`) plus runtime JSON metadata (`--print-json`) for tooling integration.
- If Docker daemon is unavailable, set `DATABASE_URL` to a reachable PostgreSQL instance explicitly.
- The script ensures an admin user exists before startup (defaults: `admin` / `admin`; override with `DJANGO_ADMIN_USERNAME`, `DJANGO_ADMIN_EMAIL`, `DJANGO_ADMIN_PASSWORD`) using Django auth APIs. It is disabled when `DJANGO_ENV=production` (or `ENVIRONMENT=production`) to avoid accidental production bootstrap.
- You can still override defaults with environment variables:
  - `DJANGO_DEV_PORT` (or `PORT`) for runserver port
  - `DJANGO_DEV_HOST` for runserver host identity (used for extension auth/session isolation)
  - `DJANGO_DEV_BASE_URL` for explicit backend origin
  - `DJANGO_DEV_DB_PORT`/`POSTGRES_PORT`, `DJANGO_DEV_DB_NAME`/`POSTGRES_DB`, `DJANGO_DEV_DB_USER`/`POSTGRES_USER`, `DJANGO_DEV_DB_PASSWORD`/`POSTGRES_PASSWORD` for per-worktree postgres values
- For the extension in each worktree:
  - Run `cd extension && pnpm run build:worktree`.
  - Load the generated unpacked extension from `extension/.local/worktrees/<worktree-id>/chrome`.
  - E2E uses the generated runtime metadata `extension/.local/worktree-runtime-<worktree-id>.json`.
- Convenience entrypoints:
  - Full local stack (extension build + backend run): `./scripts/run_worktree_stack.sh`
  - Full test run (backend + extension unit + extension e2e): `./scripts/test_worktree.sh`
- Keep local environment values worktree-scoped where possible (for example, avoid sharing one mutable database across worktrees).

## Merge Strategy

- Fast-forward-only merges are not required.
- Prefer squash merges to keep `master` history concise and releasable.

## Release Policy

- `master` must remain in a releasable state at all times.
- Create release tags from `master` only.
- Do not tag releases from non-`master` branches.

# Delivery Checklist

Before handing work back ensure all the following is ture:
[ ] Code compiles/runs.
[ ] Relevant tests pass locally.
[ ] Edge cases for auth and ownership are covered.
[ ] Migrations are included if needed.
[ ] Docs/specs are updated for behavior changes.
[ ] No unrelated files were changed.
