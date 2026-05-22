from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol, TypeAlias

if TYPE_CHECKING:
    from .orchestrator import RunContext

StepOutcome: TypeAlias = Literal["repeat", "complete", "blocked", "fail"]


@dataclass(frozen=True, slots=True)
class RepeatStepResult:
    """Step result that tells the orchestrator to rerun the current step."""

    outcome: Literal["repeat"] = "repeat"


@dataclass(frozen=True, slots=True)
class CompleteStepResult:
    """Step result that tells the orchestrator the current step finished cleanly."""

    outcome: Literal["complete"] = "complete"


@dataclass(frozen=True, slots=True)
class BlockedStepResult:
    """Step result that carries the blocker text to surface to the user."""

    blocker_text: str
    outcome: Literal["blocked"] = "blocked"


@dataclass(frozen=True, slots=True)
class FailedStepResult:
    """Step result that carries the failure summary and optional raw response."""

    failure_summary: str
    raw_response: str | None = None
    outcome: Literal["fail"] = "fail"


StepResult: TypeAlias = (
    RepeatStepResult
    | CompleteStepResult
    | BlockedStepResult
    | FailedStepResult
)


class Step(Protocol):
    """A bounded unit of lifecycle work."""

    step_id: str

    def execute(self, run_context: "RunContext") -> StepResult:
        """Run the step once and return a structured result."""
