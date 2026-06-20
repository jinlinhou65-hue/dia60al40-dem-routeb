from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "zhang-recommended-sweep.yml"


class ZhangRecommendedSweepWorkflowTest(unittest.TestCase):
    def test_workflow_dispatches_existing_dem_workflow(self):
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("actions: write", text)
        self.assertIn("dia60al40-dem.yml/dispatches", text)
        self.assertIn("runtime_profile", text)
        self.assertIn('"allow_evidence_mismatch": "true"', text)
        self.assertIn("expected the recommended robustness sweep to dispatch 9 DEM runs", text)

    def test_default_matrix_matches_current_recommendation(self):
        text = WORKFLOW.read_text(encoding="utf-8")

        emax = extract_default(text, "e_al_emax_sweep_json")
        mu = extract_default(text, "mu_scale_json")
        seeds = extract_default(text, "dem_seed_json")
        sizes = extract_default(text, "diamond_size_case_json")
        runtime = extract_default(text, "runtime_profile")

        self.assertEqual(emax, ["41.686"])
        self.assertEqual(mu, ["0.77"])
        self.assertEqual(seeds, ["0", "1", "2"])
        self.assertEqual(sizes, ["C", "D", "E"])
        self.assertEqual(runtime, "demo")
        self.assertEqual(len(emax) * len(mu) * len(seeds) * len(sizes), 9)


def extract_default(text: str, input_name: str):
    pattern = re.compile(
        rf"{re.escape(input_name)}:\n(?:        .+\n)+?        default: '([^']+)'",
        re.MULTILINE,
    )
    match = pattern.search(text)
    if not match:
        raise AssertionError(f"missing default for {input_name}")
    value = match.group(1)
    if value.startswith("["):
        return json.loads(value)
    return value


if __name__ == "__main__":
    unittest.main()
