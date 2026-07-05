from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "dispatch_zhang_pscale2_c_loading_rate_recheck.py"
SUMMARY = (
    REPO_ROOT
    / "docs"
    / "reproduction_goal"
    / "03_zhang_particle_scale"
    / "data"
    / "pscale2_c_settle_midpoint_summary.json"
)


class ZhangPscale2CLoadingRateRecheckDispatchTest(unittest.TestCase):
    def test_builds_25cm_s_recheck_with_settle1_and_physics_held(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--summary",
                str(SUMMARY),
                "--ref",
                "codex/paper-reproduction-demo",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        plan = json.loads(result.stdout)
        self.assertEqual(plan["mode"], "zhang_pscale2_c_loading_rate_recheck")
        self.assertEqual(plan["total_estimated_run_count"], 5)
        item = plan["payloads"][0]
        inputs = item["inputs"]
        metadata = item["metadata"]
        self.assertEqual(metadata["source_run_id"], "28709925303")
        self.assertEqual(metadata["changed_variable"], "demo_top_velocity_cm_s")
        self.assertEqual(metadata["baseline_velocity_cm_s"], 50.0)
        self.assertEqual(metadata["target_velocity_cm_s"], 25.0)
        self.assertEqual(metadata["settle_steps"], {
            "initial": 20000,
            "stage": 20000,
            "final": 50000,
        })
        self.assertEqual(inputs["demo_settle_scale"], "1")
        self.assertEqual(inputs["demo_top_velocity_cm_s"], "25")
        self.assertEqual(json.loads(inputs["e_al_emax_sweep_json"]), ["72.581"])
        self.assertEqual(json.loads(inputs["mu_scale_json"]), ["0.654"])
        self.assertEqual(json.loads(inputs["dem_seed_json"]), ["0", "1", "2", "3", "4"])

        workflow = (REPO_ROOT / ".github" / "workflows" / "dia60al40-dem.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("demo_top_velocity_cm_s:", workflow)
        self.assertIn("DEMO_TOP_VELOCITY_CM_S", workflow)
        self.assertIn('runtime_args+=(--top-vel-cm-s "$TOP_VELOCITY_CM_S")', workflow)
        self.assertIn("top_velocity_cm_s", workflow)

    def test_rejects_velocity_that_does_not_reduce_the_baseline(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--summary",
                str(SUMMARY),
                "--target-velocity-cm-s",
                "50",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("target velocity must be in [5, 50)", result.stderr)


if __name__ == "__main__":
    unittest.main()
