---
name: feature-delivery-gate
description: Run a standardized delivery gate before handoff by enforcing preflight checks, tests, and issue/PR state verification.
---

# Feature Delivery Gate

Use this skill before opening or handing off a PR.

## Workflow

1. Run `<path-to-skill>/scripts/gate.sh --issue <number>` from the worktree root.
2. Optionally include `--full-tests` to run `./scripts/test_worktree.sh`.
3. Include `--to-review` to move issue label from `in progress` to `in review`.

## Default checks

- `scripts/agent-preflight.sh --issue <number> --require-issue`
- backend smoke validation in current worktree
- branch upstream + open PR verification
