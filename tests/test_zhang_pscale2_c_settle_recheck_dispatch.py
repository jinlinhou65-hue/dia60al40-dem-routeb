from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "dispatch_zhang_pscale2_c_settle_recheck.py"
SUMMARY = (
    REPO_ROOT
    / "docs"
    / "reproduction_goal"
    / "03_zhang_particle_scale"
    / "data"
    / "pscale2_c_pressure_lift_summary.json"
)


class ZhangPscale2CSettleRecheckDispatchTest(unittest.TestCase):
    def test_builds_4x_settle_recheck_with_physics_held(self):
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
        self.assertEqual(plan["mode"], "zhang_pscale2_c_settle_recheck")
        self.assertEqual(plan["total_estimated_run_count"], 5)
        item = plan["payloads"][0]
        inputs = item["inputs"]
        metadata = item["metadata"]
        self.assertEqual(metadata["source_run_id"], "28709925303")
        self.assertEqual(metadata["changed_variable"], "demo_settle_scale")
        self.assertEqual(metadata["baseline_settle_steps"], {
            "initial": 20000,
            "stage": 20000,
            "final": 50000,
        })
        self.assertEqual(metadata["target_settle_steps"], {
            "initial": 80000,
            "stage": 80000,
            "final": 200000,
        })
        self.assertEqual(inputs["demo_settle_scale"], "4")
        self.assertEqual(json.loads(inputs["e_al_emax_sweep_json"]), ["72.581"])
        self.assertEqual(json.loads(inputs["mu_scale_json"]), ["0.654"])
        self.assertEqual(json.loads(inputs["dem_seed_json"]), ["0", "1", "2", "3", "4"])

        workflow = (REPO_ROOT / ".github" / "workflows" / "dia60al40-dem.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("demo_settle_scale:", workflow)
        self.assertIn("INITIAL_SETTLE_STEPS", workflow)
        self.assertIn("FINAL_SETTLE_STEPS", workflow)
        self.assertIn("\n          PY\n          if [", workflow)
        self.assertNotIn("\n            PY\n", workflow)


if __name__ == "__main__":
    unittest.main()
