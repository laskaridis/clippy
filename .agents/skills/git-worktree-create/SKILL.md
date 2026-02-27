---
name: git-worktree-create
description: Deterministically create a new git worktree for an existing branch provided by the user under project-root/.worktrees/derived-name. Use when asked to create, initialize, spin up, or add a worktree from an already existing branch while enforcing stable location and branch validation.
---

# Create Worktree

Create or reuse a worktree from an existing branch in a deterministic location: `<project-root>/.worktrees/<derived-name>`.

## Input

- <branch-name>: name of an existing branch (local or remote) to create the worktree from.

## Workflow

1. Run:
   - `<path-to-skill>/scripts/create.sh --branch "<branch-name>"`
2. Use `--dry-run` first when validating branch/path resolution without writing changes.
3. Report:
   - resolved project root
   - target worktree path
   - branch reference used
   - whether path was created or reused

## Behavior

- Resolve project root from `git rev-parse --git-common-dir` to ensure the worktree is always under the main repo root.
- Create parent worktree directory when missing: `<project-root>/.worktrees`.
- Derive a path-friednly worktree directory name from branch name by lowercasing and replacing non `[a-z0-9._-]` with `-`.
- Accept only branches:
  - local `refs/heads/<branch>`, or
  - remote `refs/remotes/origin/<branch>` (track branch in the new worktree).
- Reuse an existing matching worktree path instead of failing.

## Constraints

- Keep all new worktrees under `<project-root>/.worktrees/`.
- Refuse `master` as target branch.
- Fail when branch does not exist.
- Fail when target path exists but is not the expected worktree.

# scripts/
- `<path-to-skill>/scripts/create.sh`: deterministic create/reuse helper for existing branches.
