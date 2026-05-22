from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, TypeAlias
from uuid import uuid4

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

