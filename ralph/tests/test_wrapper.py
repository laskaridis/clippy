from __future__ import annotations

import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase


class WrapperTests(TestCase):
    def test_legacy_run_arguments_delegate_to_python_cli(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        wrapper = repo_root / "ralph" / "ralph.sh"

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            args_path = temp_path / "python-args.txt"
            python3_path = temp_path / "python3"
            python3_path.write_text(
                "#!/usr/bin/env bash\n"
                f'printf "%s\\n" "$@" > "{args_path}"\n'
                "exit 37\n",
                encoding="utf-8",
            )
            python3_path.chmod(0o755)

            env = os.environ.copy()
            env["PATH"] = f"{temp_path}{os.pathsep}{env['PATH']}"

            result = subprocess.run(
                [
                    str(wrapper),
                    "--feature-dir",
                    "/tmp/feature",
                    "--max-iterations",
                    "7",
                    "--coding-model",
                    "test-model",
                ],
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )

            captured_args = args_path.read_text(encoding="utf-8").splitlines()

        self.assertEqual(result.returncode, 37)
        self.assertEqual(captured_args, ["-m", "ralph", "run", "/tmp/feature", "--max-iterations", "7", "--model", "test-model"])

    def test_retired_retro_flags_fail_fast_without_invoking_python(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        wrapper = repo_root / "ralph" / "ralph.sh"

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            args_path = temp_path / "python-args.txt"
            python3_path = temp_path / "python3"
            python3_path.write_text(
                "#!/usr/bin/env bash\n"
                f'printf "%s\\n" "$@" > "{args_path}"\n'
                "exit 37\n",
                encoding="utf-8",
            )
            python3_path.chmod(0o755)

            env = os.environ.copy()
            env["PATH"] = f"{temp_path}{os.pathsep}{env['PATH']}"

            result = subprocess.run(
                [str(wrapper), "--retro-only"],
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("Migration error: --retro-only is retired", result.stderr)
        self.assertFalse(args_path.exists())
