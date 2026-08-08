import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "docs" / "reproduction_goal" / "04_comsol_electrothermal_field"
SOURCES = STAGE / "data" / "source" / "al_oxide_contact_parameter_sources.csv"
PARAMETERS = STAGE / "data" / "source" / "al_oxide_contact_preregistered_parameters.json"
PREREGISTRATION = STAGE / "al_oxide_contact_preregistration.md"


class AlOxideContactPreregistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parameters = json.loads(PARAMETERS.read_text(encoding="utf-8"))
        with SOURCES.open(encoding="utf-8", newline="") as handle:
            cls.sources = {row["source_id"]: row for row in csv.DictReader(handle)}

    def test_source_ledger_separates_measurement_from_assumptions(self):
        self.assertEqual(
            self.sources["al_powder_native_passivation_thickness"]["classification"],
            "measured_powder_literature",
        )
        self.assertEqual(
            self.sources["metallic_bridge_fraction"]["classification"],
            "numerical_identifiability_sweep",
        )
        self.assertEqual(
            self.sources["two_particle_film_stack"]["classification"],
            "model_assumption",
        )
        self.assertEqual(
            self.sources["alumina_resistivity_intermediate"]["classification"],
            "numerical_log_midpoint",
        )

    def test_frozen_input_contract_matches_archived_manifest(self):
        contract = self.parameters["input_contract"]
        self.assertEqual(contract["archive_run"], 29246532552)
        self.assertEqual(
            [contract["particle_count"], contract["direct_contact_count"], contract["al_al_edge_count"]],
            [96, 115, 50],
        )
        self.assertEqual(contract["source"], "liggghts_pair_gran_local")
        self.assertEqual(
            contract["files"],
            {
                "pilot_final_particles.csv": "a65ce68b8f407b15a28fa4b307ddf76f655b4811fb4ad3d7696cb580eb5deaf2",
                "pilot_final_direct_contacts.csv": "c14f72b320f5a26749b9f82591bd9baab4cd9a641c5c72252d373a0e0d2bbfbb",
                "contact_physics.csv": "20a17cae4d89f15f7095aa1b783bc60b3d46a7d7f5165d49f2e19936b44cf49f",
            },
        )
        self.assertEqual(
            contract["canonical_lf_algorithm"],
            "replace CRLF and bare CR bytes with LF before SHA-256",
        )
        self.assertEqual(
            contract["canonical_lf_files"],
            {
                "pilot_final_particles.csv": "d66af5d5e4a70b33ba91790ad8907a5e9637ce88f5039c97361f98a09cd0d089",
                "pilot_final_direct_contacts.csv": "651582908342d0fd993f677b40101e8e4abd5ffbe932d3faf4e39be1d17ac892",
                "contact_physics.csv": "1a37fab8503c5e912de0f6dc565355bd43d775c7e737fc060df3b66d6830b911",
            },
        )

    def test_parameter_grid_and_models_are_frozen_before_calculation(self):
        frozen = self.parameters["frozen_quantities"]
        self.assertEqual(frozen["particle_film_thickness_m"], [5e-9, 6e-9, 8e-9])
        self.assertEqual(frozen["film_effective_resistivity_ohm_m"], [1e6, 1e9, 1e12])
        self.assertEqual(
            frozen["metallic_bridge_area_fraction"],
            [0.0, 1e-12, 1e-10, 1e-8, 1e-6, 1e-4, 1e-2, 1.0],
        )
        self.assertEqual(
            set(self.parameters["models"]),
            {"clean_lower_bound", "intact_oxide_upper_family", "partial_rupture_primary"},
        )
        self.assertEqual(self.parameters["status"], "preregistered_not_calibrated")

    def test_preregistration_preserves_claim_boundaries(self):
        text = PREREGISTRATION.read_text(encoding="utf-8")
        for phrase in (
            "不得用五节点最短路径电阻冒充并联",
            "不是论文或实验电流",
            "不得称为 calibrated",
            "不运行 COMSOL",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
