from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "summarize_zhang_size_specific_imports.py"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "zhang-size-specific-artifact-report.yml"


class ZhangSizeSpecificArtifactImportTest(unittest.TestCase):
    def test_summarizes_imported_size_specific_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs_root = Path(tmp) / "zhang_sweep_evidence"
            write_imported_run(
                docs_root / "run_100",
                run_id="100",
                size="C",
                rows=[
                    row("artifact-C-a", "C", 44.772, 0.654, 600.0, "pass", 0.2, -0.4),
                    row("artifact-C-b", "C", 41.686, 0.885, 540.0, "review", -0.1, -0.3),
                ],
            )
            write_imported_run(
                docs_root / "run_101",
                run_id="101",
                size="D",
                rows=[
                    row("artifact-D-a", "D", 32.737, 0.539, 620.0, "pass", 0.3, -0.5),
                ],
            )
            write_imported_run(
                docs_root / "run_102",
                run_id="102",
                size="E",
                rows=[
                    row("artifact-E-a", "E", 36.471, 0.693, 700.0, "pass", 0.1, -0.2),
                ],
            )
            outdir = docs_root / "combined"

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--docs-root",
                    str(docs_root),
                    "--run-ids-json",
                    '["100","101","102"]',
                    "--outdir",
                    str(outdir),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

            payload = json.loads(result.stdout)
            self.assertEqual(payload["row_count"], 4)
            self.assertEqual(payload["status_pass_count"], 3)
            self.assertEqual(payload["pressure_window_count"], 2)
            self.assertEqual(payload["passing_window_count"], 2)
            self.assertTrue((outdir / "combined_best_by_run.csv").exists())
            self.assertTrue((outdir / "combined_size_summary.csv").exists())
            readme = (outdir / "README.md").read_text(encoding="utf-8")
            self.assertIn("Zhang Size-Specific Sweep Summary", readme)
            self.assertIn("artifact-C-a", readme)

    def test_workflow_downloads_three_artifacts_and_commits_summary(self):
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("gh run download", text)
        self.assertIn("dia60al40-dem-ensemble-summary", text)
        self.assertIn("scripts/import_zhang_sweep_artifact.py", text)
        self.assertIn("scripts/summarize_zhang_size_specific_imports.py", text)
        self.assertIn("expected exactly 3 DEM run ids", text)
        self.assertIn("docs/zhang_sweep_evidence/${slug}", text)
        self.assertIn("docs(zhang): import size-specific sweep artifacts", text)


def row(
    artifact: str,
    size: str,
    emax: float,
    mu: float,
    p95: float,
    status: str,
    participation_delta: float,
    d1_delta: float,
) -> dict[str, str]:
    return {
        "artifact": artifact,
        "diamond_size_case": size,
        "seed_index": "0",
        "e_al_emax_gpa": str(emax),
        "mu_scale": str(mu),
        "p95_mpa": str(p95),
        "status": status,
        "calibration_diagnosis": "candidate_pass" if status == "pass" else "review",
        "threshold_factor": "0.1",
        "min_chain_length": "2",
        "participation_delta": str(participation_delta),
        "d1_delta": str(d1_delta),
    }


def write_imported_run(
    run_dir: Path,
    *,
    run_id: str,
    size: str,
    rows: list[dict[str, str]],
) -> None:
    run_dir.mkdir(parents=True)
    write_csv(run_dir / "zhang_calibration_best_by_run.csv", rows)
    write_csv(
        run_dir / "zhang_calibration_group_summary.csv",
        [
            {
                "group_by": "diamond_size_case",
                "group_value": size,
                "run_count": str(len(rows)),
                "pass_run_count": str(sum(1 for item in rows if item["status"] == "pass")),
                "participation_delta_mean": "0.1",
                "d1_delta_mean": "-0.2",
            }
        ],
    )
    (run_dir / "import_metadata.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "workflow_url": f"https://github.example/runs/{run_id}",
            }
        ),
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
