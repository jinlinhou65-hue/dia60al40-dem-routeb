from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "analyze_zhang_pscale2_recalibration_results.py"


class ZhangPscale2RecalibrationResultsTest(unittest.TestCase):
    def test_summarizes_recalibration_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "evidence"
            write_run(
                evidence / "pscale2_recalibration_run_1",
                [
                    row("C", 61.0, 560.0, "pass", "candidate_pass", 0.1),
                    row("C", 65.0, 590.0, "pass", "candidate_pass", 0.2),
                ],
            )
            write_run(
                evidence / "pscale2_recalibration_run_2",
                [
                    row("D", 55.0, 635.0, "review", "needs_participation_increase", -0.1),
                ],
            )
            outdir = root / "data"
            figures = root / "figures"
            report = root / "report.md"

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--evidence-root",
                    str(evidence),
                    "--run-ids-json",
                    '["1","2"]',
                    "--outdir",
                    str(outdir),
                    "--figure-dir",
                    str(figures),
                    "--report",
                    str(report),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

            payload = json.loads(result.stdout)
            self.assertEqual(payload["row_count"], 3)
            self.assertEqual(payload["pressure_window_candidate_count"], 2)
            self.assertEqual(payload["pass_and_window_candidate_count"], 1)
            by_size = {row["diamond_size_case"]: row for row in payload["size_summary"]}
            self.assertEqual(by_size["C"]["decision"], "candidate_ready_for_seed_recheck")
            self.assertEqual(by_size["D"]["decision"], "hold_pressure_candidate_and_tune_participation")
            self.assertTrue((outdir / "pscale2_recalibration_candidates.csv").exists())
            self.assertTrue((outdir / "pscale2_recalibration_acceptance.csv").exists())
            self.assertTrue(report.exists())


def row(
    size: str,
    emax: float,
    p95: float,
    status: str,
    diagnosis: str,
    participation_delta: float,
) -> dict[str, str]:
    return {
        "artifact": f"artifact-{size}-{emax}",
        "diamond_size_case": size,
        "particle_count_scale": "2",
        "particle_count_total": "100",
        "seed_index": "2",
        "e_al_emax_gpa": str(emax),
        "mu_scale": "0.7",
        "p95_mpa": str(p95),
        "status": status,
        "calibration_diagnosis": diagnosis,
        "threshold_factor": "0.05",
        "min_chain_length": "2",
        "participation_delta": str(participation_delta),
        "d1_delta": "-0.5",
        "zhang_stage_status": "pass",
    }


def write_run(run_dir: Path, rows: list[dict[str, str]]) -> None:
    run_dir.mkdir(parents=True)
    with (run_dir / "zhang_calibration_best_by_run.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
