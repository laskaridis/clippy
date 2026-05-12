# Replace Ralph File-Backed Session Storage with Feature-Local SQLite

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [docs/PLANS.md](../PLANS.md).

## Purpose / Big Picture

Ralph currently persists run bookkeeping by writing JSON files under each feature directory's `.ralph/` folder and by maintaining a separate lock file that represents the active run lease. After this change, Ralph will persist the same logical state in a single SQLite database stored at `.ralph/sessions.sqlite3`.

Ralph will no longer support a separate `resume` operation. Each `ralph run` invocation creates a new session. If a prior run crashes or stops prematurely, the next `ralph run` starts a fresh session that takes over from the current feature artifacts already on disk rather than from persisted in-memory session state. The storage change remains behavioral rather than structural: from the repository root, a developer should be able to run the Ralph test suite with `make ralph-test` and observe the run lifecycle scenarios still passing after the backing store changes. They should also be able to inspect a feature directory after a test run and observe `.ralph/sessions.sqlite3` as the authoritative Ralph state file. Legacy file-backed artifacts such as `sessions/*.json`, `sessions/current.json`, and `.ralph/lock` are out of scope for the new implementation and may be ignored if they remain on disk.

## Progress

- [x] (2026-05-12 00:00Z) Captured the target architecture and decision-complete storage rules for the SQLite-backed session store.
- [x] (2026-05-12 00:00Z) Revised the design to remove `resume`, heartbeat-based locks, and the single-incomplete-session invariant.
- [ ] Implement `RunConfig.db_path` and remove file-store-specific config paths from the Ralph runtime configuration.
- [ ] Replace the file-backed implementation in `ralph/ralph/session.py` with a SQLite-backed `RunSessionStore` that supports run-only recovery semantics.
- [ ] Update the orchestration and tests to assert behavior against the SQLite-backed store without any legacy-artifact compatibility requirements.
- [ ] Run `make ralph-test`, `make ralph-lint`, and `make ralph-typecheck` from the repository root and capture the final outcomes here.

## Surprises & Discoveries

- Observation: The current session store is not only a collection of session JSON files. It also writes a current-session pointer file and a separate lock file, so the real migration scope includes three coordinated persistence artifacts.
  Evidence: `ralph/ralph/session.py` currently exposes `load_current_pointer()`, `load_current_session()`, `load_lock()`, `_write_current_pointer()`, `_write_lock_record()`, and `_write_lock_record_exclusive()`.

- Observation: The current orchestrator couples session recovery and lock recovery through a dedicated `resume()` path.
  Evidence: `ralph/ralph/lifecycle/orchestrator.py` currently calls `load_current_session()`, `inspect_lock()`, `acquire_lock()`, `refresh_lock_heartbeat()`, and `release_lock()` to enforce `run` and `resume` semantics.

- Observation: Once `resume` is removed, most of the bookkeeping complexity shifts from "continue this exact session" to "start a new session safely without clobbering a live process."
  Evidence: The remaining hard cases are live-lock blocking, dead same-host lock takeover, and latest-session lookup across historical incomplete sessions.

## Decision Log

- Decision: Replace all three file-backed artifacts with SQLite rather than storing only session history in SQLite and keeping the lock file or pointer file on disk.
  Rationale: A partial migration would leave the most fragile consistency boundary in place and force future contributors to maintain two storage models.
  Date/Author: 2026-05-12 / Codex + user

- Decision: Keep the SQLite database feature-local under `.ralph/`.
  Rationale: Ralph already isolates bookkeeping per feature directory. Preserving that layout avoids introducing cross-feature coordination into a storage refactor.
  Date/Author: 2026-05-12 / Codex + user

- Decision: Make this a clean-slate cutover with no migration path and no backward-compatibility behavior for the legacy JSON files or lock file.
  Rationale: The user explicitly chose lower implementation cost and a simpler implementation contract over migration continuity.
  Date/Author: 2026-05-12 / Codex + user

- Decision: Remove the separate `resume` operation entirely.
  Rationale: The user wants each `ralph run` to be a new session, with crash recovery happening through a new run that continues from current feature artifacts on disk.
  Date/Author: 2026-05-12 / Codex + user

- Decision: Remove the explicit current-session pointer artifact and derive the current/latest session from SQL queries.
  Rationale: In SQLite, a separate pointer row would duplicate information that can be derived from the `sessions` table and would reintroduce a consistency problem the migration is meant to eliminate.
  Date/Author: 2026-05-12 / Codex + user

- Decision: Add `RunConfig.db_path` as an explicit runtime configuration field and remove the public config fields that point at `sessions_dir`, `current_session_path`, and `lock_path`.
  Rationale: The SQLite database path is a real runtime artifact that should remain visible to diagnostics and tests instead of being hidden inside the store implementation.
  Date/Author: 2026-05-12 / Codex + user

- Decision: Keep only a minimal public lock API: `inspect_lock()`, `acquire_lock(session_id)`, and `release_lock(session_id)`.
  Rationale: Without `resume`, Ralph still needs a read-side lock decision for `run`, but it no longer needs raw lock loading or heartbeat refresh behavior.
  Date/Author: 2026-05-12 / Codex + user

- Decision: Remove heartbeat-based lease freshness and store only `session_id`, `pid`, `hostname`, and `started_at` for the active lock record.
  Rationale: The user chose to simplify stale-lock handling and accept dead-PID-only same-host takeover rather than maintaining heartbeat freshness.
  Date/Author: 2026-05-12 / Codex + user

- Decision: Preserve the existing domain interfaces and in-memory model shape where practical.
  Rationale: The user wants the session-management change to remain primarily an implementation swap, not a redesign of the core Ralph session abstractions beyond the removed `resume` behavior and simplified locks.
  Date/Author: 2026-05-12 / Codex + user

- Decision: Use a normalized SQLite schema with dedicated session and active-lock tables, while storing config snapshots and last-agent metadata as JSON text columns.
  Rationale: This keeps the schema small and constrained without forcing an unnecessary relational redesign of opaque payloads that Ralph only persists and reads back.
  Date/Author: 2026-05-12 / Codex + user

- Decision: Enforce an explicit SQLite schema version with `PRAGMA user_version` and fail on unsupported versions.
  Rationale: The current file-backed store already uses explicit schema versions. SQLite should preserve that upgrade-safety discipline.
  Date/Author: 2026-05-12 / Codex + user

- Decision: Allow multiple incomplete historical sessions to remain in the database.
  Rationale: A new `ralph run` should create a new session without auto-finalizing an earlier stopped session as failed, abandoned, or interrupted.
  Date/Author: 2026-05-12 / Codex + user

- Decision: Define "current/latest session" as the newest session, even if older sessions are also incomplete.
  Rationale: The user chose "newest session wins" rather than preserving the old single-incomplete-session invariant.
  Date/Author: 2026-05-12 / Codex + user

- Decision: New runs may reclaim only dead same-host locks; live locks still block.
  Rationale: The user wants safe automatic recovery after crashes without allowing a new run to steal ownership from a live Ralph process.
  Date/Author: 2026-05-12 / Codex + user

- Decision: Legacy file-backed artifacts are completely ignored by the SQLite-backed implementation.
  Rationale: The user chose a strict clean-slate storage contract in which Ralph only reads and writes `.ralph/sessions.sqlite3`, never probes legacy locations, never blocks startup because of them, and never performs cleanup on the user's behalf.
  Date/Author: 2026-05-12 / Codex + user

- Decision: Name the feature-local SQLite file `.ralph/sessions.sqlite3`.
  Rationale: The user chose this filename even though the database also holds lock state.
  Date/Author: 2026-05-12 / Codex + user

## Outcomes & Retrospective

This plan is not implemented yet. The desired outcome is a SQLite-backed Ralph session store that removes `resume`, treats each `ralph run` as a new session, and replaces the three coordinated file artifacts with one database file. The main open risk is not conceptual; it is execution discipline. The implementation must preserve single-active-run safety for live processes, preserve dead-lock takeover behavior for same-host crashed processes, and adjust tests so they validate run-only recovery semantics instead of the old resume model.

## Context and Orientation

Ralph is a standalone CLI package under `ralph/` in this repository. The session-management work is concentrated in three places.

`ralph/ralph/config.py` resolves runtime inputs such as the feature directory, the maximum iteration count, and the paths to Ralph's bookkeeping files. Today it derives `config.ralph_dir`, `config.sessions_dir`, `config.current_session_path`, and `config.lock_path`.

`ralph/ralph/session.py` is the persistence boundary for Ralph runs. It defines `RunSession`, which is an immutable snapshot of a run; `RunLock`, which represents active-run ownership; `LockInspection`, which reports whether the active lease is absent, active, or stale; and `RunSessionStore`, which reads and writes the state. The current implementation serializes sessions and locks to JSON files and uses atomic file replacement plus exclusive file creation to avoid partial writes and lock races.

`ralph/ralph/lifecycle/orchestrator.py` owns the run lifecycle. After this change, `run()` is the only lifecycle entrypoint. Each invocation must create a new session if it is allowed to proceed. A stopped earlier session is historical state only. Recovery happens through a fresh `run()` that uses the current feature artifacts on disk rather than by continuing the exact prior session.

The existing tests in `ralph/tests/test_session.py`, `ralph/tests/test_orchestrator_run.py`, `ralph/tests/test_orchestrator_resume.py`, and `ralph/tests/test_config.py` currently assert both behavior and file-path details. A successful migration must update those tests to keep the behavioral guarantees that still matter, remove assertions that depend on the old JSON or lock-file layout, and remove `resume`-specific expectations entirely.

In this plan, "lease" means the record of which process currently owns the right to continue a Ralph run. "Stale lock" means a lock that belongs to the current host and whose PID is proven dead. "Current/latest session" means the newest session for a feature, even when older incomplete sessions remain in the database. "Take over from where the last one stopped" means the new run reads the current feature artifacts already written to disk, starts a new session at phase `code`, and begins with `iteration_count = 0`.

## Plan of Work

Begin in `ralph/ralph/config.py`. Replace the current file-store path fields with a single `db_path` field that points at `feature_dir / ".ralph" / "sessions.sqlite3"`. Keep `ralph_dir` because the feature-local hidden state directory still exists. Remove the constants that only make sense for the old JSON layout, and update `resolve_run_config()` tests so they validate the new path shape.

Next, replace the file-based implementation in `ralph/ralph/session.py` with a SQLite-backed store built on Python's standard-library `sqlite3` module. Preserve the public in-memory types where practical, but simplify the public lock API to `inspect_lock()`, `acquire_lock(session_id)`, and `release_lock(session_id)`. The constructor for `RunSessionStore` should continue to accept `RunConfig`. The store should lazily create `config.ralph_dir` and initialize the database schema on first use. Schema initialization must set `PRAGMA user_version` to a constant integer and must fail fast if an existing database advertises an unsupported version.

The SQLite schema should include a `sessions` table and an `active_lock` table. The `sessions` table should contain the fields needed to reconstruct `RunSession`: `session_id`, `feature_dir`, `config_json`, `current_phase`, `iteration_count`, `last_phase_outcome`, `last_agent_result_metadata_json`, `started_at`, `updated_at`, `ended_at`, and `overall_outcome`. Store the config snapshot and the last-agent metadata as JSON text because Ralph treats them as opaque structured payloads. The `active_lock` table should hold exactly zero or one row and should include `session_id`, `pid`, `hostname`, and `started_at`.

The old pointer file should disappear conceptually. `load_current_session()` should become a query. It must return the newest session ordered deterministically by `updated_at DESC, session_id DESC`, regardless of whether older incomplete sessions also exist. `load_current_pointer()` can either remain as a derived helper that returns a `RunSessionPointer` assembled from queries or be removed if no callers remain. If it remains, it must be purely derived and must not create a new persistent pointer artifact.

Use transactions to keep state transitions atomic. Creating a session, updating it, finalizing it, acquiring a lock, and releasing a lock should each be written so the underlying SQL either completes or leaves the previous state intact. The SQLite version should improve on the current file store by treating each logical state transition as one transactional change.

Redefine lock inspection around run-only semantics. `inspect_lock()` should still compare the stored hostname with the current hostname. It should call the PID liveness check only when the hosts match. It should report `LockState.STALE` only when the hosts match and the process is proven dead. Remote-host locks must remain active until a higher-level recovery policy changes. `run()` may reclaim a stale same-host lock automatically before creating a new one. `run()` must not steal a live lock from another Ralph process.

Do not implement any legacy-artifact detection, migration, validation, or cleanup. The store should create `config.ralph_dir` as needed, initialize or open `.ralph/sessions.sqlite3`, and use that database as the sole source of truth from the first call onward. Leftover file-backed artifacts such as session JSON files, `current.json`, or `.ralph/lock` are irrelevant to the SQLite-backed version and must not affect startup behavior.

After the persistence layer is in place, update `ralph/ralph/lifecycle/orchestrator.py` to remove the `resume()` entrypoint and any helper logic that assumes an existing session can be continued. `run()` should create a new session every time it is allowed to start. If an earlier session stopped prematurely, the new run should use whatever work is already reflected in the feature artifacts on disk. Error messages that currently mention `store.lock_path` should instead reference `store.config.db_path` or should speak in database-backed terms so the messages remain accurate.

Finally, update and extend the Ralph tests. `ralph/tests/test_config.py` should assert `config.db_path`. `ralph/tests/test_session.py` should validate session creation, latest-session derivation, lock acquisition, stale-lock inspection, and lock release. `ralph/tests/test_orchestrator_run.py` should prove run-only lifecycle behavior such as blocked runs, degraded retros, dead-lock takeover, live-lock rejection, and fresh-session creation after an earlier stopped run. `ralph/tests/test_orchestrator_resume.py` should be removed or replaced because `resume` is no longer part of the product contract.

## Concrete Steps

All commands in this section are run from the repository root, which in the current worktree is `/Users/e.laskaridis/Projects/sandbox/webclippings/.worktrees/ralph-cli`.

Inspect the current config, session store, and lifecycle code before editing:

    sed -n '1,220p' ralph/ralph/config.py
    sed -n '1,260p' ralph/ralph/session.py
    sed -n '1,260p' ralph/ralph/lifecycle/orchestrator.py

Inspect the current Ralph tests before editing:

    sed -n '1,220p' ralph/tests/test_config.py
    sed -n '1,240p' ralph/tests/test_session.py
    sed -n '1,280p' ralph/tests/test_orchestrator_run.py
    sed -n '1,240p' ralph/tests/test_orchestrator_resume.py

Implement the configuration and storage changes, then run the Ralph verification commands:

    make ralph-test
    make ralph-lint
    make ralph-typecheck

Expected outcomes after implementation:

    make ralph-test
    ...
    OK

    make ralph-lint
    ...
    All checks passed!

    make ralph-typecheck
    ...
    Success: no issues found

If `make ralph-test` fails in the middle of the migration, first fix the behavioral mismatch the failure describes instead of weakening the test. The migration is only complete when the run-only lifecycle guarantees are proven against SQLite-backed state.

## Validation and Acceptance

Validation must prove both storage correctness and lifecycle correctness.

First, run `make ralph-test` from the repository root and expect the Ralph test suite to pass. The key scenarios are that a new run can be created, a stopped run followed by a new run creates a fresh session that continues from feature artifacts on disk, a stale same-host lock can be reclaimed by `run`, a live lock still blocks a concurrent `run`, and latest-session queries resolve to the newest session even when older incomplete sessions remain.

Second, run `make ralph-lint` and `make ralph-typecheck` from the repository root and expect both to pass without introducing style or type regressions.

Third, add or update tests so they make the storage transition observable. At least one test should prove that after a session mutation the database file exists at `.ralph/sessions.sqlite3`. The updated suite should prove SQLite-backed session persistence, latest-session derivation, lock acquisition, lock release, dead same-host lock takeover, and unchanged run-phase outcomes. It should not depend on `resume`, heartbeat refresh, `current.json`, or `.ralph/lock`.

Acceptance is reached when a developer can read the updated tests and see that Ralph's external lifecycle behavior is now run-only, the on-disk storage format is SQLite-backed, and legacy file-backed artifacts are entirely ignored.

## Idempotence and Recovery

The implementation steps are safe to repeat because the database schema initialization should be written to tolerate reopening an existing supported database. Test commands are idempotent and may be rerun after each edit.

The main recovery hazard is a partially implemented SQLite store, not the presence of leftover file-backed artifacts. During development, legacy files may coexist in test fixtures or feature directories, but the SQLite-backed implementation should ignore them completely rather than reading, validating, or cleaning them up.

If a schema mistake is discovered mid-implementation, delete only the test fixture database created in temporary directories and rerun the tests. Do not add automatic destructive cleanup to production code beyond the existing best-effort lock release behavior, and do not introduce cleanup code for obsolete file-backed artifacts.

## Artifacts and Notes

The most important implementation artifact is the SQLite schema. The exact SQL can vary, but the resulting behavior must support these logical shapes:

    sessions(
        session_id TEXT PRIMARY KEY,
        feature_dir TEXT NOT NULL,
        config_json TEXT NOT NULL,
        current_phase TEXT NOT NULL,
        iteration_count INTEGER NOT NULL,
        last_phase_outcome TEXT,
        last_agent_result_metadata_json TEXT,
        started_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        ended_at TEXT,
        overall_outcome TEXT
    )

    active_lock(
        singleton_key INTEGER PRIMARY KEY CHECK (singleton_key = 1),
        session_id TEXT NOT NULL,
        pid INTEGER NOT NULL,
        hostname TEXT NOT NULL,
        started_at TEXT NOT NULL
    )

The `active_lock` singleton key is one straightforward way to enforce "zero or one active lock row" in SQLite. A different mechanism is acceptable if it preserves the same invariant clearly and testably.

## Interfaces and Dependencies

Use Python's built-in `sqlite3` module in `ralph/ralph/session.py`. Do not add a new ORM or third-party SQL dependency for this change.

At the end of the work, `ralph/ralph/config.py` must expose a `RunConfig` with `db_path: Path` and without `sessions_dir`, `current_session_path`, or `lock_path`.

At the end of the work, `ralph/ralph/session.py` must still expose:

    class RunSessionStore:
        def create_session(...)
        def load_session(...)
        def load_current_session(...)
        def inspect_lock(...)
        def acquire_lock(...)
        def release_lock(...)
        def update_session(...)
        def finalize_session(...)

The exact helper methods may change, but callers in `ralph/ralph/lifecycle/orchestrator.py` should not need to learn a new storage format.

At the end of the work, `ralph/ralph/lifecycle/orchestrator.py` must still be able to enforce:

    run() creates a fresh session whenever a new run is allowed to start
    run() may reclaim a dead same-host lease before acquiring a new one
    run() rejects a fresh run when a live lease already exists
    finally blocks release only the lock owned by the current session

Revision note: updated this ExecPlan on 2026-05-12 to capture the run-only design for replacing Ralph's file-backed session bookkeeping with a feature-local SQLite store, using `.ralph/sessions.sqlite3` as the sole Ralph persistence artifact, removing `resume`, and intentionally ignoring obsolete file-backed state.
