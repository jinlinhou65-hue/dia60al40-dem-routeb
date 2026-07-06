from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DISPATCH_SCRIPT = REPO_ROOT / "scripts" / "dispatch_zhang_pscale2_e_pressure_lift_recheck.py"
ANALYZE_SCRIPT = REPO_ROOT / "scripts" / "analyze_zhang_pscale2_e_pressure_lift_results.py"
PLAN = (
    REPO_ROOT
    / "docs"
    / "reproduction_goal"
    / "03_zhang_particle_scale"
    / "data"
    / "pscale2_e_pressure_lift_plan.json"
)
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "zhang-pscale2-e-pressure-lift-recheck.yml"
PINNED_COMMIT = "3d5c00f20519e6bb6eb6756f51f1ad36564e649d"


class ZhangPscale2EPressureLiftRecheckTests(unittest.TestCase):
    def test_dispatch_plan_changes_only_emax_for_five_seeds(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(DISPATCH_SCRIPT),
                "--plan",
                str(PLAN),
                "--ref",
                "codex/paper-reproduction-demo",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        plan = json.loads(result.stdout)
        self.assertEqual(plan["mode"], "zhang_pscale2_e_pressure_lift_recheck")
        self.assertEqual(plan["total_estimated_run_count"], 5)
        item = plan["payloads"][0]
        inputs = item["inputs"]
        metadata = item["metadata"]

        self.assertEqual(metadata["changed_variable"], "e_al_emax_gpa")
        self.assertEqual(metadata["source_run_id"], "27883035658")
        self.assertEqual(metadata["liggghts_commit"], PINNED_COMMIT)
        self.assertEqual(json.loads(inputs["e_al_emax_sweep_json"]), ["96.417"])
        self.assertEqual(json.loads(inputs["mu_scale_json"]), ["0.693"])
        self.assertEqual(json.loads(inputs["mu_wall_scale_json"]), ["1"])
        self.assertEqual(json.loads(inputs["diamond_size_case_json"]), ["E"])
        self.assertEqual(json.loads(inputs["particle_count_scale_json"]), ["2"])
        self.assertEqual(json.loads(inputs["dem_seed_json"]), ["0", "1", "2", "3", "4"])

    def test_analyzer_accepts_a_seed_robust_e_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            run_dir = tmp / "evidence" / "pscale2_e_pressure_lift_recheck_run_123"
            run_dir.mkdir(parents=True)
            rows = build_rows()
            with (run_dir / "zhang_calibration_best_by_run.csv").open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)

            result = subprocess.run(
                [
                    sys.executable,
                    str(ANALYZE_SCRIPT),
                    "--evidence-root",
                    str(tmp / "evidence"),
                    "--run-id",
                    "123",
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

            self.assertEqual(summary["decision"], "e_pressure_lift_seed_robust")
            self.assertEqual(summary["test"]["pass_and_window_count"], 5)
            self.assertGreater(summary["seed2_p95_delta_mpa"], 0)
            self.assertIn("e_pressure_lift_seed_robust", (tmp / "report.md").read_text())

    def test_workflow_has_a_single_five_seed_dispatch(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("--max-total-runs 5", workflow)
        self.assertIn('["96.417"]', workflow)
        self.assertIn('!= ["E"]', workflow)
        self.assertIn('!= ["0", "1", "2", "3", "4"]', workflow)


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for seed, pressure in enumerate([585.0, 590.0, 600.0, 610.0, 595.0]):
        rows.append(
            {
                "artifact": f"e-seed{seed}",
                "diamond_size_case": "E",
                "particle_count_scale": "2",
                "seed_index": str(seed),
                "e_al_emax_gpa": "96.417",
                "mu_scale": "0.693",
                "mu_wall_scale": "1",
                "mu_al_al": "0.2079",
                "mu_al_diamond": "0.2079",
                "mu_diamond_diamond": "0.0693",
                "mu_al_wall": "0.05544",
                "mu_diamond_wall": "0.05544",
                "mu_al_tool": "0.05544",
                "mu_diamond_tool": "0.05544",
                "liggghts_commit": PINNED_COMMIT,
                "top_velocity_cm_s": "50",
                "time_step_seconds": "2e-10",
                "initial_settle_steps": "20000",
                "stage_settle_steps": "20000",
                "final_settle_steps": "50000",
                "p95_mpa": str(pressure),
                "status": "pass",
                "participation_delta": "0.1",
                "d1_delta": "-0.1",
            }
        )
    return rows


if __name__ == "__main__":
    unittest.main()
