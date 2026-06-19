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

from paper_reproduction import reproduce_zhang, validate_algorithm_reproduction


ZHANG_REQUIRED_FIELDS = {
    "step",
    "pressure_mpa",
    "relative_density",
    "contact_force_mean",
    "contact_force_std",
    "contact_gini",
    "contact_participation",
    "strong_contact_threshold",
    "strong_contact_fraction",
    "force_chain_count",
    "force_chain_mean_length",
    "force_chain_mean_strength",
    "force_chain_strength_std",
    "force_chain_strength_inhomogeneity_d1",
    "measurement_circle_count",
    "local_stress_mean",
    "local_stress_std",
    "local_stress_inhomogeneity_d2",
}


class ZhangMultiscaleMetricsTest(unittest.TestCase):
    def test_zhang_outputs_force_chain_local_stress_and_friction_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            outdir = Path(tmp) / "paper"
            summary = reproduce_zhang(outdir / "zhang")

            self.assertIn("zhang_multiscale_metrics.csv", summary["outputs"])
            self.assertIn("zhang_friction_sensitivity.csv", summary["outputs"])

            metrics = read_csv(outdir / "zhang" / "zhang_multiscale_metrics.csv")
            friction = read_csv(outdir / "zhang" / "zhang_friction_sensitivity.csv")
            self.assertTrue(ZHANG_REQUIRED_FIELDS <= set(metrics[0]))
            self.assertEqual({row["friction_type"] for row in friction}, {"wall", "particle"})

            self.assertGreater(float(metrics[-1]["pressure_mpa"]), float(metrics[0]["pressure_mpa"]))
            self.assertGreater(float(metrics[-1]["relative_density"]), float(metrics[0]["relative_density"]))
            self.assertLess(
                float(metrics[-1]["force_chain_strength_inhomogeneity_d1"]),
                float(metrics[0]["force_chain_strength_inhomogeneity_d1"]),
            )
            self.assertLess(
                float(metrics[-1]["local_stress_inhomogeneity_d2"]),
                float(metrics[0]["local_stress_inhomogeneity_d2"]),
            )
            self.assertTrue(all(float(row["force_chain_count"]) > 0.0 for row in metrics))
            self.assertTrue(all(float(row["local_stress_mean"]) > 0.0 for row in metrics))

    def test_zhang_validation_gates_include_friction_dominance(self):
        with tempfile.TemporaryDirectory() as tmp:
            outdir = Path(tmp) / "paper"
            reproduce_zhang(outdir / "zhang")

            checks, acceptance = validate_algorithm_reproduction(outdir, papers=["zhang"])
            self.assertEqual(acceptance, [{"paper": "Zhang", "status": "pass", "pass": 14, "review": 0, "missing": 0, "mismatch": 0, "check_count": 14}])
            self.assertTrue(
                any(
                    check["label"] == "particle friction has stronger meso force-chain effect"
                    and check["status"] == "pass"
                    for check in checks
                )
            )

            friction = read_csv(outdir / "zhang" / "zhang_friction_sensitivity.csv")
            particle_gini = endpoint_delta(friction, "particle", "particle_mu", "contact_gini")
            wall_gini = endpoint_delta(friction, "wall", "wall_mu", "contact_gini")
            particle_d1 = endpoint_delta(friction, "particle", "particle_mu", "force_chain_strength_inhomogeneity_d1")
            wall_d1 = endpoint_delta(friction, "wall", "wall_mu", "force_chain_strength_inhomogeneity_d1")
            self.assertGreater(particle_gini, wall_gini)
            self.assertGreater(particle_d1, wall_d1)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def endpoint_delta(rows: list[dict[str, str]], friction_type: str, x_field: str, value_field: str) -> float:
    points = sorted(
        (float(row[x_field]), float(row[value_field]))
        for row in rows
        if row["friction_type"] == friction_type
    )
    return points[-1][1] - points[0][1]


if __name__ == "__main__":
    unittest.main()
