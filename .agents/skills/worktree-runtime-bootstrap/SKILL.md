---
name: worktree-runtime-bootstrap
description: Bootstrap and verify per-worktree backend and extension runtime for local development in this repository. Use when asked to set up or run a worktree environment, prepare backend+extension local testing, or debug worktree runtime mismatch issues (port/host/base URL/sqlite path/runtime metadata/output extension directory).
---

# Worktree Runtime Bootstrap

Bootstrap and validate a deterministic runtime for the current git worktree.

## Trigger examples

Use this skill when the user asks things like:
- "bootstrap this worktree"
- "set up backend and extension for this worktree"
- "prepare local testing runtime"
- "fix worktree runtime mismatch"
- "verify worktree port/base URL/sqlite path"

## Workflow

1. Run `./scripts/bootstrap_worktree_runtime.sh` from this skill directory.
2. Read the summary output and report:
- worktree id
- backend host/port/base URL
- sqlite path
- extension unpacked directory
- runtime metadata files checked
3. If the script reports warnings, surface exact remediation commands.
4. If the script fails, report the failing check and stop.

## Safety constraints

- Keep authentication and CSRF behavior unchanged.
- Do not broaden any CSRF exemptions.
- Do not print or log user clip content.
- Keep SQLite worktree-scoped; avoid shared mutable DB files across worktrees.

## Outputs

Return:
- Deterministic runtime summary for the current worktree.
- Any mismatch findings and exact fixes.
- Explicit assumptions if backend server is not currently running.

## Resources

### scripts/
- `bootstrap_worktree_runtime.sh`: executes runtime bootstrap and verification end-to-end.
