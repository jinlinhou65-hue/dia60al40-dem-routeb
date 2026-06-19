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
    process_stage_series,
    read_contacts,
    read_particles,
    summarize_contact_network,
)
from export_liggghts_contact_forces import export_contacts


class DirectContactMetricsTest(unittest.TestCase):
    def test_liggghts_local_contact_dump_converts_to_direct_contact_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            particles_path = root / "particles.csv"
            local_dump = root / "stage2_contacts_100.local"
            contacts_path = root / "stage2_rho072_contacts.csv"
            write_particles(particles_path)
            local_dump.write_text(
                "ITEM: TIMESTEP\n"
                "100\n"
                "ITEM: NUMBER OF ENTRIES\n"
                "2\n"
                "ITEM: ENTRIES c_pairContacts[1] c_pairContacts[2] c_pairContacts[3] "
                "c_pairContacts[4] c_pairContacts[5] c_pairContacts[6] "
                "c_pairContacts[7] c_pairContacts[8] c_pairContacts[9] "
                "c_pairContacts[10] c_pairContacts[11] c_pairContacts[12] c_pairContacts[13]\n"
                "1 2 0 20 0 0 20 0 0 0.0002 0.0009 0 0\n"
                "1 3 0 5 8 0 4.8 8.0 0 0.0001 0.00045 0.00075 0\n",
                encoding="utf-8",
            )

            export_contacts(local_dump, particles_path, "stage2_rho072", contacts_path)
            particles = read_particles(particles_path)
            contacts = read_contacts(contacts_path, particles)
            metrics = summarize_contact_network(particles, contacts, width_um=40, height_um=40)

            self.assertEqual(len(contacts), 2)
            self.assertEqual(contacts[0].source, "liggghts_pair_gran_local")
            self.assertAlmostEqual(contacts[0].overlap_um, 2.0)
            self.assertEqual(metrics["direct_contact_force_fraction"], 1.0)

    def test_direct_contact_force_snapshot_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            particles_path = root / "particles.csv"
            contacts_path = root / "contacts.csv"
            write_particles(particles_path)
            contacts_path.write_text(
                "i,j,force_x,force_y,normal_force,source\n"
                "1,2,2,0,2,solver\n"
                "1,3,1,1.5,1.8,solver\n"
                "2,3,-1,1.5,1.8,solver\n",
                encoding="utf-8",
            )

            particles = read_particles(particles_path)
            contacts = read_contacts(contacts_path, particles)
            metrics = summarize_contact_network(particles, contacts, width_um=40, height_um=40)

            self.assertEqual(len(contacts), 3)
            self.assertEqual(metrics["direct_contact_force_fraction"], 1.0)
            self.assertGreater(metrics["virial_von_mises"], 0.0)
            self.assertGreater(metrics["fabric_anisotropy"], 0.0)

    def test_stage_series_uses_direct_contact_force_files_when_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_dir = root / "DEM"
            contact_dir = root / "contacts"
            outdir = root / "series"
            snapshot_dir.mkdir()
            contact_dir.mkdir()
            stages = [
                ("stage0_preload", 0.0, 0.56, 50.0, 0.0),
                ("stage1_rho065", 45.0, 0.65, 42.0, 2.0),
                ("stage2_rho072", 130.0, 0.72, 36.0, 3.5),
            ]
            pressure_curve = snapshot_dir / "pressure_density_curve.csv"
            pressure_curve.write_text(
                "stage_id,pressure_mpa,actual_rho_total,target_rho_total,current_height_um\n"
                + "\n".join(f"{stage},{pressure},{rho},{rho},{height}" for stage, pressure, rho, height, _ in stages)
                + "\n",
                encoding="utf-8",
            )
            for index, (stage, _, _, _, compression) in enumerate(stages):
                write_stage_particles(snapshot_dir / f"dem_fem_handoff_{stage}.csv", compression)
                write_stage_contacts(contact_dir / f"{stage}_contacts.csv", force_scale=1.0 + index)

            process_stage_series(
                snapshot_dir=snapshot_dir,
                pressure_curve=pressure_curve,
                outdir=outdir,
                contact_dir=contact_dir,
                width_um=40.0,
            )
            metrics = read_csv(outdir / "series_network_metrics.csv")
            contacts = read_csv(outdir / "stage_details" / "stage2_rho072_contacts.csv")

            self.assertTrue(all(row["contact_source"] == "direct" for row in metrics))
            self.assertTrue(all(float(row["direct_contact_force_fraction"]) == 1.0 for row in metrics))
            self.assertTrue(all(row["source"] == "solver" for row in contacts))


def write_particles(path: Path) -> None:
    path.write_text(
        "particle_id,x_um,y_um,r_um,material\n"
        "1,0,0,10,Al\n"
        "2,18,0,10,Al\n"
        "3,9,15,10,Diamond\n",
        encoding="utf-8",
    )


def write_stage_particles(path: Path, compression: float) -> None:
    path.write_text(
        "particle_id,x_um,y_um,r_um,material\n"
        f"1,0,0,10,Al\n"
        f"2,18,0,10,Al\n"
        f"3,9,{15 - compression},10,Diamond\n"
        f"4,9,{30 - 2 * compression},10,Al\n",
        encoding="utf-8",
    )


def write_stage_contacts(path: Path, force_scale: float) -> None:
    path.write_text(
        "i,j,force_x,force_y,normal_force,source\n"
        f"1,2,{2.0 * force_scale},0,{2.0 * force_scale},solver\n"
        f"1,3,{1.0 * force_scale},{1.5 * force_scale},{1.8 * force_scale},solver\n"
        f"2,3,{-1.0 * force_scale},{1.5 * force_scale},{1.8 * force_scale},solver\n"
        f"3,4,0,{2.0 * force_scale},{2.0 * force_scale},solver\n",
        encoding="utf-8",
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
