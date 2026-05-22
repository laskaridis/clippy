from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, TypeAlias
from uuid import uuid4

from .logging import (
    AgentInvokedEvent,
    EventSink,
    NullEventSink,
    RunFinishedEvent,
    RunStartedEvent,
    StepFinishedEvent,
    StepStartedEvent,
    utc_timestamp,
)

REQUIRED_WORKFLOW_ARTIFACTS: tuple[str, ...] = ("spec.md", "tasks.json")


def _new_run_id() -> str:
    return uuid4().hex


@dataclass(frozen=True, slots=True)
class RunContext:
    """Immutable shared inputs for one Ralph run."""

    feature_dir: Path
    agent_name: str = "codex"
    model: str = "gpt-5.4"
    max_iterations: int = 50
    log_path: Path | None = None
    run_id: str = field(default_factory=_new_run_id)


@dataclass(frozen=True, slots=True)
class RunCompleted:
    """Terminal run outcome for successful completion."""

    message: str = "Run completed successfully."
    iterations: int = 0
    run_id: str = ""
    outcome: Literal["completed"] = "completed"


@dataclass(frozen=True, slots=True)
class RunBlocked:
    """Terminal run outcome for agent-reported blockage."""

    blocker_text: str
    iterations: int = 0
    run_id: str = ""
    outcome: Literal["blocked"] = "blocked"


@dataclass(frozen=True, slots=True)
class RunFailed:
    """Terminal run outcome for failed execution."""

    failure_summary: str
    raw_response: str | None = None
    iterations: int = 0
    run_id: str = ""
    outcome: Literal["failed"] = "failed"


@dataclass(frozen=True, slots=True)
class RunSetupError:
    """Terminal run outcome for invalid feature-directory setup."""

    message: str
    missing_artifacts: tuple[str, ...] = ()
    run_id: str = ""
    outcome: Literal["setup_error"] = "setup_error"


@dataclass(frozen=True, slots=True)
class RunUsageError:
    """Terminal run outcome for invalid CLI usage."""

    message: str
    run_id: str = ""
    outcome: Literal["usage_error"] = "usage_error"


RunOutcome: TypeAlias = (
    RunCompleted
    | RunBlocked
    | RunFailed
    | RunSetupError
    | RunUsageError
)


def validate_feature_directory(feature_dir: Path) -> RunSetupError | None:
    """Validate that the feature directory exists and has the required files."""

    if not feature_dir.exists():
        return RunSetupError(
            message=f"Feature directory does not exist: {feature_dir}",
            missing_artifacts=REQUIRED_WORKFLOW_ARTIFACTS,
        )

    if not feature_dir.is_dir():
        return RunSetupError(
            message=f"Feature directory is not a directory: {feature_dir}",
            missing_artifacts=REQUIRED_WORKFLOW_ARTIFACTS,
        )

    missing_artifacts = tuple(
        artifact
        for artifact in REQUIRED_WORKFLOW_ARTIFACTS
        if not (feature_dir / artifact).is_file()
    )
    if missing_artifacts:
        return RunSetupError(
            message=(
                "Feature directory is missing required workflow artifacts: "
                + ", ".join(missing_artifacts)
            ),
            missing_artifacts=missing_artifacts,
        )

    return None


def run(context: RunContext, event_sink: EventSink | None = None) -> RunOutcome:
    """Run the built-in Ralph workflow for one feature directory."""

    sink = event_sink or NullEventSink()
    sink.emit(
        RunStartedEvent(
            timestamp=utc_timestamp(),
            run_id=context.run_id,
            feature_dir=str(context.feature_dir),
            agent_name=context.agent_name,
            model=context.model,
            max_iterations=context.max_iterations,
        )
    )

    setup_error = validate_feature_directory(context.feature_dir)
    if setup_error is not None:
        outcome = RunSetupError(
            message=setup_error.message,
            missing_artifacts=setup_error.missing_artifacts,
            run_id=context.run_id,
        )
        sink.emit(
            RunFinishedEvent(
                timestamp=utc_timestamp(),
                run_id=context.run_id,
                outcome=outcome.outcome,
                message=outcome.message,
                missing_artifacts=outcome.missing_artifacts,
            )
        )
        return outcome

    from .workflow import CodeStep

    code_step = CodeStep()
    for iteration in range(1, context.max_iterations + 1):
        sink.emit(
            StepStartedEvent(
                timestamp=utc_timestamp(),
                run_id=context.run_id,
                iteration=iteration,
                step_id=code_step.step_id,
            )
        )
        sink.emit(
            AgentInvokedEvent(
                timestamp=utc_timestamp(),
                run_id=context.run_id,
                iteration=iteration,
                step_id=code_step.step_id,
                agent_name=context.agent_name,
                model=context.model,
            )
        )
        step_result = code_step.execute(context)
        sink.emit(
            StepFinishedEvent(
                timestamp=utc_timestamp(),
                run_id=context.run_id,
                iteration=iteration,
                step_id=code_step.step_id,
                outcome=step_result.outcome,
                blocker_text=getattr(step_result, "blocker_text", None),
                failure_summary=getattr(step_result, "failure_summary", None),
                raw_response=getattr(step_result, "raw_response", None),
            )
        )

        if step_result.outcome == "repeat":
            continue

        if step_result.outcome == "complete":
            outcome = RunCompleted(
                message=f"Run completed successfully after {iteration} iteration(s).",
                iterations=iteration,
                run_id=context.run_id,
            )
            sink.emit(
                RunFinishedEvent(
                    timestamp=utc_timestamp(),
                    run_id=context.run_id,
                    outcome=outcome.outcome,
                    iterations=outcome.iterations,
                    message=outcome.message,
                )
            )
            return outcome

        if step_result.outcome == "blocked":
            outcome = RunBlocked(
                blocker_text=step_result.blocker_text,
                iterations=iteration,
                run_id=context.run_id,
            )
            sink.emit(
                RunFinishedEvent(
                    timestamp=utc_timestamp(),
                    run_id=context.run_id,
                    outcome=outcome.outcome,
                    iterations=outcome.iterations,
                    blocker_text=outcome.blocker_text,
                )
            )
            return outcome

        outcome = RunFailed(
            failure_summary=step_result.failure_summary,
            raw_response=step_result.raw_response,
            iterations=iteration,
            run_id=context.run_id,
        )
        sink.emit(
            RunFinishedEvent(
                timestamp=utc_timestamp(),
                run_id=context.run_id,
                outcome=outcome.outcome,
                iterations=outcome.iterations,
                failure_summary=outcome.failure_summary,
                raw_response=outcome.raw_response,
            )
        )
        return outcome

    outcome = RunFailed(
        failure_summary=(
            f"Reached the max-iterations limit ({context.max_iterations}) without completion."
        ),
        iterations=context.max_iterations,
        run_id=context.run_id,
    )
    sink.emit(
        RunFinishedEvent(
            timestamp=utc_timestamp(),
            run_id=context.run_id,
            outcome=outcome.outcome,
            iterations=outcome.iterations,
            failure_summary=outcome.failure_summary,
        )
    )
    return outcome
