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

from paper_reproduction import (
    coupling_summary,
    infer_contacts,
    process_stage_series,
    read_particles,
    run_electrothermal_network,
    sintering_neck_ratio,
)


class SinteringLawTest(unittest.TestCase):
    def test_neck_growth_responds_to_temperature_and_particle_size(self):
        cold = sintering_neck_ratio(
            temperature_k=293.15,
            time_s=1.0,
            particle_radius_um=10.0,
            law="surface",
        )
        hot = sintering_neck_ratio(
            temperature_k=330.0,
            time_s=1.0,
            particle_radius_um=10.0,
            law="surface",
        )
        small = sintering_neck_ratio(
            temperature_k=293.15,
            time_s=1.0,
            particle_radius_um=5.0,
            law="surface",
        )

        self.assertGreater(hot, cold)
        self.assertGreater(small, cold)
        self.assertLessEqual(hot, 0.8)

    def test_electrothermal_network_outputs_diffusion_neck_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            particles_path = Path(tmp) / "particles.csv"
            write_particles(particles_path, compression=0.0)
            particles = read_particles(particles_path)
            contacts = infer_contacts(particles, normal_stiffness=2.0)
            particle_fields, contact_fields = run_electrothermal_network(
                particles,
                contacts,
                heat_to_temperature=100.0,
                sintering_time_s=2.0,
            )
            summary = coupling_summary(contact_fields, particle_fields)

            self.assertTrue(all("neck_ratio_diffusion" in row for row in particle_fields))
            self.assertTrue(all("neck_ratio_thermal_gain" in row for row in particle_fields))
            self.assertTrue(all("dominant_diffusion_mechanism" in row for row in particle_fields))
            self.assertTrue(any(float(row["neck_ratio_diffusion"]) > 0.02 for row in particle_fields))
            self.assertGreater(summary["particle_heat_vs_neck_ratio"], 0.0)

    def test_stage_series_writes_electrothermal_detail_tables(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_dir = root / "DEM"
            outdir = root / "series"
            snapshot_dir.mkdir()
            stages = [
                ("stage0_preload", 0.0, 0.56, 50.0, 0.0),
                ("stage1_rho065", 45.0, 0.65, 42.0, 2.0),
                ("stage2_rho072", 130.0, 0.72, 36.0, 3.5),
            ]
            (snapshot_dir / "pressure_density_curve.csv").write_text(
                "stage_id,pressure_mpa,actual_rho_total,target_rho_total,current_height_um\n"
                + "\n".join(f"{stage},{pressure},{rho},{rho},{height}" for stage, pressure, rho, height, _ in stages)
                + "\n",
                encoding="utf-8",
            )
            for stage, _, _, _, compression in stages:
                write_particles(snapshot_dir / f"dem_fem_handoff_{stage}.csv", compression)

            process_stage_series(
                snapshot_dir=snapshot_dir,
                pressure_curve=snapshot_dir / "pressure_density_curve.csv",
                outdir=outdir,
                width_um=40.0,
            )

            particles_csv = outdir / "stage_details" / "stage2_rho072_electrothermal_particles.csv"
            contacts_csv = outdir / "stage_details" / "stage2_rho072_electrothermal_contacts.csv"
            self.assertTrue(particles_csv.exists())
            self.assertTrue(contacts_csv.exists())
            rows = read_csv(particles_csv)
            self.assertIn("temperature_k", rows[0])
            self.assertIn("neck_ratio_diffusion", rows[0])
            self.assertIn("neck_ratio_thermal_gain", rows[0])


def write_particles(path: Path, compression: float) -> None:
    path.write_text(
        "particle_id,x_um,y_um,r_um,material\n"
        "1,0,0,10,Al\n"
        "2,18,0,10,Al\n"
        f"3,9,{15 - compression},10,Diamond\n"
        f"4,9,{30 - 2 * compression},10,Al\n",
        encoding="utf-8",
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
