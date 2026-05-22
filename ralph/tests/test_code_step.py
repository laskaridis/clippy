from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from ralph.agents.base import AgentResult
from ralph.lifecycle import BlockedStepResult, CompleteStepResult, FailedStepResult, RepeatStepResult
from ralph.orchestrator import RunContext
from ralph.workflow.code import CodeStep


class _FakeAgent:
    def __init__(self, result: AgentResult):
        self.result = result
        self.requests = []

    def invoke(self, request):
        self.requests.append(request)
        return self.result


class CodeStepTests(TestCase):
    def test_execute_rejects_unknown_agents(self) -> None:
        with TemporaryDirectory() as temp_dir:
            feature_dir = Path(temp_dir) / "feature"
            feature_dir.mkdir()

            result = CodeStep().execute(
                RunContext(
                    feature_dir=feature_dir,
                    agent_name="missing",
                )
            )

        self.assertIsInstance(result, FailedStepResult)
        self.assertEqual(str(result.failure_summary), "Unknown built-in agent: missing")
        self.assertIsNone(result.raw_response)

    def test_execute_parses_all_supported_step_outcomes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            feature_dir = Path(temp_dir) / "feature"
            feature_dir.mkdir()
            run_context = RunContext(feature_dir=feature_dir, run_id="run-123")

            cases = [
                (
                    '{"outcome":"repeat"}',
                    RepeatStepResult,
                ),
                (
                    '{"outcome":"complete"}',
                    CompleteStepResult,
                ),
                (
                    '{"outcome":"blocked","blocker_text":"Need input"}',
                    BlockedStepResult,
                ),
                (
                    '{"outcome":"fail","failure_summary":"Need a fix"}',
                    FailedStepResult,
                ),
            ]

            for raw_response, expected_type in cases:
                with self.subTest(raw_response=raw_response):
                    fake_agent = _FakeAgent(
                        AgentResult(
                            success=True,
                            command=("codex",),
                            stdout="",
                            stderr="",
                            raw_response=raw_response,
                        )
                    )
                    with patch("ralph.workflow.code.get_agent", return_value=fake_agent):
                        result = CodeStep().execute(run_context)

                    self.assertIsInstance(result, expected_type)
                    self.assertEqual(len(fake_agent.requests), 1)
                    self.assertEqual(fake_agent.requests[0].run_id, "run-123")
                    self.assertIn(str(feature_dir.resolve()), fake_agent.requests[0].prompt)

    def test_execute_rejects_non_json_and_invalid_payloads(self) -> None:
        with TemporaryDirectory() as temp_dir:
            feature_dir = Path(temp_dir) / "feature"
            feature_dir.mkdir()
            run_context = RunContext(feature_dir=feature_dir)

            cases = [
                '{"outcome":"complete"}\nHere is the explanation.',
                '{"outcome":"unknown"}',
                '{"outcome":"blocked"}',
                '{"outcome":"fail","failure_summary":""}',
            ]

            for raw_response in cases:
                with self.subTest(raw_response=raw_response):
                    fake_agent = _FakeAgent(
                        AgentResult(
                            success=True,
                            command=("codex",),
                            stdout="",
                            stderr="",
                            raw_response=raw_response,
                        )
                    )
                    with patch("ralph.workflow.code.get_agent", return_value=fake_agent):
                        result = CodeStep().execute(run_context)

                    self.assertIsInstance(result, FailedStepResult)
                    self.assertEqual(result.raw_response, raw_response)
