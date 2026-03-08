# AGENTS.md

Guidelines for coding agents working in this repository.

Use this file as the entry point, then follow the topic-specific guidance below.

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

# ExecPlans

When writing complex features or significant refactors, use an ExecPlan (as described in `docs/PLANS.md`) from design to implementation.

## Priority Rules

If guidance conflicts:
1. Security and data isolation rules win.
2. Architecture/domain invariants come next.
3. Testing and documentation requirements must still be satisfied.

## Tech Debt Maintenance

Coding agents must maintain `docs/TECH_DEBT_BACKLOG.md` while implementing issues.

- Add a backlog item when debt is discovered but intentionally deferred.
- Update an existing item when progress is made, scope changes, or ownership changes.
- Remove (or mark resolved) an item only when the debt is fully addressed in the same branch.
- Include issue/PR links and concrete next steps; avoid vague notes.
