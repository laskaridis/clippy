---
name: resolve-github-issue
description: Resolve a specific GitHub issue by implementing its scope and creating a PR.
---

# Resolve GitHub Issues

Guide to resolve a specific GitHub issue by implementing its scope and creating a PR.

## Prerequisites

Ensure gh is authenticated (for example, run `gh auth login` once), then run `gh auth status` with escalated
permissions (include workflow/repo scopes) so gh commands succeed. If sandboxing blocks gh auth status,
rerun it with `sandbox_permissions=require_escalated`.

## When to use

User asks you to:
- work on issue <number>
- fix issue <number>
- implement issue <number>
- pick up issue <number>
- resolve issue <number>
- any similar request referencing a specific issue number in GitHub.

## Inputs

* `number` (required): The GitHub issue number to work on.

## Worfkflow

Follow this workflow in order. If any step fails, stop and report the exact failed command and cause:

1. Read referenced issue <number> from GitHub to understand the scope of the changes until 
   confident (make sure to check description, comments or referenced attachements - if any).
2. Plan your implemenation approach. If you have any question or doubt, ask for clarification
   before starting to work on the issue.
3. Run `<path-to-skill>/scripts/gh_update_issue.py --issue <number>` to assign issue <number>
   to @me and set its project status to "In progress".
4. Create a new git worktree branch under `<project-home>/.worktrees` from `origing/master` with a
   name related to the issue <number> and title.
5. Implement the issue's scope only, then self-refiew and fix all problems found.
6. Make sure to run all required tests and fix any failing test until all tests pass.
7. Commit and push your work in git with a clear message specifying intent.
8. Run `<path-to-skill>/scripts/gh_create_pr.sh` to create a PR referencing the issue number with "Fixes #<issue_number>" in the body, and a clear description of the work done.

## Tooling and scripts

- Use `gh` CLI to interact with GitHub issues and PRs.
- Use `<path-to-skill>/scripts/gh_update_issue.py` to update issue assignee/status (for pickup: assign to @me + set "In progress").
- Use `<path-to-skill>/scripts/gh_create_pr.sh` for PR creation.

## Quality expectations

- All requrements mentioned in the issue have been effectively addressed.
- Your work has been tested and all tests pass.
- Your PR is well formatted, includes a clear description, and references the issue number.
- Your work adhears to the `docs/TESTING.md` expectations included in the project.
- Your work adhears to the `docs/CODE_QUALITY.md` expectations included in the project.
- Your work adhears to the `docs/SECURITY.md` exepectations included in the project.
- Your work adhears to the `docs/ARCHITECTURE.md` expectations included in the project.

## Hard constraints:

- Always do your work on a separate worktree branch created from origin/master.
- Do not skip or re-order any step in the workflow.
- Do not create a PR if tests are failing.
- Do not mark work complete without a PR.
- Do not close the issue automatically; let maintainers review and close it.
