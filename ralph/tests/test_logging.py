from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from ralph.logging import (
    AgentInvokedEvent,
    JsonlEventSink,
    RunFinishedEvent,
    RunStartedEvent,
    StepFinishedEvent,
    StepStartedEvent,
    TerminalEventSink,
)


class LoggingTests(TestCase):
    def test_terminal_sink_emits_human_readable_progress(self) -> None:
        stdout = StringIO()
        stderr = StringIO()
        sink = TerminalEventSink(stdout=stdout, stderr=stderr)

        sink.emit(
            RunStartedEvent(
                timestamp="2026-05-22T10:00:00Z",
                run_id="run-123",
                feature_dir="/tmp/feature",
                agent_name="codex",
                model="gpt-5.4",
                max_iterations=3,
            )
        )
        sink.emit(
            StepStartedEvent(
                timestamp="2026-05-22T10:00:01Z",
                run_id="run-123",
                iteration=1,
                step_id="code",
            )
        )
        sink.emit(
            AgentInvokedEvent(
                timestamp="2026-05-22T10:00:02Z",
                run_id="run-123",
                iteration=1,
                step_id="code",
                agent_name="codex",
                model="gpt-5.4",
            )
        )
        sink.emit(
            StepFinishedEvent(
                timestamp="2026-05-22T10:00:03Z",
                run_id="run-123",
                iteration=1,
                step_id="code",
                outcome="complete",
            )
        )
        sink.emit(
            RunFinishedEvent(
                timestamp="2026-05-22T10:00:04Z",
                run_id="run-123",
                outcome="completed",
                iterations=1,
                message="Run completed successfully after 1 iteration(s).",
            )
        )

        self.assertIn("Starting Ralph run for /tmp/feature", stdout.getvalue())
        self.assertIn("Iteration 1: starting code step.", stdout.getvalue())
        self.assertIn("invoking codex with model gpt-5.4.", stdout.getvalue())
        self.assertIn("step finished with outcome complete.", stdout.getvalue())
        self.assertIn("Run completed successfully after 1 iteration(s).", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")

    def test_jsonl_sink_writes_required_fields_and_preserves_raw_response(self) -> None:
        with TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "events.jsonl"
            with JsonlEventSink(log_path) as sink:
                sink.emit(
                    RunStartedEvent(
                        timestamp="2026-05-22T10:00:00Z",
                        run_id="run-123",
                        feature_dir="/tmp/feature",
                        agent_name="codex",
                        model="gpt-5.4",
                        max_iterations=3,
                    )
                )
                sink.emit(
                    StepStartedEvent(
                        timestamp="2026-05-22T10:00:01Z",
                        run_id="run-123",
                        iteration=1,
                        step_id="code",
                    )
                )
                sink.emit(
                    AgentInvokedEvent(
                        timestamp="2026-05-22T10:00:02Z",
                        run_id="run-123",
                        iteration=1,
                        step_id="code",
                        agent_name="codex",
                        model="gpt-5.4",
                    )
                )
                sink.emit(
                    StepFinishedEvent(
                        timestamp="2026-05-22T10:00:03Z",
                        run_id="run-123",
                        iteration=1,
                        step_id="code",
                        outcome="fail",
                        raw_response='{"outcome":"fail","failure_summary":"Need a fix"}',
                    )
                )
                sink.emit(
                    RunFinishedEvent(
                        timestamp="2026-05-22T10:00:04Z",
                        run_id="run-123",
                        outcome="failed",
                        iterations=1,
                        failure_summary="Need a fix",
                        raw_response='{"outcome":"fail","failure_summary":"Need a fix"}',
                    )
                )

            records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(
            [record["event"] for record in records],
            ["run_started", "step_started", "agent_invoked", "step_finished", "run_finished"],
        )
        self.assertEqual({record["run_id"] for record in records}, {"run-123"})
        self.assertEqual(records[3]["raw_response"], '{"outcome":"fail","failure_summary":"Need a fix"}')
        self.assertEqual(records[4]["failure_summary"], "Need a fix")
