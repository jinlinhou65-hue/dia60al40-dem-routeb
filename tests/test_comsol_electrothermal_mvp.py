from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from prepare_comsol_electrothermal_input import prepare_inputs  # noqa: E402
from analyze_electrothermal_mvp import relative_difference  # noqa: E402
from analyze_comsol_mesh_convergence import analyze as analyze_mesh_convergence  # noqa: E402
from analyze_comsol_mesh_convergence import parse_comsol_log  # noqa: E402
from solve_electrothermal_fvm import solve_fvm  # noqa: E402


class ComsolElectrothermalMvpTest(unittest.TestCase):
    def write_fixture(self, root: Path, *, source: str = "liggghts_pair_gran_local") -> tuple[Path, Path]:
        particles = root / "particles.csv"
        contacts = root / "contacts.csv"
        with particles.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["current_height_um", "particle_id", "material"])
            writer.writerow([100.0, 1, "Al"])
            writer.writerow([100.0, 2, "Diamond"])
        with contacts.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "stage_id",
                    "i",
                    "j",
                    "normal_force",
                    "contact_point_x_um",
                    "contact_point_y_um",
                    "source",
                    "force_unit",
                ]
            )
            writer.writerow(["stage5_rho095", 1, 2, 10000.0, 50.0, 50.0, source, "dyne"])
        return particles, contacts

    def test_preprocessor_requires_direct_liggghts_contacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            particles, contacts = self.write_fixture(root, source="inferred")
            with self.assertRaisesRegex(ValueError, "contact source"):
                prepare_inputs(particles, contacts, root / "out", width_um=100.0, nx=9, ny=9)

    def test_preprocessor_writes_bounded_positive_property_grid(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            particles, contacts = self.write_fixture(root)
            manifest = prepare_inputs(particles, contacts, root / "out", width_um=100.0, nx=9, ny=9)
            with (root / "out" / "stage5_contact_property_grid.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 81)
            factors = [float(row["contact_factor"]) for row in rows]
            self.assertAlmostEqual(max(factors), 1.0)
            self.assertGreaterEqual(min(factors), 0.0)
            self.assertTrue(all(float(row["sigma_s_m"]) > 0 for row in rows))
            interpolation = root / "out" / "stage5_comsol_interpolation.txt"
            self.assertTrue(interpolation.is_file())
            self.assertTrue(interpolation.read_text(encoding="ascii").startswith("% x_um y_um"))
            self.assertEqual(manifest["contact_mapping"]["contact_count"], 1)
            self.assertEqual(manifest["fidelity"], "mesoscale_smoke_model_not_particle_resolved")

    def test_parallel_fvm_satisfies_limits_and_power_balance(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            particles, contacts = self.write_fixture(root)
            prepare_inputs(particles, contacts, root / "input", width_um=100.0, nx=17, ny=17)
            summary = solve_fvm(root / "input" / "stage5_contact_property_grid.csv", root / "result")
            self.assertAlmostEqual(summary["voltage_min_v"], 0.0, places=10)
            self.assertAlmostEqual(summary["voltage_max_v"], 0.1, places=10)
            self.assertLess(summary["electric_relative_balance_error"], 1.0e-8)
            self.assertGreater(summary["temperature_rise_max_k"], 0.0)
            self.assertTrue((root / "result" / "fvm_electrothermal_fields.png").is_file())
            saved = json.loads((root / "result" / "fvm_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["solver"], "structured_finite_volume_parallel_check")

    def test_comsol_builder_contains_required_physics_without_solid_mechanics(self) -> None:
        source = (ROOT / "comsol" / "Dia60Al40_ElectrothermalMVP.java").read_text(encoding="utf-8")
        self.assertIn('"ConductiveMedia"', source)
        self.assertIn('"HeatTransfer"', source)
        self.assertIn('"ElectromagneticHeatSource"', source)
        self.assertIn('"ec.Qh"', source)
        self.assertNotIn('"SolidMechanics"', source)
        self.assertNotIn("static class", source)

    def test_comsol_builder_accepts_parameterized_mesh_sizes(self) -> None:
        source = (ROOT / "comsol" / "Dia60Al40_ElectrothermalMVP.java").read_text(encoding="utf-8")
        self.assertIn("meshHmaxUm", source)
        self.assertIn("meshHminUm", source)
        self.assertIn("mesh_hmax_um", source)

    def test_mesh_analyzer_parses_chinese_comsol_log_and_passes_refinement(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for level, hmax, hmin, elements, dof, power, max_temp in (
                ("coarse", 12.0, 1.5, 1500, 6200, 397.0, 293.7910),
                ("medium", 8.0, 1.0, 3300, 13600, 396.3, 293.7898),
                ("fine", 5.0, 0.625, 8200, 33200, 396.1, 293.7894),
            ):
                directory = root / level
                directory.mkdir()
                (directory / "comsol_summary.json").write_text(
                    json.dumps(
                        {
                            "mesh_hmax_um": hmax,
                            "mesh_hmin_um": hmin,
                            "ambient_temperature_k": 293.15,
                            "max_temperature_k": max_temp,
                            "integrated_joule_2d_w_per_m_depth": power,
                            "solve_status": "success",
                        }
                    ),
                    encoding="utf-8",
                )
                (directory / "comsol_batch.log").write_text(
                    f"单元数：{elements}\n最小单元质量：0.65\n求解的自由度数：{dof}（加上 10 个内部自由度）。\n",
                    encoding="utf-8",
                )
            result = analyze_mesh_convergence(root, root / "comparison")
            self.assertEqual(result["decision"], "mesh_pass")
            self.assertTrue((root / "comparison" / "mesh_convergence.png").is_file())
            parsed = parse_comsol_log((root / "fine" / "comsol_batch.log").read_text(encoding="utf-8"))
            self.assertEqual(parsed["element_count"], 8200)

    def test_cross_solver_relative_difference_is_symmetric(self) -> None:
        self.assertAlmostEqual(relative_difference(396.0, 392.0), relative_difference(392.0, 396.0))
        self.assertEqual(relative_difference(0.0, 0.0), 0.0)


if __name__ == "__main__":
    unittest.main()
