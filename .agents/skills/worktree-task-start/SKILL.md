---
name: worktree-task-start
description: Start a task in workflow compliance by creating a dedicated feature branch worktree under .worktrees without GitHub issue integration.
---

# Worktree Task Start (Issue-less)

Use this skill to start implementation work when no GitHub issue integration is needed.

## When to use

- "start work on this feature"
- "create a worktree for this task"
- "set up branch/worktree without issue linkage"

## Workflow

1. Run `<path-to-skill>/scripts/start.sh --slug <task-slug>`.
2. Optionally include `--base <branch>`.
3. Move into the created worktree and run `scripts/agent-preflight.sh`.

## Guarantees

- Branch naming: `feature/<slug>`
- Worktree path: `.worktrees/<slug>`
- No issue assignment or issue label mutation

