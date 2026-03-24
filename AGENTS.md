# AGENTS.md

Guidelines for coding agents working in this repository.

Use this file as the entry point, then follow the topic-specific guidance below.

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

## Directory outline

- .codex # codex agent specific configuration (i.e. skills, etc)
- .local # artifacts specific to the local environment
- .specify # spec-kit specific files
- .worktrees # required location for all project git worktrees
- backend # backend api application
- docs # project documentation artifacts
- extension # browser extensions (currently only chrome)
- infra # application infrastructure
- specs # feature specifications and plans (created by spec-kit)

## Context-Specific Guides

- Product principles context: [docs/PRODUCT_SENSE.md](docs/PRODUCT_SENSE.md)
- Application architecture context: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Testing and verification: [docs/TESTING.md](docs/TESTING.md)
- Security and privacy context: [docs/SECURITY.md](docs/SECURITY.md)
- Code quality standards: [docs/CODE_QUALITY.md](docs/CODE_QUALITY.md)
- Tech debt backlog: [docs/TECH_DEBT_BACKLOG.md](docs/TECH_DEBT_BACKLOG.md)
- Development workflow (including worktree location/deletion policy): [docs/DEVELOPMENT_WORKFLOW.md](docs/DEVELOPMENT_WORKFLOW.md)
- Core review findings template: [docs/plans/templates/code-review-findings.md](docs/plans/templates/code-review-findings.md)

# ExecPlans

When writing complex features or significant refactors, use an ExecPlan (as described in `docs/PLANS.md`) from design to implementation.

## Tech Debt Maintenance

Coding agents must maintain `docs/TECH_DEBT_BACKLOG.md` while implementing tasks.

- Add a backlog item when debt is discovered but intentionally deferred.
- Update an existing item when progress is made, scope changes, or ownership changes.
- Remove (or mark resolved) an item only when the debt is fully addressed in the same branch.
- Include issue/PR links and concrete next steps; avoid vague notes.
