from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "dispatch_zhang_pscale2_followup.py"
SUMMARY = (
    REPO_ROOT
    / "docs"
    / "reproduction_goal"
    / "03_zhang_particle_scale"
    / "data"
    / "pscale2_recalibration_size_summary.csv"
)


class ZhangPscale2FollowupDispatchTest(unittest.TestCase):
    def test_builds_targeted_followup_payloads_from_recalibration_summary(self):
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

        payload = json.loads(result.stdout)
        self.assertEqual(payload["mode"], "zhang_pscale2_size_specific_followup")
        self.assertEqual(payload["payload_count"], 3)
        self.assertEqual(payload["total_estimated_run_count"], 10)

        by_size = {
            item["metadata"]["diamond_size_case"]: item
            for item in payload["payloads"]
        }
        self.assertEqual(sorted(by_size), ["C", "D", "E"])

        c_inputs = by_size["C"]["inputs"]
        c_meta = by_size["C"]["metadata"]
        self.assertEqual(c_meta["purpose"], "c_pressure_edge_narrow_emax")
        self.assertEqual(json.loads(c_inputs["e_al_emax_sweep_json"]), ["60.462", "61.462", "62.462", "63.462"])
        self.assertEqual(json.loads(c_inputs["mu_scale_json"]), ["0.654"])
        self.assertEqual(c_meta["estimated_run_count"], 4)

        d_inputs = by_size["D"]["inputs"]
        d_meta = by_size["D"]["metadata"]
        self.assertEqual(d_meta["purpose"], "d_hold_pressure_tune_friction_participation")
        self.assertEqual(json.loads(d_inputs["e_al_emax_sweep_json"]), ["57.173"])
        self.assertEqual(json.loads(d_inputs["mu_scale_json"]), ["0.77", "0.847", "0.963"])
        self.assertEqual(d_meta["estimated_run_count"], 3)

        e_inputs = by_size["E"]["inputs"]
        e_meta = by_size["E"]["metadata"]
        self.assertEqual(e_meta["purpose"], "e_pressure_extension_emax")
        self.assertEqual(json.loads(e_inputs["mu_scale_json"]), ["0.693"])
        self.assertEqual(json.loads(e_inputs["e_al_emax_sweep_json"]), ["75.454", "79.426", "87.368"])
        self.assertEqual(e_meta["estimated_run_count"], 3)

        for item in payload["payloads"]:
            inputs = item["inputs"]
            self.assertEqual(inputs["runtime_profile"], "demo")
            self.assertEqual(inputs["allow_evidence_mismatch"], "true")
            self.assertEqual(json.loads(inputs["particle_count_scale_json"]), ["2"])
            self.assertEqual(json.loads(inputs["dem_seed_json"]), ["2"])


if __name__ == "__main__":
    unittest.main()
