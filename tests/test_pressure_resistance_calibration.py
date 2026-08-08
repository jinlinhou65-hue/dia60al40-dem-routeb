from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from calibrate_pressure_resistance import (  # noqa: E402
    DataContractError,
    calibrate,
    invert_network_resistance,
    load_network_curve,
    load_records,
)


STAGE = ROOT / "docs" / "reproduction_goal" / "04_comsol_electrothermal_field"
SCHEMA = STAGE / "data" / "source" / "pressure_resistance_experiment_schema.json"
TEMPLATE = STAGE / "data" / "source" / "pressure_resistance_experiment_template.csv"
CONFIG = STAGE / "data" / "source" / "pressure_resistance_calibration_config.template.json"
SCENARIOS = STAGE / "evidence" / "al_oxide_network_sensitivity" / "scenarios.csv"
WORKFLOW = ROOT / ".github" / "workflows" / "pressure-resistance-calibration-contract.yml"


def synthetic_row(specimen: int, resistance: float) -> dict[str, str]:
    return {
        "record_id": f"synthetic-{specimen}",
        "data_origin": "synthetic_test",
        "condition_id": "synthetic-condition",
        "specimen_id": f"synthetic-specimen-{specimen}",
        "powder_batch_id": "synthetic-batch",
        "repeat_index": str(specimen),
        "composition_basis": "volume_fraction",
        "al_fraction": "0.4",
        "diamond_fraction": "0.6",
        "specimen_diameter_m": "0.01",
        "specimen_height_m": "0.002",
        "cycle_index": "1",
        "measurement_index": "1",
        "loading_stage": "loading",
        "pressure_pa": "1e8",
        "elapsed_time_s": "10",
        "dwell_time_s": "0",
        "specimen_temperature_k": "293.15",
        "source_mode": "resistance_meter",
        "wiring_mode": "four_wire",
        "applied_voltage_v": "",
        "applied_current_a": "",
        "measured_voltage_v": "",
        "measured_current_a": "",
        "measured_resistance_ohm": f"{resistance:.17g}",
        "lead_contact_resistance_ohm": "0",
        "resistance_standard_uncertainty_ohm": "0",
        "instrument_id": "synthetic-instrument",
        "instrument_calibration_date": "2026-08-08",
        "operator_id": "synthetic-test",
        "quality_flag": "accepted",
        "notes": "algorithm fixture; never physical evidence",
    }


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    fields = [field["name"] for field in json.loads(SCHEMA.read_text())["fields"]]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


class PressureResistanceCalibrationTests(unittest.TestCase):
    def test_empty_template_is_valid_but_cannot_calibrate(self):
        with tempfile.TemporaryDirectory() as temp:
            summary = calibrate(TEMPLATE, SCHEMA, CONFIG, SCENARIOS, Path(temp))
            self.assertEqual(summary["status"], "awaiting_real_experiment_data")
            self.assertFalse(summary["calibrated"])
            self.assertEqual(summary["row_count"], 0)
            self.assertTrue((Path(temp) / "evidence_manifest.json").is_file())

    def test_template_header_exactly_matches_machine_schema(self):
        records, schema = load_records(TEMPLATE, SCHEMA)
        self.assertEqual(records, [])
        with TEMPLATE.open(newline="", encoding="utf-8-sig") as handle:
            observed = csv.DictReader(handle).fieldnames
        self.assertEqual(observed, [field["name"] for field in schema["fields"]])
        self.assertEqual(len(observed), 32)

    def test_frozen_curve_exactly_recovers_a_grid_bridge_fraction(self):
        curve = load_network_curve(SCENARIOS)
        target = dict(curve)[1e-6]
        result = invert_network_resistance(target, curve)
        self.assertEqual(result["status"], "grid_exact")
        self.assertEqual(result["f_m"], 1e-6)

    def test_synthetic_fixture_never_becomes_physical_calibration(self):
        curve = load_network_curve(SCENARIOS)
        scale = 2.5
        resistance = dict(curve)[1e-6] * scale
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / "synthetic.csv"
            config_path = root / "config.json"
            write_rows(data, [synthetic_row(index, resistance) for index in range(1, 4)])
            config = json.loads(CONFIG.read_text())
            config.update(
                {
                    "specimen_resistance_scale_factor": scale,
                    "scale_factor_source": "synthetic_unit_test_only",
                    "scale_relative_standard_uncertainty": 0.0,
                    "bootstrap_resamples": 100,
                }
            )
            config_path.write_text(json.dumps(config), encoding="utf-8")
            summary = calibrate(data, SCHEMA, config_path, SCENARIOS, root / "output")
            with (root / "output" / "condition_results.csv").open(newline="", encoding="utf-8") as handle:
                result = list(csv.DictReader(handle))[0]
            self.assertEqual(summary["status"], "synthetic_validation_only")
            self.assertFalse(summary["calibrated"])
            self.assertAlmostEqual(float(result["f_m"]), 1e-6)

    def test_missing_scale_is_reported_as_not_identifiable(self):
        curve = load_network_curve(SCENARIOS)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / "synthetic.csv"
            write_rows(data, [synthetic_row(index, dict(curve)[1e-6]) for index in range(1, 4)])
            summary = calibrate(data, SCHEMA, CONFIG, SCENARIOS, root / "output")
            self.assertEqual(summary["status"], "not_identifiable_missing_scale")
            self.assertIn("missing_independent_specimen_scale_factor", summary["blockers"])
            self.assertFalse(summary["calibrated"])

    def test_two_wire_without_lead_contact_resistance_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            data = Path(temp) / "bad.csv"
            row = synthetic_row(1, 10.0)
            row["wiring_mode"] = "two_wire"
            row["lead_contact_resistance_ohm"] = ""
            write_rows(data, [row])
            with self.assertRaisesRegex(DataContractError, "two_wire requires"):
                load_records(data, SCHEMA)

    def test_fewer_than_three_independent_specimens_is_a_blocker(self):
        curve = load_network_curve(SCENARIOS)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / "synthetic.csv"
            config_path = root / "config.json"
            write_rows(data, [synthetic_row(index, dict(curve)[1e-6]) for index in range(1, 3)])
            config = json.loads(CONFIG.read_text())
            config.update(
                {
                    "specimen_resistance_scale_factor": 1.0,
                    "scale_factor_source": "synthetic_unit_test_only",
                    "scale_relative_standard_uncertainty": 0.0,
                    "bootstrap_resamples": 10,
                }
            )
            config_path.write_text(json.dumps(config), encoding="utf-8")
            summary = calibrate(data, SCHEMA, config_path, SCENARIOS, root / "output")
            self.assertIn("insufficient_independent_specimens", summary["blockers"])
            self.assertFalse(summary["calibrated"])

    def test_voltage_current_inconsistency_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            data = Path(temp) / "bad.csv"
            row = synthetic_row(1, 10.0)
            row["measured_voltage_v"] = "1"
            row["measured_current_a"] = "1"
            write_rows(data, [row])
            with self.assertRaisesRegex(DataContractError, "V/I and measured resistance"):
                load_records(data, SCHEMA)

    def test_workflow_is_license_free_time_bounded_and_no_data(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("timeout-minutes: 5", text)
        self.assertIn("awaiting_real_experiment_data", text)
        self.assertIn("tests.test_pressure_resistance_calibration", text)
        self.assertNotIn("COMSOL", text)
        self.assertNotIn("liggghts", text.lower())


if __name__ == "__main__":
    unittest.main()
