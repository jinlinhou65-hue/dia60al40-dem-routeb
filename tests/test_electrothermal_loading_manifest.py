from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_electrothermal_loading_manifest import (  # noqa: E402
    EXPECTED_REVIEW_CASES,
    sha256_file,
    validate_decision_snapshot,
    verify_records,
)


class ElectrothermalLoadingManifestTest(unittest.TestCase):
    def test_record_verifier_detects_content_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "evidence.txt"
            path.write_text("original", encoding="utf-8")
            manifest = {
                "records": [
                    {
                        "path": "evidence.txt",
                        "bytes": path.stat().st_size,
                        "sha256": sha256_file(path),
                    }
                ]
            }
            self.assertEqual(verify_records(manifest, root), [])
            path.write_text("changed", encoding="utf-8")
            self.assertIn("sha256 mismatch: evidence.txt", verify_records(manifest, root))

    def test_decision_contract_preserves_review_and_refinement_pass(self) -> None:
        snapshot = {
            "open_six_case_decision": "loading_mode_fvm_pass",
            "archived_comsol_comparison_decision": "review",
            "archived_comsol_failed_case_ids": list(EXPECTED_REVIEW_CASES),
            "archived_comsol_global_gates": {
                "all_case_gates": False,
                "fixed_mesh_element_gate": True,
                "fixed_voltage_power_trend_gate": True,
            },
            "refinement_decision": "fvm_refinement_pass",
            "refinement_original_loading_decision": "review",
            "refinement_gates": {"factor3_comsol_power_gate": True},
        }
        validate_decision_snapshot(snapshot)
        snapshot["archived_comsol_comparison_decision"] = "loading_mode_comsol_pass"
        with self.assertRaisesRegex(ValueError, "preserve review"):
            validate_decision_snapshot(snapshot)


if __name__ == "__main__":
    unittest.main()
