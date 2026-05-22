from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Protocol, TextIO, TypeAlias


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class RunStartedEvent:
    event: Literal["run_started"] = "run_started"
    timestamp: str = ""
    run_id: str = ""
    feature_dir: str = ""
    agent_name: str = ""
    model: str = ""
    max_iterations: int = 0


@dataclass(frozen=True, slots=True)
class StepStartedEvent:
    event: Literal["step_started"] = "step_started"
    timestamp: str = ""
    run_id: str = ""
    iteration: int = 0
    step_id: str = ""


@dataclass(frozen=True, slots=True)
class AgentInvokedEvent:
    event: Literal["agent_invoked"] = "agent_invoked"
    timestamp: str = ""
    run_id: str = ""
    iteration: int = 0
    step_id: str = ""
    agent_name: str = ""
    model: str = ""


@dataclass(frozen=True, slots=True)
class StepFinishedEvent:
    event: Literal["step_finished"] = "step_finished"
    timestamp: str = ""
    run_id: str = ""
    iteration: int = 0
    step_id: str = ""
    outcome: str = ""
    blocker_text: str | None = None
    failure_summary: str | None = None
    raw_response: str | None = None


@dataclass(frozen=True, slots=True)
class RunFinishedEvent:
    event: Literal["run_finished"] = "run_finished"
    timestamp: str = ""
    run_id: str = ""
    outcome: str = ""
    iterations: int = 0
    message: str | None = None
    blocker_text: str | None = None
    failure_summary: str | None = None
    raw_response: str | None = None
    missing_artifacts: tuple[str, ...] | None = None


RunEvent: TypeAlias = (
    RunStartedEvent
    | StepStartedEvent
    | AgentInvokedEvent
    | StepFinishedEvent
    | RunFinishedEvent
)


class EventSink(Protocol):
    def emit(self, event: RunEvent) -> None:
        """Emit a single run event."""


@dataclass(frozen=True, slots=True)
class NullEventSink:
    def emit(self, event: RunEvent) -> None:  # pragma: no cover - intentionally empty
        return


@dataclass(slots=True)
class TerminalEventSink:
    """Human-readable console presenter for Ralph run progress."""

    stdout: TextIO = field(default_factory=lambda: sys.stdout)
    stderr: TextIO = field(default_factory=lambda: sys.stderr)

    def emit(self, event: RunEvent) -> None:
        if isinstance(event, RunStartedEvent):
            self._write_stdout(
                "Starting Ralph run for "
                f"{event.feature_dir} (agent={event.agent_name}, model={event.model}, "
                f"max_iterations={event.max_iterations}, run_id={event.run_id})."
            )
            return

        if isinstance(event, StepStartedEvent):
            self._write_stdout(f"Iteration {event.iteration}: starting {event.step_id} step.")
            return

        if isinstance(event, AgentInvokedEvent):
            self._write_stdout(
                f"Iteration {event.iteration}: invoking {event.agent_name} with model {event.model}."
            )
            return

        if isinstance(event, StepFinishedEvent):
            self._write_stdout(
                f"Iteration {event.iteration}: {event.step_id} step finished with outcome {event.outcome}."
            )
            return

        if isinstance(event, RunFinishedEvent):
            self._emit_run_finished(event)
            return

        raise TypeError(f"Unhandled event type: {type(event)!r}")

    def _emit_run_finished(self, event: RunFinishedEvent) -> None:
        if event.outcome == "completed":
            self._write_stdout(event.message or f"Run completed successfully after {event.iterations} iteration(s).")
            return

        if event.outcome == "blocked":
            self._write_stderr(
                event.blocker_text
                or f"Run blocked after {event.iterations} iteration(s)."
            )
            return

        if event.outcome == "failed":
            self._write_stderr(
                event.failure_summary
                or f"Run failed after {event.iterations} iteration(s)."
            )
            return

        if event.outcome == "setup_error":
            self._write_stderr(event.message or "Run setup failed.")
            if event.missing_artifacts:
                self._write_stderr(
                    "Missing workflow artifacts: " + ", ".join(event.missing_artifacts)
                )
            return

        if event.outcome == "usage_error":
            self._write_stderr(event.message or "Invalid CLI usage.")
            return

        self._write_stderr(
            event.message or f"Run finished with outcome {event.outcome}."
        )

    def _write_stdout(self, message: str) -> None:
        print(message, file=self.stdout, flush=True)

    def _write_stderr(self, message: str) -> None:
        print(message, file=self.stderr, flush=True)


@dataclass(slots=True)
class JsonlEventSink:
    """JSONL writer for machine-readable Ralph run events."""

    path: Path
    encoding: str = "utf-8"
    _handle: TextIO | None = None

    def __enter__(self) -> "JsonlEventSink":
        self._handle = self.path.open("a", encoding=self.encoding)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None

    def emit(self, event: RunEvent) -> None:
        if self._handle is None:
            raise RuntimeError("JSONL event sink must be opened with a context manager.")
        record = asdict(event)
        self._handle.write(json.dumps(record, ensure_ascii=False))
        self._handle.write("\n")
        self._handle.flush()


@dataclass(frozen=True, slots=True)
class CompositeEventSink:
    """Fan out run events to multiple sinks."""

    sinks: tuple[EventSink, ...]

    def emit(self, event: RunEvent) -> None:
        for sink in self.sinks:
            sink.emit(event)
