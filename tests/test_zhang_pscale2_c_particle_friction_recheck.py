from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DISPATCH_SCRIPT = REPO_ROOT / "scripts" / "dispatch_zhang_pscale2_c_particle_friction_recheck.py"
ANALYZE_SCRIPT = REPO_ROOT / "scripts" / "analyze_zhang_pscale2_c_particle_friction_results.py"
PLAN = (
    REPO_ROOT
    / "docs"
    / "reproduction_goal"
    / "03_zhang_particle_scale"
    / "data"
    / "pscale2_c_particle_friction_plan.json"
)
PREVIOUS = PLAN.with_name("pscale2_c_wall_friction_summary.json")
PINNED_COMMIT = "3d5c00f20519e6bb6eb6756f51f1ad36564e649d"


class ZhangPscale2CParticleFrictionRecheckTests(unittest.TestCase):
    def test_dispatch_reuses_baseline_and_runs_only_five_test_seeds(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(DISPATCH_SCRIPT),
                "--plan",
                str(PLAN),
                "--previous-summary",
                str(PREVIOUS),
                "--ref",
                "codex/paper-reproduction-demo",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        plan = json.loads(result.stdout)
        self.assertEqual(plan["mode"], "zhang_pscale2_c_particle_friction_recheck")
        self.assertEqual(plan["total_estimated_run_count"], 5)
        item = plan["payloads"][0]
        inputs = item["inputs"]
        metadata = item["metadata"]

        self.assertEqual(metadata["baseline_run_id"], "28747847286")
        self.assertEqual(metadata["changed_variable"], "interparticle_friction_coefficients")
        self.assertEqual(metadata["liggghts_commit"], PINNED_COMMIT)
        for field in ("mu_al_al", "mu_al_diamond", "mu_diamond_diamond"):
            self.assertAlmostEqual(float(inputs[field]) * 0.654, 0.001, places=9)
        self.assertEqual(inputs["mu_al_tool"], "0.08")
        self.assertEqual(inputs["mu_al_wall"], "0.08")
        self.assertEqual(json.loads(inputs["mu_wall_scale_json"]), ["1"])
        self.assertEqual(json.loads(inputs["dem_seed_json"]), ["0", "1", "2", "3", "4"])

    def test_analyzer_accepts_a_seed_robust_particle_friction_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            evidence = tmp / "evidence"
            baseline_dir = evidence / "pscale2_c_wall_friction_recheck_run_28747847286"
            test_dir = evidence / "pscale2_c_particle_friction_recheck_run_456"
            baseline_dir.mkdir(parents=True)
            test_dir.mkdir(parents=True)
            write_rows(baseline_dir / "zhang_calibration_best_by_run.csv", build_baseline_rows())
            write_rows(test_dir / "zhang_calibration_best_by_run.csv", build_test_rows())

            result = subprocess.run(
                [
                    sys.executable,
                    str(ANALYZE_SCRIPT),
                    "--evidence-root",
                    str(evidence),
                    "--test-run-id",
                    "456",
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

            self.assertEqual(summary["decision"], "c_particle_friction_seed_robust")
            self.assertEqual(summary["baseline"]["pass_and_window_count"], 2)
            self.assertEqual(summary["test"]["pass_and_window_count"], 5)
            self.assertLess(summary["test"]["p95_cv"], summary["baseline"]["p95_cv"])
            self.assertIn("c_particle_friction_seed_robust", (tmp / "report.md").read_text())


def build_baseline_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    baseline_pressures = [573.483, 543.867, 607.732, 575.955, 570.019]
    baseline_statuses = ["review", "pass", "pass", "pass", "pass"]
    for wall_scale, wall_mu, pressures, statuses in (
        (1.0, 0.05232, baseline_pressures, baseline_statuses),
        (0.019113, 0.000999992, [523.0, 567.1, 608.2, 577.4, 549.9], ["pass"] * 5),
    ):
        for seed, (pressure, status) in enumerate(zip(pressures, statuses, strict=True)):
            rows.append(common_row(seed, pressure, status, wall_scale, wall_mu))
    return rows


def build_test_rows() -> list[dict[str, str]]:
    rows = []
    for seed, pressure in enumerate([585.0, 590.0, 580.0, 600.0, 595.0]):
        row = common_row(seed, pressure, "pass", 1.0, 0.05232)
        row.update(
            {
                "mu_al_al": "0.001",
                "mu_al_diamond": "0.001",
                "mu_diamond_diamond": "0.001",
            }
        )
        rows.append(row)
    return rows


def common_row(
    seed: int, pressure: float, status: str, wall_scale: float, wall_mu: float
) -> dict[str, str]:
    return {
        "artifact": f"run-seed{seed}",
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


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
