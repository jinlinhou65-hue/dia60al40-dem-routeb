from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_electrothermal_fvm_refinement import (  # noqa: E402
    resample_property_grid,
    weighted_top_centroid,
)


class ElectrothermalFvmRefinementTest(unittest.TestCase):
    def test_property_resampling_preserves_bounds_and_refines_intervals(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.csv"
            with source.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["x_um", "y_um", "sigma_s_m", "k_w_mk"])
                for y in (0.0, 1.0, 2.0):
                    for x in (0.0, 1.0, 2.0):
                        writer.writerow([x, y, 10.0 + x + y, 20.0 + x + y])
            output = root / "refined.csv"
            nx, ny = resample_property_grid(source, 2, output)
            with output.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
        self.assertEqual((nx, ny), (5, 5))
        self.assertEqual(len(rows), 25)
        self.assertEqual(min(float(row["sigma_s_m"]) for row in rows), 10.0)
        self.assertEqual(max(float(row["sigma_s_m"]) for row in rows), 14.0)

    def test_weighted_top_centroid_tracks_high_field_region(self) -> None:
        xs = np.array([0.0, 1.0, 2.0])
        ys = np.array([0.0, 1.0, 2.0])
        field = np.ones((3, 3))
        field[2, 2] = 100.0
        centroid = weighted_top_centroid(xs, ys, field, quantile=0.8)
        self.assertGreater(float(centroid["x_um"]), 1.9)
        self.assertGreater(float(centroid["y_um"]), 1.9)


if __name__ == "__main__":
    unittest.main()
