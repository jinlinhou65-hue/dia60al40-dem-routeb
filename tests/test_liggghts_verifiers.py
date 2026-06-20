from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = REPO_ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from verify_dem_stages import classify_counts


def write_dump(path: Path) -> None:
    path.write_text(
        "ITEM: TIMESTEP\n"
        "0\n"
        "ITEM: NUMBER OF ATOMS\n"
        "3\n"
        "ITEM: BOX BOUNDS pp pp pp\n"
        "0 1\n"
        "0 1\n"
        "0 1\n"
        "ITEM: ATOMS id type x y z vx vy vz radius\n"
        "1 1 0.0100 0.0100 0 0 0 0 0.000919239\n"
        "2 2 0.0200 0.0100 0 0 0 0 0.00212132\n"
        "3 2 0.0300 0.0100 0 0 0 0 0.00212132\n",
        encoding="utf-8",
    )


class LiggghtsVerifierTest(unittest.TestCase):
    def test_final_dump_verifier_uses_refined_dl_radius(self):
        with tempfile.TemporaryDirectory() as tmp:
            dump = Path(tmp) / "stage5.dump"
            write_dump(dump)

            result = subprocess.run(
                [
                    sys.executable,
                    str(PYTHON_DIR / "verify_liggghts_dump.py"),
                    "--input",
                    str(dump),
                    "--expect-al",
                    "1",
                    "--expect-ds",
                    "0",
                    "--expect-dl",
                    "2",
                    "--dl-radius-um",
                    "21.2132",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertIn("Al=1 DS=0 DL=2", result.stdout)

    def test_stage_verifier_classifier_uses_refined_dl_radius(self):
        rows = [
            {"type": "1", "radius": "0.000919239"},
            {"type": "2", "radius": "0.00212132"},
            {"type": "2", "radius": "0.00212132"},
        ]
        args = SimpleNamespace(expect_ds=0, expect_dl=2, ds_radius_um=0.0, dl_radius_um=21.2132)

        counts = classify_counts(rows, args)

        self.assertEqual(counts["Al"], 1)
        self.assertEqual(counts["DS"], 0)
        self.assertEqual(counts["DL"], 2)


if __name__ == "__main__":
    unittest.main()
