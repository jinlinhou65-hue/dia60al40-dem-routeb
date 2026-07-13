from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from electrothermal_contact_model import (  # noqa: E402
    analyze_topology,
    build_contact_physics,
    gaussian_property_grid,
    load_parameter_set,
    read_contacts,
    read_particles,
)


STAGE = ROOT / "docs" / "reproduction_goal" / "04_comsol_electrothermal_field"
PARTICLES = STAGE / "data" / "source" / "dem_fem_handoff_stage5_rho095.csv"
CONTACTS = STAGE / "data" / "source" / "stage5_rho095_direct_contacts.csv"
PARAMETERS = STAGE / "data" / "source" / "electrothermal_parameter_set.json"


class ElectrothermalContactModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parameters = load_parameter_set(PARAMETERS)
        cls.particles, cls.height_um = read_particles(PARTICLES)
        cls.contacts = read_contacts(CONTACTS)
        cls.parameters["domain_height_um"] = cls.height_um

    def test_real_stage_contact_types_and_hertz_geometry_are_audited(self) -> None:
        rows = build_contact_physics(
            self.particles, self.contacts, self.parameters, al_al_multiplier=10.0
        )
        topology = analyze_topology(self.particles, self.height_um, rows, self.parameters)
        self.assertEqual(topology["contact_type_counts"], {
            "Al-Al": 63,
            "Al-Diamond": 80,
            "Diamond-Diamond": 14,
        })
        self.assertGreater(topology["hertz_warning_count"], 0)
        self.assertLess(topology["max_contact_radius_fraction"], 1.0)

    def test_undoped_diamond_screen_removes_electrical_percolation(self) -> None:
        rows = build_contact_physics(
            self.particles, self.contacts, self.parameters, al_al_multiplier=10.0
        )
        topology = analyze_topology(self.particles, self.height_um, rows, self.parameters)
        self.assertEqual(topology["electrical_active_contact_type_counts"], {"Al-Al": 63})
        self.assertFalse(topology["electrical_percolates_bottom_to_top"])

    def test_diamond_contact_is_far_more_resistive_than_al_al(self) -> None:
        rows = build_contact_physics(
            self.particles, self.contacts, self.parameters, al_al_multiplier=10.0
        )
        al_al = [row["electrical_resistance_ohm"] for row in rows if row["contact_type"] == "Al-Al"]
        cross = [row["electrical_resistance_ohm"] for row in rows if row["contact_type"] == "Al-Diamond"]
        self.assertGreater(min(cross), max(al_al) * 1.0e12)
        self.assertTrue(
            all(row["thermal_interface_resistance_k_w"] > 0 for row in rows if row["contact_type"] == "Al-Diamond")
        )

    def test_frozen_reference_mapping_preserves_resistance_sensitivity(self) -> None:
        reference = build_contact_physics(
            self.particles, self.contacts, self.parameters, al_al_multiplier=10.0
        )
        high_resistance = build_contact_physics(
            self.particles, self.contacts, self.parameters, al_al_multiplier=100.0
        )
        reference_grid = gaussian_property_grid(reference, reference, self.parameters)
        high_grid = gaussian_property_grid(high_resistance, reference, self.parameters)
        mean_reference = sum(row["sigma_s_m"] for row in reference_grid) / len(reference_grid)
        mean_high = sum(row["sigma_s_m"] for row in high_grid) / len(high_grid)
        self.assertGreater(mean_reference, mean_high)
        self.assertAlmostEqual(max(row["electrical_contact_factor"] for row in reference_grid), 1.0)


if __name__ == "__main__":
    unittest.main()
