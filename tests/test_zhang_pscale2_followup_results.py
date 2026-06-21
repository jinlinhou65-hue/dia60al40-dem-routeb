from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "analyze_zhang_pscale2_followup_results.py"


class ZhangPscale2FollowupResultsTest(unittest.TestCase):
    def test_summarizes_followup_runs_and_decisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "evidence"
            write_run(
                evidence / "pscale2_followup_run_1",
                [
                    row("C", 63.462, 0.654, 586.0, "pass", "candidate_pass", 0.06, -1.1),
                    row("C", 61.462, 0.654, 527.0, "pass", "candidate_pass", 0.09, -1.1),
                ],
            )
            write_run(
                evidence / "pscale2_followup_run_2",
                [
                    row("D", 57.173, 0.770, 635.0, "review", "needs_participation_increase", -0.1, -0.2),
                    row("D", 57.173, 0.963, 520.0, "review", "needs_d1_decrease", 0.9, 0.7),
                ],
            )
            write_run(
                evidence / "pscale2_followup_run_3",
                [
                    row("E", 87.368, 0.693, 544.0, "pass", "candidate_pass", 0.02, -0.9),
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
                    '["1","2","3"]',
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
            self.assertEqual(payload["row_count"], 5)
            self.assertEqual(payload["pressure_window_candidate_count"], 2)
            self.assertEqual(payload["pass_and_window_candidate_count"], 1)
            by_size = {row["diamond_size_case"]: row for row in payload["size_summary"]}
            self.assertEqual(by_size["C"]["decision"], "candidate_ready_for_seed_recheck")
            self.assertEqual(by_size["D"]["decision"], "hold_pressure_candidate_and_tune_trend")
            self.assertEqual(by_size["E"]["decision"], "extend_pressure_without_losing_trend")
            self.assertTrue((outdir / "pscale2_followup_candidates.csv").exists())
            self.assertTrue((outdir / "pscale2_followup_acceptance.csv").exists())
            self.assertTrue(report.exists())


def row(
    size: str,
    emax: float,
    mu: float,
    p95: float,
    status: str,
    diagnosis: str,
    participation_delta: float,
    d1_delta: float,
) -> dict[str, str]:
    return {
        "artifact": f"artifact-{size}-{emax}-{mu}",
        "diamond_size_case": size,
        "particle_count_scale": "2",
        "particle_count_total": "100",
        "seed_index": "2",
        "e_al_emax_gpa": str(emax),
        "mu_scale": str(mu),
        "p95_mpa": str(p95),
        "status": status,
        "calibration_diagnosis": diagnosis,
        "threshold_factor": "0.05",
        "min_chain_length": "2",
        "participation_delta": str(participation_delta),
        "d1_delta": str(d1_delta),
        "zhang_stage_status": "pass" if status == "pass" else "review",
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
