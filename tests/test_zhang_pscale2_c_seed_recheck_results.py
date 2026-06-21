from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "analyze_zhang_pscale2_c_seed_recheck_results.py"
EVIDENCE = REPO_ROOT / "docs" / "reproduction_goal" / "03_zhang_particle_scale" / "evidence"


class ZhangPscale2CSeedRecheckResultsTest(unittest.TestCase):
    def test_analyzes_imported_seed_recheck_as_not_robust(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--evidence-root",
                    str(EVIDENCE),
                    "--run-id",
                    "27898770533",
                    "--outdir",
                    str(tmp / "data"),
                    "--figure-dir",
                    str(tmp / "figures"),
                    "--report",
                    str(tmp / "report.md"),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["decision"], "c_candidate_not_seed_robust")
            self.assertEqual(summary["seed_count"], 5)
            self.assertEqual(summary["pass_count"], 4)
            self.assertEqual(summary["pressure_window_count"], 1)
            self.assertEqual(summary["pass_and_window_count"], 1)
            self.assertAlmostEqual(summary["p95_mean_mpa"], 524.6190186)

            report = (tmp / "report.md").read_text(encoding="utf-8")
            self.assertIn("C is not seed-robust", report)
            acceptance = (tmp / "data" / "pscale2_c_seed_recheck_acceptance.csv").read_text(
                encoding="utf-8"
            )
            self.assertIn("c_candidate_not_seed_robust", acceptance)


if __name__ == "__main__":
    unittest.main()
