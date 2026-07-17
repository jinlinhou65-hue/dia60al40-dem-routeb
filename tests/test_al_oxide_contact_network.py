from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_al_oxide_contact_network import analyze, solve_network  # noqa: E402
from verify_al_oxide_network_results import verify  # noqa: E402


STAGE = ROOT / "docs" / "reproduction_goal" / "04_comsol_electrothermal_field"
PARAMETERS = STAGE / "data" / "source" / "al_oxide_contact_preregistered_parameters.json"
ARCHIVE = STAGE / "evidence" / "true_3d_percolation" / "run_29246532552"
REFERENCE = STAGE / "evidence" / "al_oxide_network_sensitivity"
WORKFLOW = ROOT / ".github" / "workflows" / "al-oxide-network-verification.yml"


class AlOxideContactNetworkTests(unittest.TestCase):
    def test_full_network_combines_parallel_paths(self):
        edges = [
            {"edge_id": 0, "i": 1, "j": 2, "resistance_ohm": 1.0},
            {"edge_id": 1, "i": 2, "j": 4, "resistance_ohm": 1.0},
            {"edge_id": 2, "i": 1, "j": 3, "resistance_ohm": 1.0},
            {"edge_id": 3, "i": 3, "j": 4, "resistance_ohm": 1.0},
        ]
        result = solve_network(edges, {1}, {4}, 0.1)
        self.assertAlmostEqual(result["equivalent_resistance_ohm"], 1.0)
        self.assertAlmostEqual(result["source_current_a_fixed_voltage"], 0.1)
        self.assertLess(result["relative_kcl_residual"], 1e-14)
        self.assertLess(result["relative_power_balance_error"], 1e-14)

    def test_archived_preregistered_sweep_passes_all_gates(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "result"
            summary = analyze(PARAMETERS, ARCHIVE, output)
            self.assertEqual(summary["decision"], "bounded_oxide_network_sensitivity_pass")
            self.assertEqual(summary["scenario_count"], 18)
            self.assertEqual(summary["al_al_edge_count"], 50)
            self.assertFalse(summary["calibrated"])
            self.assertTrue((output / "oxide_network_sensitivity.png").is_file())
            self.assertEqual((output / "edge_results.csv").read_text(encoding="utf-8").count("\n"), 901)

    def test_tampered_archive_is_rejected_before_solution(self):
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp) / "archive"
            shutil.copytree(ARCHIVE, copied)
            particles = copied / "pilot_final_particles.csv"
            particles.write_text(particles.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                analyze(PARAMETERS, copied, Path(temp) / "result")

    def test_reference_verifier_accepts_an_independent_rerun(self):
        with tempfile.TemporaryDirectory() as temp:
            candidate = Path(temp) / "candidate"
            analyze(PARAMETERS, ARCHIVE, candidate)
            result = verify(candidate, REFERENCE)
            self.assertEqual(result["decision"], "oxide_network_reference_match")
            self.assertEqual(result["scenario_count"], 18)

    def test_workflow_is_license_free_and_time_bounded(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("timeout-minutes: 5", text)
        self.assertIn("verify_al_oxide_network_results.py", text)
        self.assertIn("numpy==2.2.6", text)
        self.assertNotIn("COMSOL", text)
        self.assertNotIn("liggghts", text.lower())


if __name__ == "__main__":
    unittest.main()
