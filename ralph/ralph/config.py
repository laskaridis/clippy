"""Resolved Ralph runtime configuration and feature validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ralph.errors import FeatureValidationError

DEFAULT_CODING_MODEL = "gpt-5.4-mini"
DEFAULT_RETRO_MODEL = "gpt-5.4-medium"
DEFAULT_AGENT_IDENTIFIER = "codex"

FEATURE_SPEC_FILENAME = "spec.md"
FEATURE_TASKS_FILENAME = "tasks.json"
FEATURE_LOG_FILENAME = "ralph.txt"
FEATURE_RETRO_FILENAME = "ralph.retro.md"
RALPH_STATE_DIRECTORY = ".ralph"
RALPH_SESSIONS_DIRECTORY = "sessions"
RALPH_CURRENT_SESSION_FILENAME = "current.json"
RALPH_LOCK_FILENAME = "lock"


@dataclass(frozen=True, slots=True)
class RunConfig:
    """Resolved runtime settings for a Ralph execution."""

    feature_dir: Path
    max_iterations: int
    coding_model: str
    retro_model: str
    retro_only: bool
    agent_identifier: str = DEFAULT_AGENT_IDENTIFIER
    spec_path: Path = field(init=False)
    tasks_path: Path = field(init=False)
    ralph_txt_path: Path = field(init=False)
    retro_path: Path = field(init=False)
    ralph_dir: Path = field(init=False)
    sessions_dir: Path = field(init=False)
    current_session_path: Path = field(init=False)
    lock_path: Path = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "spec_path", self.feature_dir / FEATURE_SPEC_FILENAME)
        object.__setattr__(self, "tasks_path", self.feature_dir / FEATURE_TASKS_FILENAME)
        object.__setattr__(self, "ralph_txt_path", self.feature_dir / FEATURE_LOG_FILENAME)
        object.__setattr__(self, "retro_path", self.feature_dir / FEATURE_RETRO_FILENAME)
        ralph_dir = self.feature_dir / RALPH_STATE_DIRECTORY
        sessions_dir = ralph_dir / RALPH_SESSIONS_DIRECTORY
        object.__setattr__(self, "ralph_dir", ralph_dir)
        object.__setattr__(self, "sessions_dir", sessions_dir)
        object.__setattr__(self, "current_session_path", sessions_dir / RALPH_CURRENT_SESSION_FILENAME)
        object.__setattr__(self, "lock_path", ralph_dir / RALPH_LOCK_FILENAME)


def resolve_feature_dir(feature_dir: str | Path, *, cwd: Path | None = None) -> Path:
    """Resolve a relative feature directory against the caller's CWD."""

    candidate = Path(feature_dir)
    if candidate.is_absolute():
        raise FeatureValidationError(f"--feature-dir must be relative to the current working directory: {candidate}")

    base_dir = Path.cwd() if cwd is None else Path(cwd)
    return (base_dir / candidate).resolve()


def validate_feature_layout(feature_dir: Path) -> None:
    """Validate the narrow feature-folder contract Ralph depends on."""

    if not feature_dir.exists():
        raise FeatureValidationError(f"Feature directory does not exist: {feature_dir}")
    if not feature_dir.is_dir():
        raise FeatureValidationError(f"Feature path is not a directory: {feature_dir}")

    required_files = (
        feature_dir / FEATURE_SPEC_FILENAME,
        feature_dir / FEATURE_TASKS_FILENAME,
    )
    for required_file in required_files:
        if not required_file.is_file():
            raise FeatureValidationError(f"Missing required feature file: {required_file}")


def resolve_run_config(
    feature_dir: str | Path,
    *,
    max_iterations: int = 50,
    coding_model: str = DEFAULT_CODING_MODEL,
    retro_model: str = DEFAULT_RETRO_MODEL,
    retro_only: bool = False,
    agent_identifier: str = DEFAULT_AGENT_IDENTIFIER,
    cwd: Path | None = None,
) -> RunConfig:
    """Resolve and validate runtime inputs into a `RunConfig`."""

    if isinstance(max_iterations, bool) or not isinstance(max_iterations, int) or max_iterations <= 0:
        raise FeatureValidationError(f"--max-iterations must be a positive integer: {max_iterations}")

    resolved_feature_dir = resolve_feature_dir(feature_dir, cwd=cwd)
    validate_feature_layout(resolved_feature_dir)

    return RunConfig(
        feature_dir=resolved_feature_dir,
        max_iterations=max_iterations,
        coding_model=coding_model,
        retro_model=retro_model,
        retro_only=retro_only,
        agent_identifier=agent_identifier,
    )


__all__ = [
    "DEFAULT_AGENT_IDENTIFIER",
    "DEFAULT_CODING_MODEL",
    "DEFAULT_RETRO_MODEL",
    "FEATURE_LOG_FILENAME",
    "FEATURE_RETRO_FILENAME",
    "FEATURE_SPEC_FILENAME",
    "FEATURE_TASKS_FILENAME",
    "RALPH_CURRENT_SESSION_FILENAME",
    "RALPH_LOCK_FILENAME",
    "RALPH_SESSIONS_DIRECTORY",
    "RALPH_STATE_DIRECTORY",
    "RunConfig",
    "resolve_feature_dir",
    "resolve_run_config",
    "validate_feature_layout",
]
