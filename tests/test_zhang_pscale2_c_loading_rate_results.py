from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "analyze_zhang_pscale2_c_loading_rate_results.py"
STAGE = REPO_ROOT / "docs" / "reproduction_goal" / "03_zhang_particle_scale"


class ZhangPscale2CLoadingRateResultsTest(unittest.TestCase):
    def test_accepts_only_a_paired_lower_variance_loading_rate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            evidence = tmp / "evidence" / "pscale2_c_loading_rate_recheck_run_123"
            evidence.mkdir(parents=True)
            source = STAGE / "data" / "pscale2_c_settle_candidates.csv"
            with source.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

            pressures = [575.0, 560.0, 610.0, 580.0, 600.0]
            for row, pressure in zip(rows, pressures, strict=True):
                row["artifact"] = row["artifact"].replace("settle4", "settle1-vel25")
                row["p95_mpa"] = str(pressure)
                row["status"] = "pass"
                row["top_velocity_cm_s"] = "25"
                row["initial_settle_steps"] = "20000"
                row["stage_settle_steps"] = "20000"
                row["final_settle_steps"] = "50000"
            artifact_csv = evidence / "zhang_calibration_best_by_run.csv"
            with artifact_csv.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--evidence-root",
                    str(tmp / "evidence"),
                    "--run-id",
                    "123",
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
            self.assertEqual(summary["decision"], "c_loading_rate_improves_tradeoff")
            self.assertEqual(summary["test"]["trend_pass_count"], 5)
            self.assertEqual(summary["test"]["pass_and_window_count"], 4)
            self.assertLess(summary["test"]["p95_cv"], summary["baseline"]["p95_cv"])
            self.assertEqual(summary["settle_steps"]["final"], 50000)

            report = (tmp / "report.md").read_text(encoding="utf-8")
            self.assertIn("50 cm/s baseline", report)
            self.assertIn("c_loading_rate_improves_tradeoff", report)

    def test_rejects_real_25cm_s_artifact_because_cv_increases(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--evidence-root",
                    str(STAGE / "evidence"),
                    "--run-id",
                    "28729754426",
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
            self.assertEqual(summary["decision"], "c_loading_rate_not_better")
            self.assertAlmostEqual(summary["test"]["p95_mean_mpa"], 578.432016)
            self.assertAlmostEqual(summary["test"]["p95_cv"], 0.052841281320507236)
            self.assertEqual(summary["test"]["trend_pass_count"], 5)
            self.assertEqual(summary["test"]["pass_and_window_count"], 3)
            self.assertGreater(summary["test"]["p95_cv"], summary["baseline"]["p95_cv"])


if __name__ == "__main__":
    unittest.main()
