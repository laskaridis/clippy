# Development Workflow

This repository follows a branch-based workflow to keep `master` always releasable.

## Branch Naming

- `feature/*`: default branch type for all planned work (features, refactors, chores).
- `hotfix/*`: urgent production fixes.
- `docs/*` (optional): documentation-only changes when a dedicated docs branch is useful.

Use short, descriptive suffixes, for example:
- `feature/agent-guidelines`
- `hotfix/login-redirect-loop`
- `docs/workflow-guidelines`

## Day-to-Day Flow

1. Branch from the latest `master`.
2. Implement changes and run relevant tests.
3. Open a pull request into `master`.
4. Merge only after review and passing checks.
5. Use squash merge for pull requests into `master`.

## Merge Strategy

- Fast-forward-only merges are not required.
- Prefer squash merges to keep `master` history concise and releasable.

## Release Policy

- `master` must remain in a releasable state at all times.
- Create release tags from `master` only.
- Do not tag releases from feature or hotfix branches.
