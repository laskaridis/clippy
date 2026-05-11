"""Code-phase status parsing helpers.

The coding phase owns the first-line Ralph status contract. This module turns a
raw agent response into a typed result the code phase can map directly into the
shared lifecycle outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ralph.errors import MalformedStatusError
from ralph.lifecycle.phases.base import PhaseOutcome

RALPH_STATUS_CONTINUE = "RALPH_STATUS=CONTINUE"
RALPH_STATUS_COMPLETE = "RALPH_STATUS=COMPLETE"
RALPH_STATUS_BLOCKED = "RALPH_STATUS=BLOCKED"


class CodeStatus(str, Enum):
    """Exact first-line status values accepted from the coding phase."""

    CONTINUE = RALPH_STATUS_CONTINUE
    COMPLETE = RALPH_STATUS_COMPLETE
    BLOCKED = RALPH_STATUS_BLOCKED

    @property
    def phase_outcome(self) -> PhaseOutcome:
        """Map the code-phase status to the shared lifecycle outcome."""

        if self is CodeStatus.CONTINUE:
            return PhaseOutcome.NEXT_ITERATION
        if self is CodeStatus.COMPLETE:
            return PhaseOutcome.COMPLETED
        return PhaseOutcome.BLOCKED


@dataclass(frozen=True, slots=True)
class CodeStatusResult:
    """Typed parse result for a single coding-phase response."""

    status: CodeStatus
    outcome: PhaseOutcome
    response_body: str
    blocker_line: str | None = None

    @property
    def phase_outcome(self) -> PhaseOutcome:
        """Expose the shared lifecycle outcome directly for phase callers."""

        return self.outcome


def _normalize_response_text(response_text: str) -> str:
    return response_text.replace("\r\n", "\n").replace("\r", "\n")


def _missing_status_error() -> MalformedStatusError:
    return MalformedStatusError("Missing Ralph status line in coding response.")


def parse_code_status(response_text: str) -> CodeStatusResult:
    """Parse a coding-phase response into a typed status result."""

    if not isinstance(response_text, str):
        raise MalformedStatusError(f"Expected text response from coding phase: {response_text!r}")

    normalized_text = _normalize_response_text(response_text)
    if not normalized_text:
        raise _missing_status_error()

    first_line, separator, remaining_text = normalized_text.partition("\n")
    if not first_line:
        raise _missing_status_error()

    try:
        status = CodeStatus(first_line)
    except ValueError as exc:
        raise MalformedStatusError(f"Unrecognized Ralph status line: {first_line!r}") from exc

    blocker_line: str | None = None
    if status is CodeStatus.BLOCKED:
        if not separator:
            raise MalformedStatusError("RALPH_STATUS=BLOCKED requires a human-readable blocker line.")
        blocker_line, _, _ = remaining_text.partition("\n")
        if not blocker_line.strip():
            raise MalformedStatusError("RALPH_STATUS=BLOCKED requires a human-readable blocker line.")

    return CodeStatusResult(
        status=status,
        outcome=status.phase_outcome,
        response_body=remaining_text,
        blocker_line=blocker_line,
    )


def parse_code_status_response(response_text: str) -> CodeStatusResult:
    """Compatibility alias for callers that treat the payload as a response."""

    return parse_code_status(response_text)


def parse_code_status_lines(response_text: str) -> CodeStatusResult:
    """Compatibility alias for callers that refer to the full output as lines."""

    return parse_code_status(response_text)


__all__ = [
    "CodeStatus",
    "CodeStatusResult",
    "RALPH_STATUS_BLOCKED",
    "RALPH_STATUS_COMPLETE",
    "RALPH_STATUS_CONTINUE",
    "parse_code_status",
    "parse_code_status_lines",
    "parse_code_status_response",
]
