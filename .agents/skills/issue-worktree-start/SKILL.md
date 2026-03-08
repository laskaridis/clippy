---
name: issue-worktree-start
description: Start a task in full workflow compliance by ensuring/assigning issue state and creating a dedicated feature branch worktree under .worktrees.
---

# Issue + Worktree Start

Use this skill to start implementation work in a compliant way.

## When to use

- "start work on issue <number>"
- "create a worktree for this issue"
- "set up branch and issue before implementation"

## Workflow

1. Run `<path-to-skill>/scripts/start.sh --issue <number> --slug <task-slug>`.
2. If requested, include `--bootstrap` to initialize backend/extension runtime.
3. Move into the created worktree and run `scripts/agent-preflight.sh --issue <number> --require-issue`.

## Guarantees

- Branch naming: `feature/<slug>`
- Worktree path: `.worktrees/<slug>`
- Issue assignment to `@me` + `in progress` label
