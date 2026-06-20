from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "diagnose_particle_scale_feasibility.py"


class ParticleScaleFeasibilityTest(unittest.TestCase):
    def test_diagnostic_reports_d_pscale2_crowding(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--cases",
                "D",
                "--particle-count-scales",
                "2",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        rows = list(csv.DictReader(result.stdout.splitlines()))
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["diamond_size_case"], "D")
        self.assertEqual(row["particle_count_scale"], "2")
        self.assertEqual(row["al_count"], "70")
        self.assertEqual(row["dl_count"], "22")
        self.assertGreater(float(row["stage5_disk_packing_fraction"]), 1.0)
        self.assertIn("final_disk_packing_ge_1", row["risk_flags"])

    def test_diagnostic_writes_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "scale_feasibility.csv"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--cases",
                    "C,D,E",
                    "--particle-count-scales",
                    "1,2",
                    "--output",
                    str(output),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

            with output.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 6)
            self.assertIn("insert_region_disk_packing_fraction", rows[0])
            self.assertIn("largest_diameter_to_stage5_height", rows[0])


if __name__ == "__main__":
    unittest.main()
