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

When working on multiple features in parallel with `git worktree`, each worktree must be able to boot the backend independently.

- Use `backend/scripts/runserver_worktree.sh` to start Django in local development.
- The script derives a deterministic per-worktree default port and SQLite path.
- The script ensures an admin user exists before startup (defaults: `admin` / `admin`; override with `DJANGO_ADMIN_USERNAME`, `DJANGO_ADMIN_EMAIL`, `DJANGO_ADMIN_PASSWORD`) using Django auth APIs. It is disabled when `DJANGO_ENV=production` (or `ENVIRONMENT=production`) to avoid accidental production bootstrap.
- You can still override defaults with environment variables:
  - `DJANGO_DEV_PORT` (or `PORT`) for runserver port
  - `DJANGO_SQLITE_PATH` for sqlite file location
- Keep local environment values worktree-scoped where possible (for example, avoid sharing one mutable sqlite file across worktrees).

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

