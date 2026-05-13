"""Code-phase bookkeeping validation helpers.

The coding phase owns the narrow post-run bookkeeping contract. This module
keeps the rules phase-local: it loads `tasks.json`, makes sure `ralph.txt`
exists, and accepts or rejects the phase status based only on those artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from ralph.config import RunConfig
from ralph.errors import BookkeepingValidationError
from ralph.lifecycle.phases.code.status import CodeStatus, CodeStatusResult


@dataclass(frozen=True, slots=True)
class CodeBookkeepingResult:
    """Summary of the code-phase bookkeeping check."""

    status: CodeStatus
    tasks_path: Path
    ralph_txt_path: Path
    task_count: int
    completed_task_count: int
    pending_task_count: int
    ralph_txt_created: bool

    @property
    def all_tasks_completed(self) -> bool:
        """Return `True` when every task entry is already completed."""

        return self.pending_task_count == 0


def _read_json_file(path: Path) -> Any:
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BookkeepingValidationError(f"Failed to read bookkeeping file: {path}") from exc

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise BookkeepingValidationError(f"Failed to parse bookkeeping file as JSON: {path}") from exc


def _ensure_ralph_txt_exists(path: Path) -> bool:
    if path.exists():
        if not path.is_file():
            raise BookkeepingValidationError(f"Expected ralph.txt to be a file: {path}")
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.touch(exist_ok=True)
    except OSError as exc:
        raise BookkeepingValidationError(f"Failed to create required bookkeeping file: {path}") from exc
    return True


def _load_task_entries(tasks_path: Path) -> list[Any]:
    payload = _read_json_file(tasks_path)
    if not isinstance(payload, Mapping):
        raise BookkeepingValidationError(f"Bookkeeping file must contain a JSON object: {tasks_path}")

    tasks_raw = payload.get("tasks")
    if not isinstance(tasks_raw, list):
        raise BookkeepingValidationError(f"Bookkeeping file must contain a task list at `tasks`: {tasks_path}")

    return list(tasks_raw)


def validate_code_bookkeeping(
    config: RunConfig,
    status_result: CodeStatusResult,
) -> CodeBookkeepingResult:
    """Validate the narrow v1 bookkeeping contract for one coding pass."""

    task_entries = _load_task_entries(config.tasks_path)
    ralph_txt_created = _ensure_ralph_txt_exists(config.ralph_txt_path)

    completed_task_count = 0
    for task_entry in task_entries:
        if isinstance(task_entry, Mapping) and task_entry.get("status") == "completed":
            completed_task_count += 1
    pending_task_count = len(task_entries) - completed_task_count

    if status_result.status is CodeStatus.BLOCKED:
        if status_result.blocker_line is None or not status_result.blocker_line.strip():
            raise BookkeepingValidationError(
                "RALPH_STATUS=BLOCKED requires a human-readable blocker line."
            )
    elif status_result.status is CodeStatus.COMPLETE:
        if pending_task_count != 0:
            raise BookkeepingValidationError(
                "RALPH_STATUS=COMPLETE is only valid when every task entry is completed."
            )
    elif status_result.status is CodeStatus.CONTINUE:
        if pending_task_count == 0:
            raise BookkeepingValidationError(
                "RALPH_STATUS=CONTINUE requires at least one task entry to remain not completed."
            )
    else:  # pragma: no cover - defensive against future enum extensions.
        raise BookkeepingValidationError(f"Unsupported code status for bookkeeping validation: {status_result.status!r}")

    return CodeBookkeepingResult(
        status=status_result.status,
        tasks_path=config.tasks_path,
        ralph_txt_path=config.ralph_txt_path,
        task_count=len(task_entries),
        completed_task_count=completed_task_count,
        pending_task_count=pending_task_count,
        ralph_txt_created=ralph_txt_created,
    )


__all__ = [
    "CodeBookkeepingResult",
    "validate_code_bookkeeping",
]
