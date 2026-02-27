---
name: git-worktree-cleanup
description: Safely remove a completed git worktree with strict verification gates. Use when asked to clean up, remove, tear down, or delete a worktree after work is done. Require that the worktree is clean and branch commits are pushed to origin before removal.
---

# Cleanup Worktree

## When to use

Use this skill when asked to:
- clean up current worktree 
- remove worktree 
- tear down worktree 
- delete worktree 
- any similar request referencing a specific worktree path either directly or indirectly.

## Tooling

Use this helper as the default path:
- `<path-to-skill>/scripts/cleanup.sh`

## Execution

1. `cd` to the linked worktree to be removed.
2. Run `<path-to-skill>/scripts/cleanup.sh`.
3. `cd` to project root after cleanup.
4. Report the removed path.

## Hard Constraints

- Do not remove a worktree with uncommitted/staged/untracked changes.
- Do not remove a worktree if local commits are not pushed to the tracking branch.
- Do not run `git worktree remove` from inside the worktree being removed; the script must change to the project root first.
