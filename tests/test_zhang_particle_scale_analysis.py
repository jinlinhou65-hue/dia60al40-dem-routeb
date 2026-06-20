from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "analyze_zhang_particle_scale.py"


class ZhangParticleScaleAnalysisTest(unittest.TestCase):
    def test_compares_baseline_and_refined_particle_scale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline.csv"
            refined = root / "refined.csv"
            refined_best = root / "refined_best.csv"
            outdir = root / "data"
            figure_dir = root / "figures"
            write_csv(
                baseline,
                [
                    size_row("C", 44.772, 0.654, 634.203315, "pass", "run1", "artifact-C-1x"),
                    size_row("D", 37.517, 0.770, 620.578088, "pass", "run2", "artifact-D-1x"),
                ],
            )
            write_csv(
                refined,
                [
                    size_row("C", 44.772, 0.654, 411.86608, "pass", "run3", "artifact-C-2x"),
                    size_row("D", 37.517, 0.770, 413.405454, "review", "run4", "artifact-D-2x"),
                ],
            )
            write_csv(
                refined_best,
                [
                    best_row("C", 411.86608, "pass", "candidate_pass", 0.1, -1.0, 151),
                    best_row("D", 413.405454, "review", "needs_participation_increase", -0.2, -0.8, 92),
                ],
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--baseline-summary",
                    str(baseline),
                    "--refined-summary",
                    str(refined),
                    "--refined-best",
                    str(refined_best),
                    "--outdir",
                    str(outdir),
                    "--figure-dir",
                    str(figure_dir),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

            payload = json.loads(result.stdout)
            self.assertFalse(payload["all_2x_pressure_in_window"])
            self.assertEqual(payload["recommended_next_step"].startswith("Do not launch 4x yet"), True)
            comparison = read_csv(outdir / "1x_vs_2x_comparison.csv")
            self.assertEqual(len(comparison), 2)
            c_row = next(row for row in comparison if row["diamond_size_case"] == "C")
            self.assertEqual(c_row["refined_status"], "pass")
            self.assertEqual(c_row["refined_pressure_in_window"], "False")
            acceptance = read_csv(outdir / "zhang_particle_scale_acceptance.csv")
            self.assertEqual(
                {row["diamond_size_case"]: row["decision"] for row in acceptance},
                {
                    "C": "rerun_with_higher_endpoint_pressure",
                    "D": "recalibrate_before_4x",
                },
            )
            self.assertTrue((outdir / "summary.json").exists())
            self.assertTrue((root / "report.md").exists())


def size_row(
    size: str,
    emax: float,
    mu: float,
    p95: float,
    status: str,
    run_id: str,
    artifact: str,
) -> dict[str, str]:
    return {
        "diamond_size_case": size,
        "best_e_al_emax_gpa": str(emax),
        "best_mu_scale": str(mu),
        "best_p95_mpa": str(p95),
        "best_status": status,
        "best_source_run_id": run_id,
        "best_artifact": artifact,
    }


def best_row(
    size: str,
    p95: float,
    status: str,
    diagnosis: str,
    participation_delta: float,
    d1_delta: float,
    count: int,
) -> dict[str, str]:
    return {
        "diamond_size_case": size,
        "p95_mpa": str(p95),
        "status": status,
        "calibration_diagnosis": diagnosis,
        "participation_delta": str(participation_delta),
        "d1_delta": str(d1_delta),
        "particle_count_total": str(count),
    }


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
