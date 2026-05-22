from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from ralph.lifecycle import BlockedStepResult, CompleteStepResult, FailedStepResult, RepeatStepResult
from ralph.logging import (
    AgentInvokedEvent,
    RunFinishedEvent,
    RunStartedEvent,
    StepFinishedEvent,
    StepStartedEvent,
)
from ralph.orchestrator import (
    RunBlocked,
    RunCompleted,
    RunContext,
    RunFailed,
    RunSetupError,
    run,
)


@dataclass
class RecordingSink:
    events: list[object]

    def emit(self, event) -> None:
        self.events.append(event)


class OrchestratorTests(TestCase):
    def test_run_rejects_missing_feature_directory_before_step_execution(self) -> None:
        with TemporaryDirectory() as temp_dir:
            feature_dir = Path(temp_dir) / "missing"
            context = RunContext(feature_dir=feature_dir, run_id="run-123")
            sink = RecordingSink(events=[])

            outcome = run(context, event_sink=sink)

        self.assertIsInstance(outcome, RunSetupError)
        self.assertEqual(outcome.missing_artifacts, ("spec.md", "tasks.json"))
        self.assertEqual([type(event) for event in sink.events], [RunStartedEvent, RunFinishedEvent])

    def test_run_rejects_missing_artifacts_before_step_execution(self) -> None:
        with TemporaryDirectory() as temp_dir:
            feature_dir = Path(temp_dir) / "feature"
            feature_dir.mkdir()
            (feature_dir / "spec.md").write_text("# spec\n", encoding="utf-8")
            context = RunContext(feature_dir=feature_dir, run_id="run-123")
            sink = RecordingSink(events=[])

            outcome = run(context, event_sink=sink)

        self.assertIsInstance(outcome, RunSetupError)
        self.assertEqual(outcome.missing_artifacts, ("tasks.json",))
        self.assertEqual([type(event) for event in sink.events], [RunStartedEvent, RunFinishedEvent])

    def test_run_repeats_until_a_terminal_outcome_is_returned(self) -> None:
        with TemporaryDirectory() as temp_dir:
            feature_dir = Path(temp_dir) / "feature"
            feature_dir.mkdir()
            (feature_dir / "spec.md").write_text("# spec\n", encoding="utf-8")
            (feature_dir / "tasks.json").write_text("{}", encoding="utf-8")
            context = RunContext(feature_dir=feature_dir, run_id="run-123", max_iterations=5)
            sink = RecordingSink(events=[])

            class FakeCodeStep:
                step_id = "code"

                def __init__(self) -> None:
                    self.calls = 0

                def execute(self, run_context):
                    self.calls += 1
                    if self.calls == 1:
                        return RepeatStepResult()
                    return CompleteStepResult()

            with patch("ralph.workflow.CodeStep", FakeCodeStep):
                outcome = run(context, event_sink=sink)

        self.assertIsInstance(outcome, RunCompleted)
        self.assertEqual(outcome.iterations, 2)
        self.assertEqual(outcome.run_id, "run-123")

        step_started_events = [event for event in sink.events if isinstance(event, StepStartedEvent)]
        self.assertEqual([event.iteration for event in step_started_events], [1, 2])

        step_finished_events = [event for event in sink.events if isinstance(event, StepFinishedEvent)]
        self.assertEqual([event.outcome for event in step_finished_events], ["repeat", "complete"])

        agent_invoked_events = [event for event in sink.events if isinstance(event, AgentInvokedEvent)]
        self.assertEqual([event.iteration for event in agent_invoked_events], [1, 2])

    def test_run_returns_blocked_and_failed_outcomes_verbatim(self) -> None:
        with TemporaryDirectory() as temp_dir:
            feature_dir = Path(temp_dir) / "feature"
            feature_dir.mkdir()
            (feature_dir / "spec.md").write_text("# spec\n", encoding="utf-8")
            (feature_dir / "tasks.json").write_text("{}", encoding="utf-8")

            for step_result, expected_type in (
                (BlockedStepResult(blocker_text="Need input"), RunBlocked),
                (
                    FailedStepResult(
                        failure_summary="Need a fix",
                        raw_response='{"outcome":"fail","failure_summary":"Need a fix"}',
                    ),
                    RunFailed,
                ),
            ):
                with self.subTest(step_result=step_result):
                    context = RunContext(feature_dir=feature_dir, run_id="run-123")
                    sink = RecordingSink(events=[])

                    class FakeCodeStep:
                        step_id = "code"

                        def execute(self, run_context):
                            return step_result

                    with patch("ralph.workflow.CodeStep", FakeCodeStep):
                        outcome = run(context, event_sink=sink)

                    self.assertIsInstance(outcome, expected_type)
                    self.assertEqual(outcome.run_id, "run-123")
                    self.assertEqual(outcome.iterations, 1)

                    finished_events = [
                        event for event in sink.events if isinstance(event, RunFinishedEvent)
                    ]
                    self.assertEqual(len(finished_events), 1)
                    self.assertEqual(finished_events[0].run_id, "run-123")

                    if isinstance(outcome, RunBlocked):
                        self.assertEqual(outcome.blocker_text, "Need input")
                    else:
                        self.assertEqual(outcome.failure_summary, "Need a fix")
                        self.assertEqual(
                            outcome.raw_response,
                            '{"outcome":"fail","failure_summary":"Need a fix"}',
                        )

    def test_run_fails_when_iteration_cap_is_reached(self) -> None:
        with TemporaryDirectory() as temp_dir:
            feature_dir = Path(temp_dir) / "feature"
            feature_dir.mkdir()
            (feature_dir / "spec.md").write_text("# spec\n", encoding="utf-8")
            (feature_dir / "tasks.json").write_text("{}", encoding="utf-8")
            context = RunContext(feature_dir=feature_dir, run_id="run-123", max_iterations=2)
            sink = RecordingSink(events=[])

            class FakeCodeStep:
                step_id = "code"

                def execute(self, run_context):
                    return RepeatStepResult()

            with patch("ralph.workflow.CodeStep", FakeCodeStep):
                outcome = run(context, event_sink=sink)

        self.assertIsInstance(outcome, RunFailed)
        self.assertEqual(outcome.iterations, 2)
        self.assertIn("max-iterations limit (2)", outcome.failure_summary)
