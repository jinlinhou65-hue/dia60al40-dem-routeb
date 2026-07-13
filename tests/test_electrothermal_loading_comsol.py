from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_electrothermal_loading_comsol import (  # noqa: E402
    evaluate_global_gates,
    field_hotspots,
)


def row(mode: str, multiplier: float, power: float, rise: float) -> dict[str, object]:
    return {
        "loading_mode": mode,
        "al_al_resistance_multiplier": multiplier,
        "comsol_power_w_per_m_depth": power,
        "comsol_temperature_rise_k": rise,
        "element_count": 3316,
        "case_gate": True,
        "comsol_joule_hotspot_x_um": multiplier,
        "comsol_joule_hotspot_y_um": 1.0,
        "comsol_temperature_hotspot_x_um": multiplier,
        "comsol_temperature_hotspot_y_um": 2.0,
    }


class ElectrothermalLoadingComsolTest(unittest.TestCase):
    def test_global_gates_require_fixed_mesh_opposite_trends_and_stable_hotspots(self) -> None:
        rows = [
            row("fixed_voltage", 1.0, 100.0, 1.0),
            row("fixed_voltage", 10.0, 10.0, 0.1),
            row("fixed_voltage", 100.0, 1.0, 0.01),
            row("fixed_current", 1.0, 1.0, 0.01),
            row("fixed_current", 10.0, 10.0, 0.1),
            row("fixed_current", 100.0, 100.0, 1.0),
        ]
        self.assertTrue(all(evaluate_global_gates(rows, 3316, 1.0e-6).values()))
        rows[-1]["element_count"] = 3315
        self.assertFalse(evaluate_global_gates(rows, 3316, 1.0e-6)["fixed_mesh_element_gate"])

    def test_field_hotspots_reads_comsol_export_contract(self) -> None:
        content = """% x,y,V,T,J,Q,sigma,k
0,0,0,293.15,1,2,3,4
1,2,0.1,294,5,6,7,8
"""
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "comsol_fields.csv"
            path.write_text(content, encoding="utf-8")
            metrics = field_hotspots(path)
        self.assertEqual(metrics["comsol_joule_hotspot_x_um"], 1.0)
        self.assertEqual(metrics["comsol_temperature_hotspot_y_um"], 2.0)

    def test_powershell_orchestrator_requires_six_cases_and_fixed_mesh(self) -> None:
        source = (ROOT / "scripts" / "run_comsol_electrothermal_loading_sensitivity.ps1").read_text(
            encoding="utf-8"
        )
        self.assertIn("$plan.cases.Count -ne 6", source)
        self.assertIn("repeat_mesh_study", source)
        self.assertIn("run_comsol_electrothermal_mvp.ps1", source)
        self.assertIn("'fixed_current_multiplier_1'", source)
        self.assertIn("'fixed_voltage_multiplier_1'", source)
        self.assertIn("fvm_refinement_pass", source)


if __name__ == "__main__":
    unittest.main()
