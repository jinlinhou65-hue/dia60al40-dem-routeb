from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path


import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = REPO_ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from paper_reproduction import reproduce_yuan, validate_algorithm_reproduction


class YuanArchMetricsTest(unittest.TestCase):
    def test_yuan_outputs_paper_arch_length_obstruction_and_trends(self):
        with tempfile.TemporaryDirectory() as tmp:
            outdir = Path(tmp)
            reproduce_yuan(outdir / "yuan")
            rows = read_csv(outdir / "yuan" / "yuan_arch_bridge_metrics.csv")

            self.assertTrue(rows)
            for field in [
                "arch_mean_length",
                "arch_total_length",
                "arch_obstruction_index",
                "arch_mean_strength",
                "arch_direction_angle_degrees",
                "arch_buckling_angle_degrees",
            ]:
                self.assertIn(field, rows[0])

            circle = [row for row in rows if row["shape"] == "circle"]
            strip = [row for row in rows if row["shape"] == "strip"]
            self.assertGreater(maximum(circle, "arch_count"), float(circle[0]["arch_count"]))
            self.assertGreater(maximum(circle, "arch_count"), float(circle[-1]["arch_count"]))
            self.assertGreater(mean(circle, "arch_obstruction_index"), mean(strip, "arch_obstruction_index"))
            self.assertLess(
                abs(maximum(rows, "arch_direction_angle_degrees") - 90.0),
                8.0,
            )

            checks, summary = validate_algorithm_reproduction(outdir, papers=["yuan"])
            self.assertEqual(summary[0]["status"], "pass")
            labels = {check["label"]: check["status"] for check in checks}
            self.assertEqual(labels["arch count increases then fluctuates"], "pass")
            self.assertEqual(labels["arch total length fluctuates"], "pass")
            self.assertEqual(labels["arch strength growth slows after 100 MPa"], "pass")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def mean(rows: list[dict[str, str]], field: str) -> float:
    values = [float(row[field]) for row in rows]
    return sum(values) / len(values)


def maximum(rows: list[dict[str, str]], field: str) -> float:
    return max(float(row[field]) for row in rows)


if __name__ == "__main__":
    unittest.main()
