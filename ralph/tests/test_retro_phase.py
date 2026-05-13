from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from ralph.config import resolve_run_config
from ralph.errors import RetrospectiveFailureError
from ralph.lifecycle.phases.base import PhaseOutcome
from ralph.lifecycle.phases.retro.phase import run_retro_phase
from ralph.tests.fakes import agent_result, scripted_agent


class RetroPhaseTests(unittest.TestCase):
    def _make_config(self, root: Path):
        feature_dir = root / "feature"
        feature_dir.mkdir()
        (feature_dir / "spec.md").write_text("spec\n", encoding="utf-8")
        (feature_dir / "tasks.json").write_text('{"tasks":[]}\n', encoding="utf-8")
        (feature_dir / "ralph.txt").write_text("coding log\n", encoding="utf-8")
        (feature_dir / "ralph.retro.md").write_text("retro output\n", encoding="utf-8")
        return resolve_run_config("feature", cwd=root)

    def test_validate_retro_prerequisites_requires_ralph_txt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feature_dir = root / "feature"
            feature_dir.mkdir()
            (feature_dir / "spec.md").write_text("spec\n", encoding="utf-8")
            (feature_dir / "tasks.json").write_text('{"tasks":[]}\n', encoding="utf-8")

            config = resolve_run_config("feature", cwd=root)

            with self.assertRaises(RetrospectiveFailureError):
                run_retro_phase(config, scripted_agent(agent_result("unused\n")))

    def test_run_retro_phase_completes_with_existing_output_and_fake_agent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self._make_config(root)
            agent = scripted_agent(agent_result("retro complete\n", exit_code=0, metadata={"source": "fake"}))

            result = run_retro_phase(config, agent)

            self.assertEqual(result.outcome, PhaseOutcome.COMPLETED)
            self.assertEqual(agent.invocation_count, 1)
            self.assertEqual(agent.calls[0].model, config.retro_model)
            self.assertEqual(result.metadata["retro_output_present"], True)
            self.assertEqual(result.metadata["ralph_txt_path"], str(config.ralph_txt_path))


if __name__ == "__main__":
    unittest.main()
