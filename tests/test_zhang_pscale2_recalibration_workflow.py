from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "dispatch_zhang_pscale2_recalibration.py"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "zhang-pscale2-recalibration.yml"


class ZhangPscale2RecalibrationWorkflowTest(unittest.TestCase):
    def test_dispatch_script_builds_pressure_first_recalibration_payloads(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--ref",
                "codex/paper-reproduction-demo",
                "--target-pressure-mpa",
                "600",
                "--e-multipliers-json",
                "[0.95,1.0,1.05]",
                "--max-total-runs",
                "9",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        payload = json.loads(result.stdout)
        self.assertFalse(payload["dispatch"])
        self.assertEqual(payload["mode"], "zhang_pscale2_pressure_recalibration")
        self.assertEqual(payload["payload_count"], 3)
        self.assertEqual(payload["total_estimated_run_count"], 9)
        sizes = [item["metadata"]["diamond_size_case"] for item in payload["payloads"]]
        self.assertEqual(sizes, ["C", "D", "E"])
        by_size = {item["metadata"]["diamond_size_case"]: item for item in payload["payloads"]}
        self.assertEqual(json.loads(by_size["C"]["inputs"]["e_al_emax_sweep_json"]), ["61.962", "65.223", "68.484"])
        self.assertEqual(json.loads(by_size["D"]["inputs"]["e_al_emax_sweep_json"]), ["51.728", "54.451", "57.173"])
        self.assertEqual(json.loads(by_size["E"]["inputs"]["e_al_emax_sweep_json"]), ["57.506", "60.533", "63.559"])
        for item in payload["payloads"]:
            inputs = item["inputs"]
            self.assertEqual(inputs["runtime_profile"], "demo")
            self.assertEqual(inputs["allow_evidence_mismatch"], "true")
            self.assertEqual(json.loads(inputs["particle_count_scale_json"]), ["2"])
            self.assertEqual(json.loads(inputs["dem_seed_json"]), ["2"])
            self.assertEqual(len(json.loads(inputs["mu_scale_json"])), 1)

    def test_workflow_dispatches_nine_job_recalibration(self):
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("actions: write", text)
        self.assertIn("dispatch_zhang_pscale2_recalibration.py", text)
        self.assertIn("--dispatch", text)
        self.assertIn("expected 9 DEM jobs", text)
        self.assertIn("particle_count_scale_json", text)
        self.assertIn("e_al_emax_sweep_json", text)


if __name__ == "__main__":
    unittest.main()
