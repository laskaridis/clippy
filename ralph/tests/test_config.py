from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from ralph.config import resolve_run_config
from ralph.errors import FeatureValidationError


class RunConfigTests(unittest.TestCase):
    def _make_feature_dir(self, root: Path) -> Path:
        feature_dir = root / "feature"
        feature_dir.mkdir()
        (feature_dir / "spec.md").write_text("spec\n", encoding="utf-8")
        (feature_dir / "tasks.json").write_text(json.dumps({"tasks": []}), encoding="utf-8")
        return feature_dir

    def test_resolve_run_config_derives_feature_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_feature_dir(root)

            config = resolve_run_config(
                "feature",
                cwd=root,
                max_iterations=3,
                coding_model="coding-model",
                retro_model="retro-model",
                retro_only=True,
                agent_identifier="codex",
            )

            feature_dir = (root / "feature").resolve()
            self.assertEqual(config.feature_dir, feature_dir)
            self.assertEqual(config.spec_path, feature_dir / "spec.md")
            self.assertEqual(config.tasks_path, feature_dir / "tasks.json")
            self.assertEqual(config.ralph_txt_path, feature_dir / "ralph.txt")
            self.assertEqual(config.retro_path, feature_dir / "ralph.retro.md")
            self.assertEqual(config.ralph_dir, feature_dir / ".ralph")
            self.assertEqual(config.sessions_dir, feature_dir / ".ralph" / "sessions")
            self.assertEqual(config.current_session_path, feature_dir / ".ralph" / "sessions" / "current.json")
            self.assertEqual(config.lock_path, feature_dir / ".ralph" / "lock")
            self.assertTrue(config.retro_only)
            self.assertEqual(config.agent_identifier, "codex")

    def test_resolve_run_config_rejects_absolute_feature_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feature_dir = self._make_feature_dir(root)

            with self.assertRaises(FeatureValidationError):
                resolve_run_config(feature_dir, cwd=root)

    def test_resolve_run_config_rejects_missing_required_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feature_dir = root / "feature"
            feature_dir.mkdir()
            (feature_dir / "spec.md").write_text("spec\n", encoding="utf-8")

            with self.assertRaises(FeatureValidationError):
                resolve_run_config("feature", cwd=root)


if __name__ == "__main__":
    unittest.main()
