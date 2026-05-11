from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ralph.config import resolve_run_config
from ralph.errors import BookkeepingValidationError
from ralph.lifecycle.orchestrator import RunOutcome, resume
from ralph.session import LockState, RunSessionStore
from ralph.tests.fakes import agent_result, scripted_agent


class ResumeLifecycleIntegrationTests(unittest.TestCase):
    def _make_feature_dir(self, root: Path) -> Path:
        feature_dir = root / "feature"
        feature_dir.mkdir()
        (feature_dir / "spec.md").write_text("spec\n", encoding="utf-8")
        (feature_dir / "tasks.json").write_text(
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
        (feature_dir / "ralph.retro.md").write_text("retro output\n", encoding="utf-8")
        return feature_dir

    def _make_config(self, root: Path):
        self._make_feature_dir(root)
        return resolve_run_config("feature", cwd=root, max_iterations=3)

    def _seed_incomplete_session(self, store: RunSessionStore, *, session_id: str, started_at: datetime) -> None:
        store.create_session(session_id=session_id, started_at=started_at)
        store.update_session(
            session_id,
            current_phase="code",
            iteration_count=1,
            last_phase_outcome="next_iteration",
        )

    def test_resume_after_interrupted_run_continues_the_next_iteration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self._make_config(root)
            store = RunSessionStore(config)
            started_at = datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc)
            self._seed_incomplete_session(store, session_id="session-1", started_at=started_at)
            store.acquire_lock("session-1", started_at=started_at, last_heartbeat_at=started_at)

            agent = scripted_agent(
                agent_result("RALPH_STATUS=COMPLETE\nIteration resumed.\n", metadata={"phase": "code"}),
                agent_result("Retrospective complete.\n", metadata={"phase": "retro"}),
            )

            outcome = resume(config, agent)

            self.assertEqual(outcome, RunOutcome.COMPLETED)
            self.assertEqual(agent.invocation_count, 2)
            self.assertEqual([call.model for call in agent.calls], [config.coding_model, config.retro_model])
            self.assertFalse(config.lock_path.exists())

            pointer = store.load_current_pointer()
            self.assertIsNotNone(pointer)
            assert pointer is not None
            self.assertEqual(pointer.session_id, "session-1")
            self.assertEqual(pointer.status, "completed")
            self.assertEqual(pointer.overall_outcome, "completed")

            session = store.load_current_session()
            self.assertIsNotNone(session)
            assert session is not None
            self.assertEqual(session.iteration_count, 2)
            self.assertEqual(session.current_phase, "retro")
            self.assertEqual(session.last_phase_outcome, "completed")
            self.assertEqual(session.overall_outcome, "completed")

    def test_resume_recovers_from_stale_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self._make_config(root)
            store = RunSessionStore(config)
            started_at = datetime(2026, 5, 11, 11, 0, tzinfo=timezone.utc)
            stale_heartbeat = started_at
            self._seed_incomplete_session(store, session_id="session-2", started_at=started_at)
            store.acquire_lock(
                "stale-lock",
                pid=12345,
                hostname="stale-host",
                started_at=started_at,
                last_heartbeat_at=stale_heartbeat,
            )

            checked_at = started_at + timedelta(minutes=12)

            with patch("ralph.session._current_hostname", return_value="stale-host"), patch(
                "ralph.session._process_is_running",
                return_value=False,
            ), patch("ralph.session._utc_now", return_value=checked_at):
                inspection = store.inspect_lock(now=checked_at)
                self.assertEqual(inspection.state, LockState.STALE)
                self.assertTrue(inspection.is_stale)
                outcome = resume(
                    config,
                    scripted_agent(
                        agent_result("RALPH_STATUS=COMPLETE\nIteration resumed.\n", metadata={"phase": "code"}),
                        agent_result("Retrospective complete.\n", metadata={"phase": "retro"}),
                    ),
                )

            self.assertEqual(outcome, RunOutcome.COMPLETED)
            self.assertFalse(config.lock_path.exists())

            pointer = store.load_current_pointer()
            self.assertIsNotNone(pointer)
            assert pointer is not None
            self.assertEqual(pointer.session_id, "session-2")
            self.assertEqual(pointer.status, "completed")
            self.assertEqual(pointer.overall_outcome, "completed")

            session = store.load_current_session()
            self.assertIsNotNone(session)
            assert session is not None
            self.assertEqual(session.overall_outcome, "completed")
            self.assertEqual(session.current_phase, "retro")

    def test_resume_rejects_terminal_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self._make_config(root)
            store = RunSessionStore(config)
            started_at = datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc)
            store.create_session(session_id="terminal-session", started_at=started_at)
            store.finalize_session("terminal-session", overall_outcome="completed", ended_at=started_at)

            with self.assertRaises(BookkeepingValidationError):
                resume(config, scripted_agent())


if __name__ == "__main__":
    unittest.main()
