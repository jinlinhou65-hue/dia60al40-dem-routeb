from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = REPO_ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from paper_reproduction import aggregate_zhang_calibration, collect_zhang_calibration_rows


class ZhangCalibrationEnsembleTest(unittest.TestCase):
    def test_aggregates_best_candidate_per_dem_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "ensemble_inputs"
            outdir = Path(tmp) / "summary"
            write_artifact(
                root / "artifact-review",
                mu_scale=1.0,
                emax=12.0,
                status="review",
                participation_delta=-0.30,
                d1_delta=-0.40,
            )
            write_artifact(
                root / "artifact-pass",
                mu_scale=1.3,
                emax=14.0,
                status="pass",
                participation_delta=0.20,
                d1_delta=-0.25,
            )

            result = aggregate_zhang_calibration(root, outdir)
            best = read_csv(outdir / "zhang_calibration_best_by_run.csv")
            groups = read_csv(outdir / "zhang_calibration_group_summary.csv")
            report = (outdir / "zhang_calibration_ensemble_report.md").read_text()

            self.assertEqual(result["run_count"], 2)
            self.assertEqual(result["pass_run_count"], 1)
            self.assertEqual(len(best), 2)
            review_row = next(row for row in best if row["artifact"] == "artifact-review")
            self.assertEqual(review_row["calibration_diagnosis"], "needs_participation_increase")
            self.assertTrue(any(row["group_by"] == "mu_scale" and row["group_value"] == "1.3" for row in groups))
            self.assertIn("Runs with pass candidate: `1`", report)

    def test_collect_rows_enriches_parameters(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "ensemble_inputs"
            write_artifact(root / "artifact-review", mu_scale=0.7, emax=10.0)

            rows = collect_zhang_calibration_rows(root)

            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["diamond_size_case"], "C")
            self.assertEqual(rows[0]["seed_index"], 0)
            self.assertEqual(rows[0]["mu_scale"], 0.7)
            self.assertEqual(rows[0]["zhang_stage_status"], "review")

    def test_cli_writes_json_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "ensemble_inputs"
            outdir = Path(tmp) / "summary"
            write_artifact(root / "artifact-review")

            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "aggregate_zhang_calibration.py"),
                    "--root",
                    str(root),
                    "--outdir",
                    str(outdir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(result.stdout)
            self.assertEqual(payload["candidate_count"], 2)
            self.assertTrue((outdir / "zhang_calibration_ensemble_report.md").exists())


def write_artifact(
    artifact_dir: Path,
    *,
    mu_scale: float = 1.0,
    emax: float = 12.0,
    status: str = "review",
    participation_delta: float = -0.25,
    d1_delta: float = -0.30,
) -> None:
    dem_dir = artifact_dir / "DEM"
    calibration = dem_dir / "paper_reproduction" / "zhang_force_chain_calibration"
    calibration.mkdir(parents=True)
    (dem_dir / "model_parameters.csv").write_text(
        "parameter,value\n"
        "diamond_size_case,C\n"
        "DEM_seed_index,0\n"
        f"E_Al_smoothstep_Emax,{emax}\n"
        f"mu_scale,{mu_scale}\n",
        encoding="utf-8",
    )
    (dem_dir / "pressure_density_summary.csv").write_text(
        "target_rho_total,p_target_mpa,reference_mpa,delta_mpa,ratio_to_reference,judgement\n"
        "0.95,297.8374,200,97.8374,1.489187,high\n",
        encoding="utf-8",
    )
    (dem_dir / "paper_reproduction" / "series_acceptance_summary.csv").write_text(
        "paper,status,pass,review,missing,mismatch,check_count\n"
        "Li,pass,1,0,0,0,1\n"
        "Liu,pass,5,0,0,0,5\n"
        "Yuan,pass,3,0,0,0,3\n"
        "Zhang,review,4,2,0,0,6\n",
        encoding="utf-8",
    )
    first = 0.8
    last = first + participation_delta
    d1_first = 0.4
    d1_last = d1_first + d1_delta
    calibration.joinpath("zhang_force_chain_calibration_summary.csv").write_text(
        "chain_coverage,d1_first,d1_last,d1_trend,max_chain_count,min_chain_length,"
        "participation_first,participation_last,participation_trend,rank,stage_count,"
        "status,threshold_factor,trend_score\n"
        f"1.0,{d1_first},{d1_last},decreasing,4,2,{first},{last},decreasing,1,6,{status},0.05,1\n"
        f"0.5,{d1_first},0.8,increasing,1,3,{first},{first + 0.1},increasing,2,6,review,2.0,1\n",
        encoding="utf-8",
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
