from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DISPATCH_SCRIPT = REPO_ROOT / "scripts" / "dispatch_zhang_pscale2_c_wall_friction_recheck.py"
ANALYZE_SCRIPT = REPO_ROOT / "scripts" / "analyze_zhang_pscale2_c_wall_friction_results.py"
AUDIT = (
    REPO_ROOT
    / "docs"
    / "reproduction_goal"
    / "03_zhang_particle_scale"
    / "data"
    / "zhang_contact_parameter_audit.json"
)
PINNED_COMMIT = "3d5c00f20519e6bb6eb6756f51f1ad36564e649d"


class ZhangPscale2CWallFrictionRecheckTests(unittest.TestCase):
    def test_dispatch_plan_pairs_two_wall_scales_across_five_seeds(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(DISPATCH_SCRIPT),
                "--audit",
                str(AUDIT),
                "--ref",
                "codex/paper-reproduction-demo",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        plan = json.loads(result.stdout)
        self.assertEqual(plan["mode"], "zhang_pscale2_c_wall_friction_recheck")
        self.assertEqual(plan["total_estimated_run_count"], 10)
        item = plan["payloads"][0]
        inputs = item["inputs"]
        metadata = item["metadata"]

        self.assertEqual(metadata["changed_variable"], "mu_wall_scale")
        self.assertEqual(metadata["liggghts_commit"], PINNED_COMMIT)
        self.assertEqual(json.loads(inputs["mu_wall_scale_json"]), ["1", "0.019113"])
        self.assertEqual(json.loads(inputs["mu_scale_json"]), ["0.654"])
        self.assertEqual(json.loads(inputs["e_al_emax_sweep_json"]), ["72.581"])
        self.assertEqual(json.loads(inputs["dem_seed_json"]), ["0", "1", "2", "3", "4"])
        self.assertEqual(inputs["demo_settle_scale"], "1")
        self.assertEqual(inputs["demo_top_velocity_cm_s"], "50")

    def test_analyzer_accepts_a_seed_robust_low_wall_friction_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            run_dir = tmp / "evidence" / "pscale2_c_wall_friction_recheck_run_123"
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

            self.assertEqual(summary["decision"], "c_wall_friction_seed_robust")
            self.assertEqual(summary["baseline"]["pass_and_window_count"], 2)
            self.assertEqual(summary["test"]["pass_and_window_count"], 5)
            self.assertLess(summary["test"]["p95_cv"], summary["baseline"]["p95_cv"])
            self.assertEqual(summary["liggghts_commit"], PINNED_COMMIT)
            self.assertIn("c_wall_friction_seed_robust", (tmp / "report.md").read_text())


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    baseline_pressures = [573.483, 543.867, 607.732, 575.955, 570.019]
    baseline_statuses = ["pass", "pass", "review", "pass", "pass"]
    test_pressures = [585.0, 590.0, 580.0, 600.0, 595.0]
    for wall_scale, wall_mu, pressures, statuses in (
        (1.0, 0.05232, baseline_pressures, baseline_statuses),
        (0.019113, 0.000999992, test_pressures, ["pass"] * 5),
    ):
        for seed, (pressure, status) in enumerate(zip(pressures, statuses, strict=True)):
            rows.append(
                {
                    "artifact": f"wall{wall_scale}-seed{seed}",
                    "diamond_size_case": "C",
                    "particle_count_scale": "2",
                    "seed_index": str(seed),
                    "e_al_emax_gpa": "72.581",
                    "mu_scale": "0.654",
                    "mu_wall_scale": str(wall_scale),
                    "mu_al_wall": str(wall_mu),
                    "mu_diamond_wall": str(wall_mu),
                    "mu_al_tool": "0.05232",
                    "mu_diamond_tool": "0.05232",
                    "liggghts_commit": PINNED_COMMIT,
                    "top_velocity_cm_s": "50",
                    "time_step_seconds": "2e-10",
                    "initial_settle_steps": "20000",
                    "stage_settle_steps": "20000",
                    "final_settle_steps": "50000",
                    "p95_mpa": str(pressure),
                    "status": status,
                    "participation_delta": "0.1",
                    "d1_delta": "-0.1",
                }
            )
    return rows


if __name__ == "__main__":
    unittest.main()
