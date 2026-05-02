# AGENTS.md

Guidelines for coding agents working in this repository.

## Context-Specific Guides

Before doing any work read the `docs/README.md` first to learn about any context-specific documentation available in this project in case you need to access it later.

## Canonical task entrypoints

When working with the codebase prefer `Makefile` as the primary surface of stable tasks for local workflow and automation such as testing, launching servers, initializing environments, running guardrail checks, etc:

- For the live command list, run `make help`.
- `make all-*` targets are the canonical cross-project entrypoints.
- `make backend-*` and `make extension-*` targets are project-scoped entrypoints.
- Backend script wrappers should assume the devcontainer is already prepared and call project commands directly from `backend/` rather than re-running runtime bootstrap helpers.

If you need to do something **ALWAYS** check first if there is a Makefile target that you could use to complete your task. If you can't find one, consider creating one.

## Project Directory Outline

```
├── .codex/      # codex agent specific configuration (i.e. skills, etc)
├── .local/      # artifacts specific to the local environment
├── .specify/    # spec-kit specific files
├── .worktrees/  # required location for all project git worktrees
├── backend/     # backend application (api and web app)
├── docs/        # project's documentation artifacts
├── extension/   # browser app extensions (currently only for chrome)
├── infra/       # infrastructure related artifacts
└── specs/       # feature specifications and implementation plans
```

## Front-end development

Before writing any code that includes any kind of **front-end** changes **ALLWAYS** read `docs/frontend.md` to learn about the core principles, rules and guidelines followed in this project.

For the browser extension shared config, keep the precedence order explicit: runtime config first, manifest host_permissions second, and the hard-coded localhost fallback last. When updating `extension/chrome/manifest.json`, keep localhost wildcard permissions before any non-local example host so the manifest fallback stays deterministic.
Extension Playwright helpers should load the checked-in `extension/chrome` directory directly and, when they need to self-start the backend, do so with `make backend-run` from the repository root instead of any generated worktree runtime file or deleted bootstrap script.
When removing obsolete helper scripts, delete any thin wrappers that still invoke them and scrub live README references before running repo-wide reference audits.
