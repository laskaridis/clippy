---
name: cleanup-worktree
description: Safely remove a completed git worktree with strict verification gates. Use when asked to clean up, remove, tear down, or delete a worktree after work is done. Require that the worktree is clean and branch commits are pushed to origin before removal.
---

# Cleanup Worktree

Run this workflow when worktree implementation is complete and local work is already pushed.

## Script

Use this helper as the default path:
- `.codex/skills/cleanup-worktree/scripts/cleanup_worktree.sh`

## Execution

1. Enter the linked worktree to be removed.
2. Run `.codex/skills/cleanup-worktree/scripts/cleanup_worktree.sh`.
3. Report the removed path.

## Hard Constraints

- Do not remove a worktree with uncommitted/staged/untracked changes.
- Do not remove a worktree if local commits are not pushed to the tracking branch.
- Do not run `git worktree remove` from inside the worktree being removed; the script must change to the project root first.
