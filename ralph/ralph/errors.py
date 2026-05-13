"""Shared Ralph exception surface.

This module intentionally stays small and stdlib-only so other modules can
import typed failures without creating ad hoc exception names.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


class RalphError(Exception):
    """Base class for all Ralph-specific failures."""


class FeatureValidationError(RalphError):
    """Raised when the feature folder or its required artifacts are invalid."""


class PromptLoadingError(RalphError):
    """Raised when a phase prompt cannot be loaded or rendered."""


class AgentExecutionError(RalphError):
    """Raised when an agent invocation fails or returns unusable diagnostics."""


class MalformedStatusError(RalphError):
    """Raised when a coding phase response violates the status-line contract."""


class BookkeepingValidationError(RalphError):
    """Raised when Ralph bookkeeping artifacts fail their narrow contract."""


class RetrospectiveFailureError(RalphError):
    """Raised when the retrospective phase cannot complete successfully."""


@dataclass(frozen=True, slots=True)
class ErrorContext:
    """Structured diagnostic context for a Ralph failure."""

    message: str
    details: Mapping[str, object] | None = None

