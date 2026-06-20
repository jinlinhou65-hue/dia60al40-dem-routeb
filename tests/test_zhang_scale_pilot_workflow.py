from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "dispatch_zhang_scale_pilot.py"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "zhang-scale-pilot.yml"
SUMMARY = (
    REPO_ROOT
    / "docs"
    / "zhang_sweep_evidence"
    / "size_specific_27874059503_27874061902_27874064063"
    / "summary.json"
)


class ZhangScalePilotWorkflowTest(unittest.TestCase):
    def test_dispatch_script_builds_three_scale_pilot_payloads(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--summary",
                str(SUMMARY),
                "--ref",
                "codex/paper-reproduction-demo",
                "--particle-count-scale",
                "2",
                "--max-total-runs",
                "3",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        payload = json.loads(result.stdout)
        self.assertFalse(payload["dispatch"])
        self.assertEqual(payload["mode"], "zhang_particle_count_scale_pilot")
        self.assertEqual(payload["payload_count"], 3)
        self.assertEqual(payload["total_estimated_run_count"], 3)
        self.assertEqual(payload["particle_count_scale"], 2)
        sizes = [item["metadata"]["diamond_size_case"] for item in payload["payloads"]]
        self.assertEqual(sizes, ["C", "D", "E"])
        for item in payload["payloads"]:
            inputs = item["inputs"]
            self.assertEqual(inputs["runtime_profile"], "demo")
            self.assertEqual(inputs["allow_evidence_mismatch"], "true")
            self.assertEqual(json.loads(inputs["particle_count_scale_json"]), ["2"])
            self.assertEqual(json.loads(inputs["diamond_size_case_json"]), [item["metadata"]["diamond_size_case"]])
            self.assertEqual(json.loads(inputs["dem_seed_json"]), ["2"])

    def test_workflow_dispatches_scale_pilot_from_imported_summary(self):
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("actions: write", text)
        self.assertIn("dispatch_zhang_scale_pilot.py", text)
        self.assertIn("--dispatch", text)
        self.assertIn("expected 3 scale-pilot payloads", text)
        self.assertIn("expected 3 DEM jobs", text)
        self.assertIn("particle_count_scale", text)


if __name__ == "__main__":
    unittest.main()
