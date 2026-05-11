"""Lifecycle orchestration for a fresh Ralph run.

This module owns the v1 new-session control flow: it starts a run, enforces
the one-active-run-per-feature rule, drives the coding phase iteratively, and
invokes the retrospective automatically after implementation completes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from ralph.agents.base import Agent
from ralph.config import RunConfig
from ralph.errors import BookkeepingValidationError, RalphError
from ralph.lifecycle.phases.base import PhaseOutcome, PhaseResult
from ralph.lifecycle.phases.code.phase import CODE_PHASE_NAME, run_code_phase
from ralph.lifecycle.phases.retro.phase import RETRO_PHASE_NAME, run_retro_phase
from ralph.session import LockState, RunSession, RunSessionStore

RUN_PHASE_NAME = "run"


class RunOutcome(str, Enum):
    """Terminal outcomes for one Ralph run."""

    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    MAX_ITERATIONS = "max_iterations"
    DEGRADED = "degraded"


@dataclass(frozen=True, slots=True)
class RunReport:
    """Structured report for callers that want more than the terminal outcome."""

    outcome: RunOutcome
    session_id: str
    iteration_count: int


def run(config: RunConfig, agent: Agent) -> RunOutcome:
    """Start a fresh Ralph run and return the terminal run outcome."""

    store = RunSessionStore(config)
    _validate_new_run_start(store)

    session_id = _new_run_session_id()
    try:
        try:
            lock = store.acquire_lock(session_id)
        except BookkeepingValidationError as exc:
            raise BookkeepingValidationError(
                "Cannot start a new Ralph run because a lock already exists; use `resume` instead."
            ) from exc
        session = store.create_session(session_id=session_id, started_at=lock.started_at)
        report = _run_new_session(store, session, agent)
        return report.outcome
    finally:
        store.release_lock(session_id)


def _run_new_session(store: RunSessionStore, session: RunSession, agent: Agent) -> RunReport:
    """Drive the implementation loop for a newly created session."""

    current_session = session
    for iteration in range(current_session.iteration_count + 1, store.config.max_iterations + 1):
        current_session = _refresh_lock_heartbeat(store, current_session)
        try:
            phase_result = run_code_phase(store.config, agent)
        except RalphError as exc:
            current_session = _record_phase_failure(
                store,
                current_session,
                phase_name=CODE_PHASE_NAME,
                iteration_count=iteration,
                exc=exc,
            )
            _finalize_session(store, current_session.session_id, RunOutcome.FAILED)
            return RunReport(outcome=RunOutcome.FAILED, session_id=current_session.session_id, iteration_count=iteration)

        current_session = _record_phase_result(
            store,
            current_session,
            phase_name=CODE_PHASE_NAME,
            iteration_count=iteration,
            phase_result=phase_result,
        )
        current_session = _refresh_lock_heartbeat(store, current_session)

        if phase_result.outcome is PhaseOutcome.NEXT_ITERATION:
            if iteration >= store.config.max_iterations:
                _finalize_session(store, current_session.session_id, RunOutcome.MAX_ITERATIONS)
                return RunReport(
                    outcome=RunOutcome.MAX_ITERATIONS,
                    session_id=current_session.session_id,
                    iteration_count=iteration,
                )
            continue

        if phase_result.outcome is PhaseOutcome.BLOCKED:
            _finalize_session(store, current_session.session_id, RunOutcome.BLOCKED)
            return RunReport(outcome=RunOutcome.BLOCKED, session_id=current_session.session_id, iteration_count=iteration)

        if phase_result.outcome is PhaseOutcome.FAILED:
            _finalize_session(store, current_session.session_id, RunOutcome.FAILED)
            return RunReport(outcome=RunOutcome.FAILED, session_id=current_session.session_id, iteration_count=iteration)

        current_session = store.update_session(
            current_session.session_id,
            current_phase=RETRO_PHASE_NAME,
            iteration_count=iteration,
            last_phase_outcome=phase_result.outcome.value,
            last_agent_result_metadata=_phase_result_metadata(phase_result),
        )
        current_session = _refresh_lock_heartbeat(store, current_session)

        try:
            retro_result = run_retro_phase(store.config, agent)
        except RalphError as exc:
            current_session = _record_phase_failure(
                store,
                current_session,
                phase_name=RETRO_PHASE_NAME,
                iteration_count=iteration,
                exc=exc,
            )
            _finalize_session(store, current_session.session_id, RunOutcome.DEGRADED)
            return RunReport(
                outcome=RunOutcome.DEGRADED,
                session_id=current_session.session_id,
                iteration_count=iteration,
            )

        current_session = _record_phase_result(
            store,
            current_session,
            phase_name=RETRO_PHASE_NAME,
            iteration_count=iteration,
            phase_result=retro_result,
        )
        overall_outcome = (
            RunOutcome.COMPLETED
            if retro_result.outcome is PhaseOutcome.COMPLETED
            else RunOutcome.DEGRADED
        )
        _finalize_session(store, current_session.session_id, overall_outcome)
        return RunReport(
            outcome=overall_outcome,
            session_id=current_session.session_id,
            iteration_count=iteration,
        )

    _finalize_session(store, current_session.session_id, RunOutcome.MAX_ITERATIONS)
    return RunReport(
        outcome=RunOutcome.MAX_ITERATIONS,
        session_id=current_session.session_id,
        iteration_count=current_session.iteration_count,
    )


def _validate_new_run_start(store: RunSessionStore) -> None:
    """Reject any attempt to start a new run when one is already active."""

    current_session = store.load_current_session()
    if current_session is not None and not current_session.is_terminal:
        raise BookkeepingValidationError(
            "Cannot start a new Ralph run because an incomplete session already exists; use `resume` instead."
        )

    lock_inspection = store.inspect_lock()
    if lock_inspection.state is not LockState.ABSENT:
        raise BookkeepingValidationError(
            f"Cannot start a new Ralph run because {store.lock_path} is {lock_inspection.state.value}; use `resume` instead."
        )


def _record_phase_result(
    store: RunSessionStore,
    session: RunSession,
    *,
    phase_name: str,
    iteration_count: int,
    phase_result: PhaseResult,
) -> RunSession:
    """Persist one phase boundary and return the refreshed session snapshot."""

    return store.update_session(
        session.session_id,
        current_phase=phase_name,
        iteration_count=iteration_count,
        last_phase_outcome=phase_result.outcome.value,
        last_agent_result_metadata=_phase_result_metadata(phase_result),
    )


def _record_phase_failure(
    store: RunSessionStore,
    session: RunSession,
    *,
    phase_name: str,
    iteration_count: int,
    exc: RalphError,
) -> RunSession:
    """Persist a phase failure in the current session snapshot."""

    return store.update_session(
        session.session_id,
        current_phase=phase_name,
        iteration_count=iteration_count,
        last_phase_outcome=PhaseOutcome.FAILED.value,
        last_agent_result_metadata=_failure_metadata(phase_name, exc),
    )


def _refresh_lock_heartbeat(store: RunSessionStore, session: RunSession) -> RunSession:
    """Refresh the active-run heartbeat and return the latest session snapshot."""

    store.refresh_lock_heartbeat(session.session_id)
    return store.load_session(session.session_id)


def _finalize_session(store: RunSessionStore, session_id: str, overall_outcome: RunOutcome) -> RunSession:
    """Mark the session terminal and persist the final pointer state."""

    return store.finalize_session(session_id, overall_outcome=overall_outcome.value)


def _phase_result_metadata(phase_result: PhaseResult) -> dict[str, Any]:
    """Copy phase metadata into a plain dictionary for session persistence."""

    return dict(phase_result.metadata)


def _failure_metadata(phase_name: str, exc: RalphError) -> dict[str, Any]:
    """Capture failure diagnostics without persisting raw prompt or response bodies."""

    return {
        "phase": phase_name,
        "error_type": type(exc).__name__,
        "error_message": str(exc),
    }


def _new_run_session_id(moment: datetime | None = None) -> str:
    """Generate a filesystem-safe run-session identifier."""

    stamp = (moment or datetime.now(timezone.utc)).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{uuid4().hex[:8]}"


__all__ = [
    "RUN_PHASE_NAME",
    "RunOutcome",
    "RunReport",
    "run",
]
