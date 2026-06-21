from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "dispatch_zhang_pscale2_c_seed_recheck.py"
SUMMARY = (
    REPO_ROOT
    / "docs"
    / "reproduction_goal"
    / "03_zhang_particle_scale"
    / "data"
    / "pscale2_followup_size_summary.csv"
)


class ZhangPscale2CSeedRecheckDispatchTest(unittest.TestCase):
    def test_builds_c_seed_recheck_payload_from_followup_summary(self):
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
        self.assertEqual(payload["mode"], "zhang_pscale2_c_seed_recheck")
        self.assertEqual(payload["payload_count"], 1)
        self.assertEqual(payload["total_estimated_run_count"], 5)

        item = payload["payloads"][0]
        inputs = item["inputs"]
        metadata = item["metadata"]
        self.assertEqual(metadata["diamond_size_case"], "C")
        self.assertEqual(metadata["purpose"], "c_seed_robustness_recheck")
        self.assertEqual(metadata["source_decision"], "candidate_ready_for_seed_recheck")
        self.assertEqual(metadata["source_best_p95_mpa"], 586.646265)
        self.assertEqual(json.loads(inputs["diamond_size_case_json"]), ["C"])
        self.assertEqual(json.loads(inputs["particle_count_scale_json"]), ["2"])
        self.assertEqual(json.loads(inputs["e_al_emax_sweep_json"]), ["63.462"])
        self.assertEqual(json.loads(inputs["mu_scale_json"]), ["0.654"])
        self.assertEqual(json.loads(inputs["dem_seed_json"]), ["0", "1", "2", "3", "4"])
        self.assertEqual(inputs["runtime_profile"], "demo")
        self.assertEqual(inputs["allow_evidence_mismatch"], "true")


if __name__ == "__main__":
    unittest.main()
