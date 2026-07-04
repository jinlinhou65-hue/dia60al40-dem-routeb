from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "analyze_zhang_pscale2_c_pressure_lift_results.py"
STAGE = REPO_ROOT / "docs" / "reproduction_goal" / "03_zhang_particle_scale"


class ZhangPscale2CPressureLiftResultsTest(unittest.TestCase):
    def test_compares_pressure_lift_against_same_seed_baseline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--evidence-root",
                    str(STAGE / "evidence"),
                    "--run-id",
                    "28709925303",
                    "--baseline",
                    str(STAGE / "data" / "pscale2_c_seed_recheck_candidates.csv"),
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
            self.assertEqual(
                summary["decision"],
                "c_pressure_lift_improves_but_not_seed_robust",
            )
            self.assertEqual(summary["seed_count"], 5)
            self.assertEqual(summary["pressure_lift_pass_count"], 4)
            self.assertEqual(summary["pressure_lift_window_count"], 3)
            self.assertEqual(summary["baseline_pass_and_window_count"], 1)
            self.assertEqual(summary["pressure_lift_pass_and_window_count"], 2)
            self.assertAlmostEqual(summary["baseline_p95_mean_mpa"], 524.6190186)
            self.assertAlmostEqual(summary["pressure_lift_p95_mean_mpa"], 574.2111362)
            self.assertLess(summary["pressure_lift_p95_cv"], summary["baseline_p95_cv"])

            paired = (tmp / "data" / "pscale2_c_pressure_lift_paired.csv").read_text(
                encoding="utf-8"
            )
            self.assertIn("79.604553", paired)
            report = (tmp / "report.md").read_text(encoding="utf-8")
            self.assertIn("do not raise Emax again as the sole control", report)


if __name__ == "__main__":
    unittest.main()
