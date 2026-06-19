from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "run_paper_algorithm_reproduction.py"
VALIDATOR = REPO_ROOT / ".github" / "scripts" / "validate_paper_reproduction_content.py"


class PaperContentValidationTest(unittest.TestCase):
    def test_validator_accepts_generated_all_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            outdir = Path(tmp) / "paper"
            subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--paper",
                    "all",
                    "--outdir",
                    str(outdir),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=True,
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--paper",
                    "all",
                    "--outdir",
                    str(outdir),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn("status=pass", result.stdout)
            self.assertIn('"papers"', result.stdout)

    def test_validator_accepts_generated_single_paper_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            outdir = Path(tmp) / "paper"
            subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--paper",
                    "liu",
                    "--outdir",
                    str(outdir),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=True,
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--paper",
                    "liu",
                    "--outdir",
                    str(outdir),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn("status=pass", result.stdout)
            self.assertIn('"liu"', result.stdout)

    def test_validator_fails_when_core_outputs_are_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--paper",
                    "all",
                    "--outdir",
                    str(Path(tmp) / "missing"),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("missing required file", result.stderr)


if __name__ == "__main__":
    unittest.main()
