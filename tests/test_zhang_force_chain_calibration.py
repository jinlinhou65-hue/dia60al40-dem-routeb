from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = REPO_ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from paper_reproduction import (
    calibrate_zhang_force_chains,
    force_chain_metrics,
    read_contacts,
    read_particles,
)


class ZhangForceChainCalibrationTest(unittest.TestCase):
    def test_calibration_finds_balancing_force_chain_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_dir, contact_dir, pressure_curve = write_force_chain_series(root)
            outdir = root / "calibration"

            summary = calibrate_zhang_force_chains(
                snapshot_dir=snapshot_dir,
                pressure_curve=pressure_curve,
                contact_dir=contact_dir,
                outdir=outdir,
                threshold_factors=[0.05],
                min_chain_lengths=[3],
            )

            rows = read_csv(outdir / "zhang_force_chain_calibration_summary.csv")
            self.assertEqual(summary["parameter_count"], 1)
            self.assertEqual(rows[0]["status"], "pass")
            self.assertEqual(rows[0]["participation_trend"], "increasing")
            self.assertEqual(rows[0]["d1_trend"], "decreasing")
            self.assertEqual(rows[0]["chain_coverage"], "1.0")
            report = (outdir / "zhang_force_chain_calibration_report.md").read_text()
            self.assertIn("Zhang Force-Chain Calibration Report", report)

    def test_cli_writes_json_and_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_dir, contact_dir, pressure_curve = write_force_chain_series(root)
            outdir = root / "cli_calibration"

            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "calibrate_zhang_force_chain.py"),
                    "--snapshot-dir",
                    str(snapshot_dir),
                    "--pressure-curve",
                    str(pressure_curve),
                    "--contact-dir",
                    str(contact_dir),
                    "--outdir",
                    str(outdir),
                    "--threshold-factors",
                    "0.05",
                    "--min-chain-lengths",
                    "3",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(result.stdout)
            self.assertEqual(payload["stage_count"], 2)
            self.assertTrue((outdir / "zhang_force_chain_calibration_report.md").exists())

    def test_force_chain_metrics_track_two_connected_chains(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_dir, contact_dir, _ = write_force_chain_series(root)
            particles = read_particles(snapshot_dir / "dem_fem_handoff_stage0.csv")
            contacts = read_contacts(contact_dir / "stage0_contacts.csv", particles)

            metrics = force_chain_metrics(
                particles,
                contacts,
                threshold_factor=0.05,
                min_chain_length=3,
            )

            self.assertEqual(metrics["force_chain_count"], 2)
            self.assertAlmostEqual(metrics["force_chain_mean_length"], 3.0)
            self.assertGreater(metrics["force_chain_strength_d1"], 0.5)


def write_force_chain_series(root: Path) -> tuple[Path, Path, Path]:
    snapshot_dir = root / "DEM"
    contact_dir = root / "contacts"
    snapshot_dir.mkdir()
    contact_dir.mkdir()
    pressure_curve = snapshot_dir / "pressure_density_curve.csv"
    pressure_curve.write_text(
        "stage_id,pressure_mpa,actual_rho_total\n"
        "stage0,10,0.60\n"
        "stage1,200,0.85\n",
        encoding="utf-8",
    )
    for stage_id in ("stage0", "stage1"):
        write_particles(snapshot_dir / f"dem_fem_handoff_{stage_id}.csv")
    write_contacts(contact_dir / "stage0_contacts.csv", [20.0, 20.0, 1.0, 1.0])
    write_contacts(contact_dir / "stage1_contacts.csv", [12.0, 12.0, 8.0, 8.0])
    return snapshot_dir, contact_dir, pressure_curve


def write_particles(path: Path) -> None:
    path.write_text(
        "particle_id,x_um,y_um,r_um,material\n"
        "1,0,0,10,Al\n"
        "2,18,0,10,Al\n"
        "3,36,0,10,Al\n"
        "4,0,40,10,Diamond\n"
        "5,18,40,10,Diamond\n"
        "6,36,40,10,Diamond\n",
        encoding="utf-8",
    )


def write_contacts(path: Path, forces: list[float]) -> None:
    path.write_text(
        "i,j,normal_force,source\n"
        f"1,2,{forces[0]},solver\n"
        f"2,3,{forces[1]},solver\n"
        f"4,5,{forces[2]},solver\n"
        f"5,6,{forces[3]},solver\n",
        encoding="utf-8",
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
