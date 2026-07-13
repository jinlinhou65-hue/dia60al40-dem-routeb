from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_dem_3d_percolation import analyze  # noqa: E402
from export_dem_stage_handoff import export_stage  # noqa: E402
from render_dem_3d_pilot import derive, render  # noqa: E402


STAGE = ROOT / "docs" / "reproduction_goal" / "04_comsol_electrothermal_field"
PILOT_PARAMETERS = STAGE / "data" / "source" / "dem_3d_pilot_parameters.json"
ELECTRICAL_PARAMETERS = STAGE / "data" / "source" / "electrothermal_parameter_set.json"
TEMPLATE = ROOT / "liggghts" / "in.dia60al40_dem_3d_pilot.template.liggghts"
WORKFLOW = ROOT / ".github" / "workflows" / "dem-3d-percolation-pilot.yml"


def write_fixture(root: Path, *, remove_middle_edge: bool = False) -> tuple[Path, Path, Path, Path]:
    particles = root / "particles.csv"
    contacts = root / "contacts.csv"
    raw_dump = root / "pilot_final_1.dump"
    raw_local = root / "pilot_final_contacts_1.local"
    particle_rows = []
    for index, (x, y, z) in enumerate(
        ((40, 10, -8), (42, 31.25, -4), (40, 52.5, 0), (38, 73.75, 4), (40, 95, 8)),
        start=1,
    ):
        particle_rows.append(
            {
                "particle_id": index,
                "material": "Al",
                "x_um": x,
                "y_um": y,
                "z_um": z,
                "r_um": 10,
            }
        )
    with particles.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(particle_rows[0]))
        writer.writeheader()
        writer.writerows(particle_rows)
    edges = [(1, 2), (2, 3), (3, 4), (4, 5)]
    if remove_middle_edge:
        edges.remove((3, 4))
    contact_rows = []
    for i, j in edges:
        first, second = particle_rows[i - 1], particle_rows[j - 1]
        dx = second["x_um"] - first["x_um"]
        dy = second["y_um"] - first["y_um"]
        dz = second["z_um"] - first["z_um"]
        norm = (dx * dx + dy * dy + dz * dz) ** 0.5
        contact_rows.append(
            {
                "stage_id": "pilot_final",
                "i": i,
                "j": j,
                "nx": dx / norm,
                "ny": dy / norm,
                "nz": dz / norm,
                "force_x": 0,
                "force_y": 100,
                "force_z": 0,
                "normal_force": 100,
                "contact_point_x_um": (first["x_um"] + second["x_um"]) / 2,
                "contact_point_y_um": (first["y_um"] + second["y_um"]) / 2,
                "contact_point_z_um": (first["z_um"] + second["z_um"]) / 2,
                "source": "liggghts_pair_gran_local",
                "force_unit": "dyne",
            }
        )
    with contacts.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(contact_rows[0]))
        writer.writeheader()
        writer.writerows(contact_rows)
    raw_dump.write_text(
        "ITEM: TIMESTEP\n1\nITEM: NUMBER OF ATOMS\n5\n"
        "ITEM: ATOMS id type x y z vx vy vz radius\n",
        encoding="utf-8",
    )
    raw_local.write_text(
        f"ITEM: TIMESTEP\n1\nITEM: NUMBER OF ENTRIES\n{len(edges)}\n"
        "ITEM: ENTRIES c[1] c[2]\n",
        encoding="utf-8",
    )
    return particles, contacts, raw_dump, raw_local


class Dem3dPilotTest(unittest.TestCase):
    def test_workflow_freezes_solver_budget_and_direct_contact_artifact(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("timeout-minutes: 10", text)
        self.assertIn("timeout --signal=TERM --kill-after=20s 7m", text)
        self.assertIn("3d5c00f20519e6bb6eb6756f51f1ad36564e649d", text)
        self.assertIn("pilot_final_direct_contacts.csv", text)
        self.assertIn("network_3d.png", (ROOT / "scripts" / "analyze_dem_3d_percolation.py").read_text())
        self.assertNotIn("COMSOL", text)

    def test_frozen_parameters_render_a_separate_true_3d_deck(self) -> None:
        parameters = json.loads(PILOT_PARAMETERS.read_text(encoding="utf-8"))
        derived = derive(parameters)
        self.assertEqual(derived["total_count"], 96)
        self.assertAlmostEqual(float(derived["al_volume_fraction"]), 0.40089777745)
        self.assertEqual(derived["load_steps"], 1_150_000)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "pilot.liggghts"
            summary = Path(temp) / "summary.json"
            render(TEMPLATE, PILOT_PARAMETERS, output, summary)
            text = output.read_text(encoding="utf-8")
            self.assertNotIn("@@", text)
            self.assertNotIn("fix             zlock", text)
            self.assertNotIn("set             group all z 0.0", text)
            self.assertIn("region          insertAl", text)
            self.assertIn("-0.0032 0.0032", text)
            self.assertIn("particles_in_region 96", text)

    def test_handoff_uses_true_3d_volume_density_for_custom_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            dump = root / "pilot_final_1.dump"
            dump.write_text(
                "ITEM: TIMESTEP\n1\nITEM: NUMBER OF ATOMS\n1\n"
                "ITEM: ATOMS id type x y z vx vy vz radius\n"
                "1 1 0.001 0.002 0.003 0 0 0 0.001\n",
                encoding="utf-8",
            )
            (root / "model_parameters.csv").write_text(
                "parameter,value,unit\n"
                "stage_ids,pilot_final,text\n"
                "rho_total_pilot_final,0.1,1\n"
                "height_um_pilot_final,100,um\n"
                "domain_width_um,200,um\n"
                "domain_thickness_um,50,um\n",
                encoding="utf-8",
            )
            output = root / "handoff.csv"
            export_stage(dump, "pilot_final", output, contact_gap_um=0.0)
            with output.open(newline="", encoding="utf-8") as handle:
                row = next(csv.DictReader(handle))
            expected = 4.0 * 3.141592653589793 * 10.0**3 / 3.0 / (200 * 100 * 50)
            self.assertAlmostEqual(float(row["actual_rho_total"]), expected)
            self.assertEqual(float(row["z_um"]), 30.0)

    def test_direct_3d_chain_percolates_at_all_frozen_thresholds(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = write_fixture(root)
            output = root / "analysis"
            summary = analyze(
                *paths,
                PILOT_PARAMETERS,
                ELECTRICAL_PARAMETERS,
                output,
            )
            self.assertEqual(summary["decision"], "percolating_all_thresholds")
            self.assertTrue(summary["hard_gate_pass"])
            self.assertEqual(len(summary["threshold_results"]), 3)
            self.assertTrue((output / "network_3d.png").is_file())
            self.assertTrue((output / "path_edges.csv").read_text(encoding="utf-8").count("\n") > 1)

    def test_valid_nonpercolating_direct_graph_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = write_fixture(root, remove_middle_edge=True)
            summary = analyze(
                *paths,
                PILOT_PARAMETERS,
                ELECTRICAL_PARAMETERS,
                root / "analysis",
            )
            self.assertEqual(summary["decision"], "nonpercolating_all_thresholds")
            self.assertTrue(summary["hard_gate_pass"])
            self.assertIsNone(summary["selected_path_total_resistance_ohm"])


if __name__ == "__main__":
    unittest.main()
