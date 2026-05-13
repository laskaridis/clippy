from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from ralph.config import resolve_run_config
from ralph.errors import BookkeepingValidationError
from ralph.lifecycle.phases.code.status import parse_code_status
from ralph.lifecycle.phases.code.validation import validate_code_bookkeeping


class CodeBookkeepingTests(unittest.TestCase):
    def _make_config(self, root: Path) -> tuple[Path, object]:
        feature_dir = root / "feature"
        feature_dir.mkdir()
        (feature_dir / "spec.md").write_text("spec\n", encoding="utf-8")
        (feature_dir / "tasks.json").write_text(
            '{"tasks":[{"title":"done","status":"completed"},{"title":"pending"}]}\n',
            encoding="utf-8",
        )
        return feature_dir, resolve_run_config("feature", cwd=root)

    def test_validate_code_bookkeeping_counts_missing_task_status_as_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feature_dir, config = self._make_config(root)

            result = validate_code_bookkeeping(
                config,
                parse_code_status("RALPH_STATUS=CONTINUE\nWorking on it.\n"),
            )

            self.assertEqual(result.task_count, 2)
            self.assertEqual(result.completed_task_count, 1)
            self.assertEqual(result.pending_task_count, 1)
            self.assertTrue(result.ralph_txt_created)
            self.assertTrue((feature_dir / "ralph.txt").is_file())
            self.assertFalse(result.all_tasks_completed)

    def test_validate_code_bookkeeping_rejects_complete_when_tasks_remain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, config = self._make_config(root)

            with self.assertRaises(BookkeepingValidationError):
                validate_code_bookkeeping(
                    config,
                    parse_code_status("RALPH_STATUS=COMPLETE\nFinished.\n"),
                )


if __name__ == "__main__":
    unittest.main()
