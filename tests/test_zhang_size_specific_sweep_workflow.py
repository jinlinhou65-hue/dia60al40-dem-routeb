from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "dispatch_zhang_size_specific_sweeps.py"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "zhang-size-specific-sweep.yml"
RECOMMENDATION = (
    REPO_ROOT
    / "docs"
    / "zhang_sweep_evidence"
    / "run_27867380830"
    / "zhang_next_sweep_recommendation.json"
)


class ZhangSizeSpecificSweepWorkflowTest(unittest.TestCase):
    def test_dispatch_script_builds_three_size_specific_payloads(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--recommendation",
                str(RECOMMENDATION),
                "--ref",
                "codex/paper-reproduction-demo",
                "--max-total-runs",
                "36",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        payload = json.loads(result.stdout)
        self.assertFalse(payload["dispatch"])
        self.assertEqual(payload["mode"], "size_specific_calibration")
        self.assertEqual(payload["payload_count"], 3)
        self.assertEqual(payload["total_estimated_run_count"], 36)
        sizes = [item["metadata"]["diamond_size_case"] for item in payload["payloads"]]
        self.assertEqual(sizes, ["C", "D", "E"])
        for item in payload["payloads"]:
            inputs = item["inputs"]
            size = item["metadata"]["diamond_size_case"]
            self.assertEqual(inputs["runtime_profile"], "demo")
            self.assertEqual(inputs["allow_evidence_mismatch"], "true")
            self.assertEqual(json.loads(inputs["diamond_size_case_json"]), [size])

    def test_workflow_dispatches_existing_dem_workflow_from_plan(self):
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("actions: write", text)
        self.assertIn("dispatch_zhang_size_specific_sweeps.py", text)
        self.assertIn("--dispatch", text)
        self.assertIn("expected 3 size-specific dispatch payloads", text)
        self.assertIn("expected 36 estimated DEM jobs", text)


if __name__ == "__main__":
    unittest.main()
