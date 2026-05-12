from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ralph.config import resolve_run_config
from ralph.errors import BookkeepingValidationError
from ralph.session import LockState, RunSessionStore


class SessionStoreTests(unittest.TestCase):
    def _make_store(self, root: Path) -> RunSessionStore:
        feature_dir = root / "feature"
        feature_dir.mkdir()
        (feature_dir / "spec.md").write_text("spec\n", encoding="utf-8")
        (feature_dir / "tasks.json").write_text('{"tasks": []}\n', encoding="utf-8")
        config = resolve_run_config("feature", cwd=root)
        return RunSessionStore(config)

    def test_create_session_writes_session_and_current_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = self._make_store(root)
            started_at = datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc)

            first_session = store.create_session(session_id="session-1", started_at=started_at)
            second_session = store.create_session(session_id="session-2", started_at=started_at)

            self.assertTrue(store.config.db_path.is_file())
            self.assertFalse(store.current_session_path.exists())
            self.assertEqual(first_session.session_id, "session-1")
            self.assertEqual(second_session.session_id, "session-2")
            self.assertEqual(first_session.feature_dir, store.config.feature_dir)
            self.assertEqual(first_session.iteration_count, 0)
            self.assertIsNone(first_session.overall_outcome)

            with sqlite3.connect(store.config.db_path) as conn:
                self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 1)
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0], 2)

            pointer = store.load_current_pointer()
            self.assertIsNotNone(pointer)
            assert pointer is not None
            self.assertEqual(pointer.session_id, "session-2")
            self.assertEqual(pointer.status, "incomplete")
            self.assertIsNone(pointer.overall_outcome)

            loaded = store.load_current_session()
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded.session_id, second_session.session_id)

            first_loaded = store.load_session("session-1")
            self.assertEqual(first_loaded.session_id, "session-1")
            self.assertEqual(first_loaded.started_at, started_at)

    def test_inspect_lock_reports_absent_active_and_stale_states(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = self._make_store(root)
            checked_at = datetime(2026, 5, 11, 12, 30, tzinfo=timezone.utc)
            start_at = checked_at - timedelta(minutes=12)

            absent = store.inspect_lock(now=checked_at)
            self.assertEqual(absent.state, LockState.ABSENT)
            self.assertIsNone(absent.lock)

            store.acquire_lock(
                "session-1",
                pid=12345,
                hostname="test-host",
                started_at=start_at,
                last_heartbeat_at=start_at,
            )

            with patch("ralph.session._current_hostname", return_value="test-host"), patch(
                "ralph.session._process_is_running",
                return_value=True,
            ):
                active = store.inspect_lock(now=checked_at)
                self.assertEqual(active.state, LockState.ACTIVE)
                self.assertFalse(active.is_stale)
                self.assertTrue(active.host_matches)
                self.assertTrue(active.process_running)

            with patch("ralph.session._current_hostname", return_value="test-host"), patch(
                "ralph.session._process_is_running",
                return_value=False,
            ):
                stale = store.inspect_lock(now=checked_at)
                self.assertEqual(stale.state, LockState.STALE)
                self.assertTrue(stale.is_stale)
                self.assertTrue(stale.host_matches)
                self.assertFalse(stale.process_running)
                self.assertGreater(stale.heartbeat_age, timedelta(minutes=10))

    def test_acquire_lock_does_not_overwrite_an_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = self._make_store(root)
            existing_payload = '{"schema_version": 1, "session_id": "existing"}\n'
            store.lock_path.parent.mkdir(parents=True, exist_ok=True)
            store.lock_path.write_text(existing_payload, encoding="utf-8")

            with patch.object(RunSessionStore, "load_lock", return_value=None):
                with self.assertRaises(BookkeepingValidationError):
                    store.acquire_lock("session-2")

            self.assertEqual(store.lock_path.read_text(encoding="utf-8"), existing_payload)


if __name__ == "__main__":
    unittest.main()
