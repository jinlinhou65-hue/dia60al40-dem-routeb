from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "analyze_zhang_pscale2_c_settle_results.py"
STAGE = REPO_ROOT / "docs" / "reproduction_goal" / "03_zhang_particle_scale"


class ZhangPscale2CSettleResultsTest(unittest.TestCase):
    def test_rejects_4x_settle_after_paired_seed_analysis(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--evidence-root",
                    str(STAGE / "evidence"),
                    "--run-id",
                    "28710536524",
                    "--baseline",
                    str(STAGE / "data" / "pscale2_c_pressure_lift_candidates.csv"),
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
                "c_settle_improves_trend_but_worsens_pressure_robustness",
            )
            self.assertEqual(summary["settle_pass_count"], 5)
            self.assertEqual(summary["settle_window_count"], 1)
            self.assertEqual(summary["settle_pass_and_window_count"], 1)
            self.assertAlmostEqual(summary["baseline_p95_mean_mpa"], 574.2111362)
            self.assertAlmostEqual(summary["settle_p95_mean_mpa"], 567.231842)
            self.assertGreater(summary["settle_p95_cv"], summary["baseline_p95_cv"])
            self.assertEqual(summary["test_settle_steps"]["final"], 200000)

            report = (tmp / "report.md").read_text(encoding="utf-8")
            self.assertIn("Reject settle scale 4", report)
            paired = (tmp / "data" / "pscale2_c_settle_paired.csv").read_text(
                encoding="utf-8"
            )
            self.assertIn("651.920164", paired)


if __name__ == "__main__":
    unittest.main()
