# AGENTS.md

Guidelines for coding agents working in this repository.

Use this file as the entry point, then follow the topic-specific guidance below.

## Directory outline
- .codex # codex agent specific configuration (i.e. skills, etc)
- .local # artifacts specific to the local environment
- .specify # spec-kit specific files 
- backend # backend api application
- docs # project documentation artifacts
- extension # browser extensions (currently only chrome)
- infra # application infrastructure
- specs # feature specifications and plans (created by spec-kit)

## Context-Specific Guides

- Product and repository context: [docs/PRODUCT_CONTEXT.md](docs/PRODUCT_CONTEXT.md)
- Application architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Testing and verification: [docs/TESTING.md](docs/TESTING.md)
- Security and privacy: [docs/SECURITY.md](docs/SECURITY.md)
- Code quality standards: [docs/CODE_QUALITY.md](docs/CODE_QUALITY.md)
- Tech debt backlog: [docs/TECH_DEBT_BACKLOG.md](docs/TECH_DEBT_BACKLOG.md)
- Documentation/spec sync rules: [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md)
- Definition of done: [docs/DELIVERY_CHECKLIST.md](docs/DELIVERY_CHECKLIST.md)
- Development workflow: [docs/DEVELOPMENT_WORKFLOW.md](docs/DEVELOPMENT_WORKFLOW.md)

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
