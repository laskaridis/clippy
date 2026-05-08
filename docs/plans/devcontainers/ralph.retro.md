## What went well

- The implementation mostly optimized for real behavior, not just status movement. It used live sandbox runs, checked the `/workspace` mount directly, verified reopen persistence with markers, captured host-browser evidence, and later proved authenticated `git fetch`/`git push` against a local test remote instead of assuming clone success implied interactive auth success. Evidence: `task-21`, `task-25`, `task-29`, `task-30`; `docs/plans/devcontainers/login-8794.png`; `docs/plans/devcontainers/extension-8795.png`; `docker compose ... exec -T dev-sandbox ... git fetch origin` in `docs/plans/devcontainers/ralph.txt`.

- Useful lessons were pushed into reusable repo surfaces instead of being left only in the action log. `AGENTS.md` absorbed the compose-env, askpass, and doc-order rules, and the repo now tracks reusable follow-on debt in `docs/TECH_DEBT_BACKLOG.md` (`TD-005`, `TD-006`, `TD-007`). Evidence: `AGENTS.md`; `docs/TECH_DEBT_BACKLOG.md`.

## Recurring struggles

- Acceptance was not fully validated when the work first declared its "final" evidence pass. `task-29` is described as the final isolated-clone validation, but the same entry records that `git fetch` failed because "the transient askpass helper ... does not survive," and `spec.md` still called out `task-30` as follow-up work. That means the critical Git-auth acceptance criteria were discovered only after the closure-style validation task had already run. Evidence: `task-29`, `task-30`; `docs/plans/devcontainers/spec.md`; `docs/plans/devcontainers/ralph.txt` excerpt "remaining Git-auth gap".

- Validation remained heavily manual and rediscovered the same launcher facts in multiple places. The log repeatedly relied on ad hoc temp clones, local Git daemons/HTTP servers, Docker commands, and manual marker checks; the repo now carries an explicit debt item for adding a canonical harness. Evidence: `task-25`, `task-29`, `task-32`; `docs/TECH_DEBT_BACKLOG.md` `TD-005`; validation commands recorded in `docs/plans/devcontainers/ralph.txt`.

## Scope/control issues

- The agent repeatedly stepped outside the task file set to update shared guidance. Those edits were often sensible, but they weakened scope traceability because the executed change set no longer matched the task boundary. Evidence: `task-25` scope deviation "Touched AGENTS.md"; `task-30` scope deviation "`AGENTS.md` was updated ... even though it was not listed"; `AGENTS.md`.

## Prompt/task design issues

- The task graph allowed documentation and evidence tasks to close before all acceptance-critical runtime behavior was green. In `tasks.json`, `task-29` depended on documentation tasks (`task-27`, `task-28`) rather than on the later Git-auth and preflight follow-ups (`task-30`, `task-31`, `task-32`), so the plan structure itself encouraged premature "final evidence" wording. Evidence: `docs/plans/devcontainers/tasks.json`; `docs/plans/devcontainers/ralph.txt` for `task-29` and `task-30`.

- Important launcher-contract decisions did not survive the later migration into the active reusable surfaces. The historical plan decided that only `GIT_AUTH_TOKEN` and `SANDBOX_ID` should be explicit inputs and that `SANDBOX_REPO_URL` should be derived from `origin`, but the current live workflow still tells users to set `SANDBOX_REPO_URL` manually and the active init script only clones when `/workspace/.git` is absent without the richer metadata/reopen checks described in the plan. Evidence: `docs/plans/devcontainers/spec.md`; `docs/DEVELOPMENT_WORKFLOW.md`; `.sandbox/.env.example`; `.sandbox/scripts/init`; `docs/adrs/0008-direct-docker-sandbox-workflow.md`.

## Follow-up tasks

- Add a canonical sandbox smoke harness and make it part of the stable command surface.
  Scope: `Makefile`, `.sandbox/scripts/`, and the reusable validation workflow described in `docs/TESTING.md`.
  Expected outcome: future launcher or workspace changes get one repeatable command that checks input validation, first clone, same-`SANDBOX_ID` reopen, parallel isolation, and post-start `git fetch`/`git push`.
  Problem it solves: this removes the repeated ad hoc Docker/Git smoke setup that let critical auth gaps appear late and makes acceptance evidence reproducible outside one feature log.

- Tighten the shared task-planning template so closure tasks cannot run ahead of acceptance-critical validation, and require explicit companion tasks for shared-guidance edits.
  Scope: `docs/plans/templates/tasks.md` and the reusable task-generation workflow that emits `tasks.json`.
  Expected outcome: future plans will gate "final evidence" or documentation-wrapup tasks on the actual validation blockers, and cross-cutting `AGENTS.md` or docs updates will be planned intentionally instead of appearing as scope deviations.
  Problem it solves: this reduces premature closure language, improves reviewability, and keeps task boundaries aligned with the real change set.

- Move sandbox input derivation and contract validation into the active launcher path instead of leaving those rules in historical plan artifacts.
  Scope: `.sandbox/bin/start`, a shared helper under `.sandbox/scripts/`, `.sandbox/.env.example`, `docs/DEVELOPMENT_WORKFLOW.md`, and `AGENTS.md`.
  Expected outcome: the repository has one live, launcher-agnostic startup contract for sandbox inputs and workspace safety checks, so future orchestration changes preserve accepted behavior such as repo URL validation/derivation and sandbox-reuse safeguards.
  Problem it solves: the current `.sandbox` migration kept the broad isolated-clone idea but let earlier contract improvements drift back into manual setup and lighter safety checks.
