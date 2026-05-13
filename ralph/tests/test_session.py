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

    def test_create_session_writes_database_and_uses_sqlite_latest_ordering(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = self._make_store(root)
            started_at = datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc)

            first_session = store.create_session(session_id="session-1", started_at=started_at)
            second_session = store.create_session(session_id="session-2", started_at=started_at)

            self.assertTrue(store.config.db_path.is_file())
            self.assertEqual(first_session.session_id, "session-1")
            self.assertEqual(second_session.session_id, "session-2")
            self.assertEqual(first_session.feature_dir, store.config.feature_dir)
            self.assertEqual(first_session.iteration_count, 0)
            self.assertIsNone(first_session.overall_outcome)

            with sqlite3.connect(store.config.db_path) as conn:
                self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 1)
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0], 2)

            loaded = store.load_current_session()
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded.session_id, second_session.session_id)
            self.assertEqual(loaded.updated_at, started_at)

            refreshed_first = store.update_session(
                "session-1",
                current_phase="retro",
                iteration_count=1,
                updated_at=started_at + timedelta(minutes=5),
            )
            self.assertEqual(refreshed_first.session_id, "session-1")
            self.assertEqual(refreshed_first.current_phase, "retro")

            loaded_after_refresh = store.load_current_session()
            self.assertIsNotNone(loaded_after_refresh)
            assert loaded_after_refresh is not None
            self.assertEqual(loaded_after_refresh.session_id, "session-1")
            self.assertEqual(loaded_after_refresh.updated_at, started_at + timedelta(minutes=5))

    def test_inspect_lock_reports_active_stale_and_remote_host_states(self) -> None:
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
            )

            with patch("ralph.session._current_hostname", return_value="test-host"), patch(
                "ralph.session._process_is_running",
                return_value=True,
            ) as process_is_running:
                active = store.inspect_lock(now=checked_at)
                self.assertEqual(active.state, LockState.ACTIVE)
                self.assertFalse(active.is_stale)
                self.assertTrue(active.host_matches)
                self.assertTrue(active.process_running)
                process_is_running.assert_called_once_with(12345)

            with patch("ralph.session._current_hostname", return_value="test-host"), patch(
                "ralph.session._process_is_running",
                return_value=False,
            ) as process_is_running:
                stale = store.inspect_lock(now=checked_at)
                self.assertEqual(stale.state, LockState.STALE)
                self.assertTrue(stale.is_stale)
                self.assertTrue(stale.host_matches)
                self.assertFalse(stale.process_running)
                process_is_running.assert_called_once_with(12345)

            with patch("ralph.session._current_hostname", return_value="remote-host"), patch(
                "ralph.session._process_is_running",
                return_value=False,
            ) as process_is_running:
                remote = store.inspect_lock(now=checked_at)
                self.assertEqual(remote.state, LockState.ACTIVE)
                self.assertFalse(remote.is_stale)
                self.assertFalse(remote.host_matches)
                self.assertIsNone(remote.process_running)
                process_is_running.assert_not_called()

    def test_acquire_and_release_lock_update_the_database_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = self._make_store(root)
            lock = store.acquire_lock("session-1", pid=12345, hostname="test-host")

            self.assertEqual(lock.session_id, "session-1")
            self.assertTrue(store.config.db_path.is_file())

            with sqlite3.connect(store.config.db_path) as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM active_lock").fetchone()[0], 1)

            lock = store.load_lock()
            self.assertIsNotNone(lock)
            assert lock is not None
            self.assertEqual(lock.session_id, "session-1")

            with self.assertRaises(BookkeepingValidationError):
                store.acquire_lock("session-2")

            store.release_lock("session-1")
            self.assertIsNone(store.load_lock())

            with sqlite3.connect(store.config.db_path) as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM active_lock").fetchone()[0], 0)

    def test_legacy_artifacts_are_ignored_by_sqlite_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = self._make_store(root)
            legacy_sessions_dir = store.config.ralph_dir / "sessions"
            legacy_sessions_dir.mkdir(parents=True, exist_ok=True)
            (legacy_sessions_dir / "current.json").write_text("not-json", encoding="utf-8")
            (legacy_sessions_dir / "session-legacy.json").write_text("still-not-json", encoding="utf-8")
            (store.config.ralph_dir / "lock").write_text("legacy-lock", encoding="utf-8")

            session = store.create_session(session_id="session-1", started_at=datetime(2026, 5, 11, 13, 0, tzinfo=timezone.utc))

            self.assertTrue(store.config.db_path.is_file())
            loaded = store.load_current_session()
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded.session_id, session.session_id)
            self.assertEqual(store.load_session("session-1").session_id, "session-1")


if __name__ == "__main__":
    unittest.main()
