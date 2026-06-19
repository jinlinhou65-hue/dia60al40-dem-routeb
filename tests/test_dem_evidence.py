from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = REPO_ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from paper_reproduction import validate_dem_evidence, write_dem_evidence_outputs


class DemEvidenceTest(unittest.TestCase):
    def test_complete_stage_artifact_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dem_dir = root / "DEM"
            outdir = dem_dir / "paper_reproduction"
            create_complete_artifact(root, dem_dir, outdir)

            checks, summary = validate_dem_evidence(dem_dir)
            outputs = write_dem_evidence_outputs(dem_dir)
            self.assertEqual(summary[0]["status"], "pass")
            self.assertTrue(all(check["status"] == "pass" for check in checks))
            self.assertTrue(outputs["checks"].exists())
            self.assertTrue(outputs["summary"].exists())
            self.assertTrue(outputs["report"].exists())

    def test_cli_fails_incomplete_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "validate_dem_evidence.py"),
                    "--dem-dir",
                    str(Path(tmp) / "DEM"),
                    "--outdir",
                    str(Path(tmp) / "evidence"),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertTrue((Path(tmp) / "evidence" / "dem_evidence_summary.csv").exists())


def create_complete_artifact(root: Path, dem_dir: Path, outdir: Path) -> None:
    stages = [
        ("stage0_preload", 0.0, 0.56, 50.0),
        ("stage1_rho065", 35.0, 0.65, 43.0),
        ("stage2_rho072", 80.0, 0.72, 38.0),
        ("stage3_rho080", 145.0, 0.80, 34.0),
        ("stage4_rho088", 220.0, 0.88, 30.0),
        ("stage5_rho095", 310.0, 0.95, 27.0),
    ]
    dem_dir.mkdir()
    outdir.mkdir()
    (dem_dir / "plots").mkdir()
    (root / "in.dia60al40_dem_staged.rendered.liggghts").write_text(
        "variable        topVel equal 50\nvariable        dt equal 1.0e-8\n",
        encoding="utf-8",
    )
    (dem_dir / "model_parameters.csv").write_text(
        "parameter,value\nAl_count,2\ndiamond_count_DS,1\ndiamond_count_DL,1\n",
        encoding="utf-8",
    )
    (dem_dir / "pressure_density_curve.csv").write_text(
        "stage_id,pressure_mpa,actual_rho_total,target_rho_total,current_height_um\n"
        + "\n".join(f"{stage},{pressure},{rho},{rho},{height}" for stage, pressure, rho, height in stages)
        + "\n",
        encoding="utf-8",
    )
    (dem_dir / "pressure_density_summary.csv").write_text(
        "target_rho,p_target_mpa,reference_pressure_mpa,judgement\n0.95,310,200,high\n",
        encoding="utf-8",
    )
    (dem_dir / "plots" / "pressure_density_curve.png").write_bytes(b"png")
    for stage, *_ in stages:
        write_particles(dem_dir / f"dem_fem_handoff_{stage}.csv")
        (dem_dir / f"{stage}.restart").write_text("restart\n", encoding="utf-8")
        (dem_dir / f"{stage}_100.dump").write_text("dump\n", encoding="utf-8")
    write_paper_outputs(outdir, stages)


def write_particles(path: Path) -> None:
    path.write_text(
        "particle_id,x_um,y_um,r_um,material\n"
        "1,0,0,10,Al\n2,18,0,10,Al\n3,9,15,10,Diamond\n4,9,30,10,Al\n",
        encoding="utf-8",
    )


def write_paper_outputs(outdir: Path, stages: list[tuple[str, float, float, float]]) -> None:
    details = outdir / "stage_details"
    details.mkdir()
    (outdir / "series_network_metrics.csv").write_text(
        "stage_id,pressure_mpa,actual_rho_total,contact_source,direct_contact_force_fraction,"
        "contact_gini,coupling_particle_heat_vs_neck_ratio,virial_stress_xx,virial_stress_yy,"
        "virial_stress_xy,virial_mean_pressure,virial_von_mises,fabric_tensor_xx,"
        "fabric_tensor_yy,fabric_tensor_xy,fabric_anisotropy\n"
        + "\n".join(
            f"{stage},{pressure},{rho},inferred,0,{0.5 - i * 0.05},0.9,"
            f"{1 + i},{2 + i},0.1,{1.5 + i},{3 + i},0.45,0.55,0.02,0.12"
            for i, (stage, pressure, rho, _) in enumerate(stages)
        )
        + "\n",
        encoding="utf-8",
    )
    (outdir / "series_compaction_fits.csv").write_text(
        "model,r2\nHeckel,0.99\nKawakita,0.98\n",
        encoding="utf-8",
    )
    (outdir / "series_acceptance_summary.csv").write_text(
        "paper,status,pass,review,missing,mismatch,check_count\n"
        "Li,pass,1,0,0,0,1\nLiu,pass,5,0,0,0,5\n"
        "Yuan,pass,3,0,0,0,3\nZhang,pass,6,0,0,0,6\n",
        encoding="utf-8",
    )
    (outdir / "series_report.md").write_text("# series report\n", encoding="utf-8")
    for stage, *_ in stages:
        (details / f"{stage}_electrothermal_contacts.csv").write_text(
            "i,j,normal_force,conductance,current,abs_current,joule_heat\n1,2,1,0.1,0.1,0.1,0.01\n",
            encoding="utf-8",
        )
        (details / f"{stage}_electrothermal_particles.csv").write_text(
            "particle_id,potential,heat_source,temperature_k,dominant_diffusion_mechanism,neck_growth_exponent,neck_ratio_diffusion,neck_ratio_thermal_gain,neck_ratio_proxy\n"
            "1,0,0.01,294.15,surface,7,0.04,0.002,0.04\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
