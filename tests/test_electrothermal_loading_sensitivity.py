from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from electrothermal_contact_model import write_comsol_interpolation  # noqa: E402
from run_electrothermal_loading_sensitivity import (  # noqa: E402
    evaluate_loading_gates,
    fixed_current_voltage,
    load_loading_parameters,
    portable_plan_path,
)


STAGE = ROOT / "docs" / "reproduction_goal" / "04_comsol_electrothermal_field"
BASE = STAGE / "data" / "source" / "electrothermal_parameter_set.json"
LOADING = STAGE / "data" / "source" / "loading_mode_parameter_set.json"


def make_row(mode: str, multiplier: float, power: float, rise: float) -> dict[str, object]:
    target = 10.0
    return {
        "loading_mode": mode,
        "al_al_resistance_multiplier": multiplier,
        "electric_power_w_per_m_depth": power,
        "temperature_rise_max_k": rise,
        "top_current_a_per_m_depth": target,
        "electric_relative_balance_error": 1.0e-14,
        "joule_hotspot_x_um": multiplier,
        "joule_hotspot_y_um": 5.0,
        "temperature_hotspot_x_um": multiplier,
        "temperature_hotspot_y_um": 6.0,
    }


class ElectrothermalLoadingSensitivityTest(unittest.TestCase):
    def test_portable_plan_path_marks_external_workflow_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "stage"
            inside = root / "data" / "prepared"
            outside = Path(temp) / "outputs" / "multiplier_1"
            self.assertEqual(portable_plan_path(inside, root, "external"), "data/prepared")
            self.assertEqual(
                portable_plan_path(outside, root, "external"),
                "external/multiplier_1",
            )

    def test_loading_parameter_file_pins_base_hash_and_fixed_mesh(self) -> None:
        data = load_loading_parameters(LOADING, BASE)
        self.assertEqual(data["comsol_mesh"]["expected_element_count"], 3316)
        self.assertFalse(data["comsol_mesh"]["repeat_mesh_study"])
        self.assertIn("not_paper_boundary_condition", data["paper_loading_evidence"]["classification"])

    def test_fixed_current_voltage_scales_inverse_to_base_conductance(self) -> None:
        self.assertAlmostEqual(fixed_current_voltage(10.0, 20.0, 0.1), 0.05)
        self.assertAlmostEqual(fixed_current_voltage(10.0, 2.0, 0.1), 0.5)
        with self.assertRaises(ValueError):
            fixed_current_voltage(10.0, 0.0, 0.1)

    def test_loading_gates_require_opposite_power_and_temperature_trends(self) -> None:
        loading = json.loads(LOADING.read_text(encoding="utf-8"))
        rows = [
            make_row("fixed_voltage", 1.0, 100.0, 1.0),
            make_row("fixed_voltage", 10.0, 10.0, 0.1),
            make_row("fixed_voltage", 100.0, 1.0, 0.01),
            make_row("fixed_current", 1.0, 1.0, 0.01),
            make_row("fixed_current", 10.0, 10.0, 0.1),
            make_row("fixed_current", 100.0, 100.0, 1.0),
        ]
        gates = evaluate_loading_gates(rows, loading, 10.0)
        self.assertTrue(all(gates.values()))
        rows[-1]["electric_power_w_per_m_depth"] = 5.0
        self.assertFalse(evaluate_loading_gates(rows, loading, 10.0)["fixed_current_power_trend_gate"])

    def test_comsol_interpolation_writer_uses_expected_four_column_contract(self) -> None:
        rows = [{"x_um": 0.0, "y_um": 1.0, "sigma_s_m": 2.0, "k_w_mk": 3.0}]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "stage5_comsol_interpolation.txt"
            write_comsol_interpolation(path, rows)
            self.assertEqual(
                path.read_text(encoding="ascii"),
                "% x_um y_um sigma_s_m k_w_mk\n0 1 2 3\n",
            )


if __name__ == "__main__":
    unittest.main()
