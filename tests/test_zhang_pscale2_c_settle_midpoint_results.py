from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "analyze_zhang_pscale2_c_settle_midpoint_results.py"
STAGE = REPO_ROOT / "docs" / "reproduction_goal" / "03_zhang_particle_scale"


class ZhangPscale2CSettleMidpointResultsTest(unittest.TestCase):
    def test_compares_settle_1_2_4_with_paired_runtime_provenance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            evidence = tmp / "evidence" / "pscale2_c_settle_midpoint_run_123"
            evidence.mkdir(parents=True)
            source = STAGE / "data" / "pscale2_c_settle_candidates.csv"
            with source.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

            pressures = [575.0, 560.0, 610.0, 580.0, 571.0]
            for row, pressure in zip(rows, pressures, strict=True):
                row["artifact"] = row["artifact"].replace("settle4", "settle2")
                row["p95_mpa"] = str(pressure)
                row["status"] = "pass"
                row["initial_settle_steps"] = "40000"
                row["stage_settle_steps"] = "40000"
                row["final_settle_steps"] = "100000"
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
                    "--settle4",
                    str(source),
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
                "c_settle_midpoint_improves_tradeoff",
            )
            self.assertEqual(summary["groups"]["settle1"]["trend_pass_count"], 4)
            self.assertEqual(summary["groups"]["settle2"]["trend_pass_count"], 5)
            self.assertEqual(summary["groups"]["settle2"]["pass_and_window_count"], 3)
            self.assertEqual(summary["groups"]["settle4"]["pass_and_window_count"], 1)
            self.assertEqual(summary["settle_steps"]["2"]["final"], 100000)

            report = (tmp / "report.md").read_text(encoding="utf-8")
            self.assertIn("Three-Way Comparison", report)
            self.assertIn("c_settle_midpoint_improves_tradeoff", report)
            paired = (tmp / "data" / "pscale2_c_settle_midpoint_paired.csv").read_text(
                encoding="utf-8"
            )
            self.assertIn("settle2_minus_1_mpa", paired)


if __name__ == "__main__":
    unittest.main()
