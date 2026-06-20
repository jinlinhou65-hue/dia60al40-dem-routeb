from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "import_zhang_sweep_artifact.py"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "zhang-sweep-artifact-report.yml"


class ZhangSweepArtifactImportTest(unittest.TestCase):
    def test_imports_ensemble_artifact_into_docs_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "artifact"
            outdir = root / "docs" / "run_123"
            write_artifact(artifact)

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--artifact-dir",
                    str(artifact),
                    "--run-id",
                    "123",
                    "--workflow-url",
                    "https://github.example/runs/123",
                    "--outdir",
                    str(outdir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            metadata = json.loads(result.stdout)
            readme = (outdir / "README.md").read_text(encoding="utf-8")
            self.assertEqual(metadata["run_id"], "123")
            self.assertTrue((outdir / "zhang_calibration_best_by_run.csv").exists())
            self.assertTrue((outdir / "zhang_next_sweep_recommendation.json").exists())
            self.assertIn("Zhang Sweep Artifact Report", readme)
            self.assertIn("artifact-E18-mu07", readme)
            self.assertIn("Pressure Ensemble", readme)

    def test_workflow_can_download_and_commit_report(self):
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("actions: read", text)
        self.assertIn("contents: write", text)
        self.assertIn("workflow_run:", text)
        self.assertIn("WORKFLOW_RUN_ID", text)
        self.assertIn("actions/download-artifact@v4", text)
        self.assertIn("dia60al40-dem-ensemble-summary", text)
        self.assertIn("scripts/import_zhang_sweep_artifact.py", text)
        self.assertIn("docs/zhang_sweep_evidence/run_${DEM_RUN_ID}", text)


def write_artifact(path: Path) -> None:
    path.mkdir(parents=True)
    write_csv(
        path / "ensemble_pressure_summary.csv",
        [
            {
                "n_runs": "2",
                "p95_mean_mpa": "510",
                "p95_min_mpa": "480",
                "p95_max_mpa": "540",
                "p95_range_mpa": "60",
                "p95_cv": "0.08",
            }
        ],
    )
    write_csv(
        path / "zhang_calibration_best_by_run.csv",
        [
            {
                "artifact": "artifact-E18-mu07",
                "e_al_emax_gpa": "18",
                "mu_scale": "0.7",
                "p95_mpa": "480",
                "status": "review",
                "calibration_diagnosis": "needs_participation_increase",
                "threshold_factor": "1.25",
                "min_chain_length": "2",
                "participation_delta": "-0.2",
                "d1_delta": "-0.3",
            },
            {
                "artifact": "artifact-E24-mu13",
                "e_al_emax_gpa": "24.174",
                "mu_scale": "1.3",
                "p95_mpa": "540",
                "status": "pass",
                "calibration_diagnosis": "candidate_pass",
                "threshold_factor": "1",
                "min_chain_length": "2",
                "participation_delta": "0.1",
                "d1_delta": "-0.4",
            },
        ],
    )
    write_csv(
        path / "zhang_calibration_group_summary.csv",
        [
            {
                "group_by": "mu_scale",
                "group_value": "0.7",
                "run_count": "1",
                "pass_run_count": "0",
                "participation_delta_mean": "-0.2",
                "d1_delta_mean": "-0.3",
            }
        ],
    )
    (path / "zhang_next_sweep_recommendation.json").write_text(
        json.dumps(
            {
                "diagnosis": "needs_participation_increase",
                "estimated_run_count": 6,
                "reason": "synthetic next sweep",
                "workflow_dispatch_inputs": {"runtime_profile": "demo"},
            }
        ),
        encoding="utf-8",
    )
    (path / "zhang_next_sweep_recommendation.md").write_text("# Next\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
