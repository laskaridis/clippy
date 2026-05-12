from __future__ import annotations

import json
from dataclasses import dataclass, field
from collections.abc import Callable
from pathlib import Path
import tempfile
import unittest

from ralph.agents.base import AgentResult
from ralph.config import resolve_run_config
from ralph.errors import BookkeepingValidationError
from ralph.lifecycle.orchestrator import RunOutcome, run
from ralph.session import RunSessionStore


@dataclass
class ScriptedLifecycleAgent:
    """Deterministic fake agent with optional call-indexed side effects."""

    responses: list[AgentResult]
    callbacks: dict[int, Callable[[], None]] = field(default_factory=dict)
    calls: list[tuple[str, str]] = field(default_factory=list, init=False)
    _cursor: int = field(default=0, init=False, repr=False)

    def invoke(self, prompt_text: str, *, model: str) -> AgentResult:
        self.calls.append((prompt_text, model))
        if self._cursor >= len(self.responses):
            raise AssertionError(f"ScriptedLifecycleAgent ran out of responses at call {self._cursor}.")

        callback = self.callbacks.get(self._cursor)
        if callback is not None:
            callback()

        response = self.responses[self._cursor]
        self._cursor += 1
        return response

    @property
    def invocation_count(self) -> int:
        return self._cursor


class RunLifecycleIntegrationTests(unittest.TestCase):
    def _make_feature_dir(
        self,
        root: Path,
        *,
        tasks_payload: dict,
        with_retro_output: bool = True,
    ) -> Path:
        feature_dir = root / "feature"
        feature_dir.mkdir()
        (feature_dir / "spec.md").write_text("spec\n", encoding="utf-8")
        (feature_dir / "tasks.json").write_text(json.dumps(tasks_payload, indent=2) + "\n", encoding="utf-8")
        if with_retro_output:
            (feature_dir / "ralph.retro.md").write_text("retro output\n", encoding="utf-8")
        return feature_dir

    def _make_config(self, root: Path, *, with_retro_output: bool = True):
        self._make_feature_dir(
            root,
            tasks_payload={
                "tasks": [
                    {"title": "first task", "status": "completed"},
                    {"title": "second task"},
                ]
            },
            with_retro_output=with_retro_output,
        )
        return resolve_run_config("feature", cwd=root, max_iterations=3)

    def test_run_completes_after_multiple_iterations_and_retro_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self._make_config(root)
            store = RunSessionStore(config)

            def complete_tasks_on_second_code_call() -> None:
                config.tasks_path.write_text(
                    json.dumps(
                        {
                            "tasks": [
                                {"title": "first task", "status": "completed"},
                                {"title": "second task", "status": "completed"},
                            ]
                        },
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )

            agent = ScriptedLifecycleAgent(
                responses=[
                    AgentResult(
                        stdout="RALPH_STATUS=CONTINUE\nStill working.\n",
                        exit_code=0,
                        metadata={"phase": "code-1"},
                    ),
                    AgentResult(
                        stdout="RALPH_STATUS=COMPLETE\nImplementation finished.\n",
                        exit_code=0,
                        metadata={"phase": "code-2"},
                    ),
                    AgentResult(
                        stdout="Retrospective complete.\n",
                        exit_code=0,
                        metadata={"phase": "retro"},
                    ),
                ],
                callbacks={1: complete_tasks_on_second_code_call},
            )

            outcome = run(config, agent)

            self.assertEqual(outcome, RunOutcome.COMPLETED)
            self.assertEqual(agent.invocation_count, 3)
            self.assertEqual(
                [call[1] for call in agent.calls],
                [config.coding_model, config.coding_model, config.retro_model],
            )
            self.assertFalse(config.lock_path.exists())
            self.assertTrue(config.db_path.is_file())
            self.assertFalse(config.current_session_path.exists())

            pointer = store.load_current_pointer()
            self.assertIsNotNone(pointer)
            assert pointer is not None
            session = store.load_current_session()
            self.assertIsNotNone(session)
            assert session is not None
            self.assertEqual(pointer.session_id, session.session_id)
            self.assertEqual(pointer.status, "completed")
            self.assertEqual(pointer.overall_outcome, "completed")

            self.assertEqual(session.iteration_count, 2)
            self.assertEqual(session.current_phase, "retro")
            self.assertEqual(session.last_phase_outcome, "completed")
            self.assertEqual(session.overall_outcome, "completed")

    def test_run_blocks_when_agent_reports_blocked_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self._make_config(root, with_retro_output=False)
            store = RunSessionStore(config)
            agent = ScriptedLifecycleAgent(
                responses=[
                    AgentResult(
                        stdout="RALPH_STATUS=BLOCKED\nWaiting on another team.\n",
                        exit_code=0,
                        metadata={"phase": "code"},
                    )
                ]
            )

            outcome = run(config, agent)

            self.assertEqual(outcome, RunOutcome.BLOCKED)
            self.assertEqual(agent.invocation_count, 1)
            self.assertFalse(config.lock_path.exists())
            self.assertTrue(config.db_path.is_file())
            self.assertFalse(config.current_session_path.exists())

            pointer = store.load_current_pointer()
            self.assertIsNotNone(pointer)
            assert pointer is not None
            self.assertEqual(pointer.status, "blocked")
            self.assertEqual(pointer.overall_outcome, "blocked")

            session = store.load_current_session()
            self.assertIsNotNone(session)
            assert session is not None
            self.assertEqual(session.overall_outcome, "blocked")
            self.assertEqual(session.last_phase_outcome, "blocked")
            self.assertEqual(session.iteration_count, 1)

    def test_run_refuses_to_start_when_incomplete_session_already_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self._make_config(root)
            store = RunSessionStore(config)
            store.create_session(session_id="existing-session")
            agent = ScriptedLifecycleAgent(responses=[])

            with self.assertRaises(BookkeepingValidationError):
                run(config, agent)

            self.assertEqual(agent.invocation_count, 0)
            session = store.load_current_session()
            self.assertIsNotNone(session)
            assert session is not None
            self.assertIsNone(session.overall_outcome)
            self.assertTrue(config.db_path.is_file())
            self.assertFalse(config.current_session_path.exists())

    def test_run_degrades_when_retrospective_fails_after_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_feature_dir(
                root,
                tasks_payload={
                    "tasks": [
                        {"title": "first task", "status": "completed"},
                        {"title": "second task", "status": "completed"},
                    ]
                },
                with_retro_output=True,
            )
            config = resolve_run_config("feature", cwd=root, max_iterations=3)
            store = RunSessionStore(config)
            agent = ScriptedLifecycleAgent(
                responses=[
                    AgentResult(
                        stdout="RALPH_STATUS=COMPLETE\nImplementation finished.\n",
                        exit_code=0,
                        metadata={"phase": "code"},
                    ),
                    AgentResult(
                        stdout="Retrospective failed.\n",
                        exit_code=1,
                        metadata={"phase": "retro"},
                    ),
                ]
            )

            outcome = run(config, agent)

            self.assertEqual(outcome, RunOutcome.DEGRADED)
            self.assertEqual(agent.invocation_count, 2)
            self.assertFalse(config.lock_path.exists())
            self.assertTrue(config.db_path.is_file())
            self.assertFalse(config.current_session_path.exists())

            session = store.load_current_session()
            self.assertIsNotNone(session)
            assert session is not None
            self.assertEqual(session.current_phase, "retro")
            self.assertEqual(session.last_phase_outcome, "failed")
            self.assertEqual(session.overall_outcome, "degraded")


if __name__ == "__main__":
    unittest.main()
