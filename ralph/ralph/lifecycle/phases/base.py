"""Shared lifecycle phase contract for Ralph.

The phase boundary stays intentionally small: a phase runs once, reports a
local outcome, and carries only the metadata the orchestrator needs for
bookkeeping. It does not encode loop policy or which phase should run next.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Protocol, runtime_checkable


PhaseMetadata = Mapping[str, Any]


class PhaseOutcome(str, Enum):
    """Typed result vocabulary for a single phase invocation."""

    NEXT_ITERATION = "next_iteration"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class PhaseResult:
    """Structured result for one phase invocation."""

    outcome: PhaseOutcome
    metadata: PhaseMetadata = field(default_factory=dict)


@runtime_checkable
class Phase(Protocol):
    """Execution contract for a single-shot lifecycle phase."""

    def run(self, *args: Any, **kwargs: Any) -> PhaseResult:
        """Execute the phase once and return a local result."""


__all__ = ["Phase", "PhaseMetadata", "PhaseOutcome", "PhaseResult"]
