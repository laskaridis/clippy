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

