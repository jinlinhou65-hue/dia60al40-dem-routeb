from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_dem_3d_readiness import audit, write_report  # noqa: E402


class Dem3dReadinessTest(unittest.TestCase):
    def test_current_stage_is_strict_quasi_2d_and_requires_pilot(self) -> None:
        stage = ROOT / "docs" / "reproduction_goal" / "04_comsol_electrothermal_field"
        result = audit(
            ROOT / "liggghts" / "in.dia60al40_dem_staged.liggghts",
            stage / "data" / "source" / "dem_fem_handoff_stage5_rho095.csv",
            stage / "data" / "source" / "stage5_rho095_direct_contacts.csv",
        )
        self.assertEqual(result["decision"], "true_3d_pilot_required")
        self.assertEqual(result["deck_classification"], "strict_quasi_2d")
        self.assertFalse(result["archived_stage04_source"]["has_3d_schema"])
        self.assertTrue(result["raw_output_capability"]["particle_dump_requests_z"])

    def test_report_records_evidence_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "report.md"
            result = {
                "decision": "true_3d_pilot_required",
                "raw_output_capability": {
                    "particle_dump_requests_z": True,
                    "contact_dump_requests_13_components": True,
                },
                "dimensional_constraints": {
                    "zlock_setforce_present": True,
                    "set_all_z_zero_count": 3,
                },
                "archived_stage04_source": {
                    "has_3d_schema": False,
                    "has_nonzero_depth_evidence": False,
                },
                "interpretation": "No 3D claim.",
                "next_action": "Run a true-3D pilot.",
            }
            write_report(path, result)
            text = path.read_text(encoding="utf-8")
            self.assertIn("true_3d_pilot_required", text)
            self.assertIn("No 3D claim", text)


if __name__ == "__main__":
    unittest.main()
