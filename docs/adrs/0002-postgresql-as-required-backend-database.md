# 0002: Adopt PostgreSQL as the required backend database

- Status: Accepted
- Date: 2026-02-28

## Context

The backend has supported both PostgreSQL and SQLite through environment-based configuration. That dual-path setup was useful early, but current and planned backend behavior relies on PostgreSQL-specific capabilities (for example, full-text search and trigram indexing for quick search, plus production-grade query planning/index behavior).

Maintaining SQLite as an equal runtime target now creates architecture drift:

- feature behavior diverges between local/dev and production-like environments,
- performance and relevance tuning cannot be validated consistently,
- migrations and query paths are increasingly shaped by PostgreSQL-only features.

## Decision

Use PostgreSQL as the required backend database for development, test validation, and deployment environments.

Specifically:

1. PostgreSQL is the canonical and required backend data store.
2. Backend features may use PostgreSQL-native capabilities when needed.
3. Local tooling should prioritize easy PostgreSQL startup (for example, local Docker Compose stack).
4. SQLite fallback may still exist in settings for limited bootstrap convenience, but it is not a supported parity target for feature validation or release sign-off.

## Consequences

### Positive

- Environment parity improves across local, CI, and production-like runs.
- PostgreSQL-native features can be implemented without dual-database compromises.
- Performance and indexing behavior become testable under realistic conditions.

### Negative

- Local setup now depends on a running PostgreSQL instance.
- Contributors need Docker/PostgreSQL tooling available in development environments.
- Some tests/checks may need explicit PostgreSQL execution in addition to fast local loops.

### Neutral

- Django ORM remains the primary persistence abstraction; this decision changes required runtime backing, not core module boundaries.
