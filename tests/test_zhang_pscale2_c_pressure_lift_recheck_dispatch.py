from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "dispatch_zhang_pscale2_c_pressure_lift_recheck.py"
SUMMARY = (
    REPO_ROOT
    / "docs"
    / "reproduction_goal"
    / "03_zhang_particle_scale"
    / "data"
    / "pscale2_c_seed_recheck_summary.json"
)


class ZhangPscale2CPressureLiftRecheckDispatchTest(unittest.TestCase):
    def test_derives_one_variable_pressure_lift_from_seed_summary(self):
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
        self.assertEqual(plan["mode"], "zhang_pscale2_c_pressure_lift_recheck")
        self.assertEqual(plan["payload_count"], 1)
        self.assertEqual(plan["total_estimated_run_count"], 5)

        item = plan["payloads"][0]
        inputs = item["inputs"]
        metadata = item["metadata"]
        self.assertEqual(metadata["source_run_id"], "27898770533")
        self.assertEqual(metadata["source_decision"], "c_candidate_not_seed_robust")
        self.assertEqual(metadata["changed_variable"], "e_al_emax_gpa")
        self.assertAlmostEqual(metadata["requested_lift_ratio"], 600 / 524.6190186)
        self.assertEqual(metadata["target_e_al_emax_gpa"], 72.581)
        self.assertEqual(json.loads(inputs["e_al_emax_sweep_json"]), ["72.581"])
        self.assertEqual(json.loads(inputs["mu_scale_json"]), ["0.654"])
        self.assertEqual(json.loads(inputs["dem_seed_json"]), ["0", "1", "2", "3", "4"])
        self.assertEqual(json.loads(inputs["diamond_size_case_json"]), ["C"])
        self.assertEqual(json.loads(inputs["particle_count_scale_json"]), ["2"])

    def test_rejects_a_source_summary_that_does_not_need_pressure_lift(self):
        source = json.loads(SUMMARY.read_text(encoding="utf-8"))
        source["decision"] = "c_candidate_seed_robust"
        with tempfile.TemporaryDirectory() as tmpdir:
            summary_path = Path(tmpdir) / "summary.json"
            summary_path.write_text(json.dumps(source), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--summary", str(summary_path)],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not marked c_candidate_not_seed_robust", result.stderr)


if __name__ == "__main__":
    unittest.main()
