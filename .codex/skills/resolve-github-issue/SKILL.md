---
name: resolve-github-issue
description: Resolve a GitHub issue end to end with strict execution gates. Use when asked to work on, fix, implement, pick up, or resolve a specific issue number. Enforce this sequence: read issue, set project status to In progress, create a worktree branch from origin/master, implement and self-review, run unit and e2e tests, commit and push, and open a PR that includes Fixes #<issue>.
---

# Resolve GitHub Issues

Follow this workflow in order. If any step fails, stop and report the exact failed command and cause.

## Scripts

Use these helpers as the default execution path:
- `.codex/skills/resolve-github-issue/scripts/pickup_gh_issue.sh`
- `.codex/skills/resolve-github-issue/scripts/setup_worktree.sh`
- `.codex/skills/resolve-github-issue/scripts/run_required_tests.sh`
- `.codex/skills/resolve-github-issue/scripts/create_gh_pull_request.sh`

## Start Gate

Complete before any edits:
1. Confirm trigger match and announce skill activation in one line.
2. Run `.codex/skills/resolve-github-issue/scripts/pickup_gh_issue.sh <ISSUE_NUMBER>`.
3. Summarize requirements and acceptance criteria from issue output.

## Execution Gate

Complete before implementation:
1. Run `git status --short --branch` and confirm state (or acknowledge unrelated changes).
2. Run `.codex/skills/resolve-github-issue/scripts/setup_worktree.sh <ISSUE_NUMBER> [BRANCH] [WORKTREE_DIR]`.
3. Enter the printed worktree path and print `pwd`.

Constraint: perform all edits inside the worktree path.

## Implementation and Verification

1. Implement the issue scope only.
2. Run local self-review via `git diff`; fix any problems found.
3. Run all required tests via `.codex/skills/resolve-github-issue/scripts/run_required_tests.sh`.
4. If tests fail, fix and rerun until all required tests pass.

## Delivery Gate

Complete before claiming done:
1. Create commit(s) referencing `#<ISSUE_NUMBER>`.
2. Prepare PR body in a file.
3. Run `.codex/skills/resolve-github-issue/scripts/create_gh_pull_request.sh <ISSUE_NUMBER> --body-file <PATH> [--title <TITLE>]`.
4. Confirm PR output URL and report it.

Rules:
- Always create PR content using `--body-file` (or equivalent) instead of inline shell strings.
- Do not use inline backticks/markdown in shell-interpolated arguments.

## Conclusion Gate

Provide a final report with:
- issue summary
- files changed
- test commands and results
- commit hash(es)
- PR URL

## Hard constraints:
- Do not skip any step.
- Do not create a PR if tests are failing.
- Do not mark work complete without a PR.
- Do not start implementation before Start Gate is satisfied.
- Do not claim done before Delivery Gate is satisfied.
- Do not close the issue automatically; let maintainers review and close it.
