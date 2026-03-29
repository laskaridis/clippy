# AGENTS.md

Guidelines for coding agents working in this repository.

## Context-Specific Guides

Before doing any work **ALWAYS** read the `docs/README.md` first to learn about any context-specific documentation available in this project, in case you need to access it later.

## Development Workflow

Before doing any code changes **ALWAYS** read the development workflow described in `docs/DEVELOPMENT_WORKFLOW.md` and ensure it is followed. Do **NOT** consider this optional, it's **MANDATORY** and **CRITICAL** to follow to the letter.

## Code quality

Before writing code of any kind **ALWAYS** read the core principles, rules and guidelines mentioned in `docs/CODE_QUALITY.md` document and ensure they are followed. Do **NOT** consider this optional.

## Canonical task entrypoints

When working with the codebase use `Makefile` as the primary surface for local workflows and automation such as testing, launching servers, initializing environments, running guardrail checks, etc:

- For the live command list, run `make help`.
- `make all-*` targets are the canonical cross-project entrypoints.
- `make backend-*` and `make extension-*` targets are project-scoped entrypoints.

If you need to do something **ALWAYS** check first if there is a Makefile target that you could use to complete your task. If you can't find one, consider creating one.

## Test execution guardrail

- Do not run overlapping backend verification commands that execute Django E2E tests at the same time (for example `make backend-test-e2e` in parallel with `make all-verify`), because they can race on the same test database and fail non-deterministically.

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

Before writing any code that includes any kind of **front-end** changes ALLWAYS read `docs/frontend.md` to learn about the core principles, rules and guidelines followed in this project.

- For backend server-rendered frontend work, load shared behavior through `backend/static/js/backend-app.js`; register Stimulus controllers in `backend/static/js/controllers/index.js` and keep any temporary legacy compatibility wiring inside `backend/static/js/legacy-backend-bootstrap.js` instead of adding new per-template script tags.
- For theme behavior, keep the head-loaded `backend/static/js/theme-controller.js` limited to pre-paint theme restoration only; put toggle UI state, aria updates, and persistence in the `global-theme-toggle` Stimulus controller so no-flash startup stays intact without split runtime ownership.
- For Stimulus replacements of document-level widgets (for example quick-search popovers), keep debounce/request state on the controller instance and bind document listeners in `connect()` with matching cleanup in `disconnect()` so repeated mounts do not leak global handlers.
