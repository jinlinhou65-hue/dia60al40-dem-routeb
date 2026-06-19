from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = REPO_ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from paper_reproduction import reproduce_li, validate_algorithm_reproduction


class LiCoreShellMetricsTest(unittest.TestCase):
    def test_li_outputs_core_shell_temperature_and_convergence_tables(self):
        with tempfile.TemporaryDirectory() as tmp:
            outdir = Path(tmp) / "paper"
            summary = reproduce_li(outdir / "li")

            self.assertEqual(
                set(summary["outputs"]),
                {
                    "li_coated_powder_sweeps.csv",
                    "li_core_shell_metrics.csv",
                    "li_temperature_pressure_response.csv",
                    "li_particle_count_convergence.csv",
                },
            )

            core = read_csv(outdir / "li" / "li_core_shell_metrics.csv")
            temperature = read_csv(outdir / "li" / "li_temperature_pressure_response.csv")
            convergence = read_csv(outdir / "li" / "li_particle_count_convergence.csv")

            density = {row["composition"]: float(row["relative_density_600mpa"]) for row in core}
            self.assertGreater(density["Cu30@Fe70"], density["Cu20@Fe80"])
            self.assertGreater(density["Cu20@Fe80"], density["Cu10@Fe90"])
            self.assertGreater(density["Cu10@Fe90"], density["Fe"])

            stress = {row["composition"]: float(row["stress_uniformity_index"]) for row in core}
            plasticity = {row["composition"]: float(row["plastic_strain_proxy"]) for row in core}
            self.assertLess(stress["Cu20@Fe80"], stress["Fe"])
            self.assertGreater(plasticity["Cu20@Fe80"], plasticity["Fe"])

            delta_300 = temperature_delta(temperature, 300.0)
            delta_600 = temperature_delta(temperature, 600.0)
            self.assertGreater(delta_300, 0.0)
            self.assertLess(delta_600, delta_300)

            self.assertLess(particle_count_delta(convergence, 600.0), particle_count_delta(convergence, 300.0))
            self.assertLess(particle_count_delta(convergence, 600.0), 0.001)

    def test_li_validation_gates_cover_core_shell_and_convergence(self):
        with tempfile.TemporaryDirectory() as tmp:
            outdir = Path(tmp) / "paper"
            reproduce_li(outdir / "li")

            checks, acceptance = validate_algorithm_reproduction(outdir, papers=["li"])
            self.assertEqual(acceptance[0]["paper"], "Li")
            self.assertEqual(acceptance[0]["status"], "pass")
            self.assertEqual(acceptance[0]["check_count"], 14)
            self.assertEqual(acceptance[0]["pass"], 14)
            self.assertTrue(
                any(
                    check["label"] == "temperature effect weakens after 500 MPa"
                    and check["status"] == "pass"
                    for check in checks
                )
            )
            self.assertTrue(
                any(
                    check["label"] == "100 and 197 particle models converge at high pressure"
                    and check["status"] == "pass"
                    for check in checks
                )
            )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def temperature_delta(rows: list[dict[str, str]], pressure_mpa: float) -> float:
    low = temperature_density(rows, pressure_mpa, 20.0)
    high = temperature_density(rows, pressure_mpa, 300.0)
    return high - low


def temperature_density(rows: list[dict[str, str]], pressure_mpa: float, temperature_c: float) -> float:
    for row in rows:
        if (
            row["material"] == "Cu20@Fe80"
            and float(row["pressure_mpa"]) == pressure_mpa
            and float(row["temperature_c"]) == temperature_c
        ):
            return float(row["relative_density"])
    raise AssertionError(f"missing temperature row {pressure_mpa=} {temperature_c=}")


def particle_count_delta(rows: list[dict[str, str]], pressure_mpa: float) -> float:
    values = {
        int(row["particle_count"]): float(row["relative_density"])
        for row in rows
        if float(row["pressure_mpa"]) == pressure_mpa
    }
    return abs(values[197] - values[100])


if __name__ == "__main__":
    unittest.main()
