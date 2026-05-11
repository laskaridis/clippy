"""Retrospective prerequisite validation helpers."""

from __future__ import annotations

from pathlib import Path

from ralph.config import RunConfig
from ralph.errors import RetrospectiveFailureError


def validate_retro_prerequisites(config: RunConfig) -> Path:
    """Validate the phase-local prerequisites for a retrospective run."""

    ralph_txt_path = config.ralph_txt_path
    if not ralph_txt_path.exists():
        raise RetrospectiveFailureError(
            f"Retrospective runs require an existing ralph.txt file: {ralph_txt_path}"
        )
    if not ralph_txt_path.is_file():
        raise RetrospectiveFailureError(f"Expected ralph.txt to be a file: {ralph_txt_path}")

    return ralph_txt_path


__all__ = ["validate_retro_prerequisites"]
