from __future__ import annotations

import csv
import json
import math
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
    build_manifest,
    compaction_fits,
    get_paper_targets,
    infer_contacts,
    process_stage_series,
    read_particles,
    reproduce_all,
    run_electrothermal_network,
    summarize_contact_network,
    trend_direction,
    validate_algorithm_reproduction,
    validate_stage_series,
)
from dem_case_config import DIAMOND_CASES, refined_diamond_case
from dem_case_geometry import al_count, total_solid_area_um2


class PaperReproductionTest(unittest.TestCase):
    def test_heckel_and_kawakita_fits_recover_synthetic_parameters(self):
        pressures = [0.0, 40.0, 80.0, 120.0, 180.0, 260.0]
        heckel_k = 0.004
        heckel_a = 0.82
        heckel_densities = [
            1.0 - math.exp(-(heckel_k * p + heckel_a))
            for p in pressures
        ]
        heckel = {fit.model: fit for fit in compaction_fits(pressures, heckel_densities)}["Heckel"]
        self.assertAlmostEqual(heckel.parameters["K"], heckel_k, places=9)
        self.assertAlmostEqual(heckel.parameters["A"], heckel_a, places=9)
        self.assertGreater(heckel.r2, 0.999999)

        d0 = 0.58
        a = 0.42
        b = 0.018
        kawakita_densities = []
        for p in pressures:
            c = a * b * p / (1.0 + b * p)
            kawakita_densities.append(d0 / (1.0 - c))
        kawakita = {fit.model: fit for fit in compaction_fits(pressures, kawakita_densities)}["Kawakita"]
        self.assertAlmostEqual(kawakita.parameters["a"], a, places=9)
        self.assertAlmostEqual(kawakita.parameters["b"], b, places=9)
        self.assertGreater(kawakita.r2, 0.999999)

    def test_reproduce_all_writes_expected_paper_outputs_and_trends(self):
        with tempfile.TemporaryDirectory() as tmp:
            outdir = Path(tmp) / "paper"
            summary = reproduce_all(outdir)
            self.assertEqual(set(summary["papers"]), {"zhang", "yuan", "liu", "li"})
            self.assertTrue((outdir / "summary.json").exists())
            self.assertTrue((outdir / "paper_reproduction_manifest.json").exists())
            self.assertTrue((outdir / "paper_reproduction_manifest.md").exists())
            self.assertTrue((outdir / "paper_reproduction_report.md").exists())
            self.assertTrue((outdir / "plots" / "zhang_density_pressure.svg").exists())
            self.assertTrue((outdir / "plots" / "yuan_arch_count_by_shape.svg").exists())
            self.assertTrue((outdir / "plots" / "liu_compaction_curve.svg").exists())
            self.assertTrue((outdir / "plots" / "li_composition_density.svg").exists())
            self.assertTrue((outdir / "paper_trend_checks.json").exists())
            self.assertTrue((outdir / "paper_acceptance_summary.csv").exists())

            zhang = read_csv(outdir / "zhang" / "zhang_multiscale_metrics.csv")
            self.assertGreater(float(zhang[-1]["relative_density"]), float(zhang[0]["relative_density"]))
            self.assertLess(float(zhang[-1]["contact_gini"]), float(zhang[0]["contact_gini"]))
            self.assertLess(
                float(zhang[-1]["local_stress_inhomogeneity_d2"]),
                float(zhang[0]["local_stress_inhomogeneity_d2"]),
            )

            yuan = read_csv(outdir / "yuan" / "yuan_arch_bridge_metrics.csv")
            circle_arch = max(float(row["arch_count"]) for row in yuan if row["shape"] == "circle")
            strip_arch = max(float(row["arch_count"]) for row in yuan if row["shape"] == "strip")
            self.assertGreater(circle_arch, strip_arch)

            liu_summary = json.loads(
                (outdir / "liu" / "liu_coupling_summary.json").read_text(encoding="utf-8")
            )
            self.assertGreater(liu_summary["normal_force_vs_current"], 0.0)
            self.assertGreater(liu_summary["joule_heat_vs_neck_ratio"], 0.0)
            self.assertGreater(len(read_csv(outdir / "liu" / "liu_compaction_fits.csv")), 1)

            li = read_csv(outdir / "li" / "li_coated_powder_sweeps.csv")
            low_cu = next(row for row in li if row["sweep"] == "composition" and row["cu_fraction"] == "0.0")
            high_cu = next(row for row in li if row["sweep"] == "composition" and row["cu_fraction"] == "0.25")
            self.assertGreater(
                float(high_cu["predicted_relative_density"]),
                float(low_cu["predicted_relative_density"]),
            )

            checks = json.loads((outdir / "paper_trend_checks.json").read_text(encoding="utf-8"))
            acceptance = read_csv(outdir / "paper_acceptance_summary.csv")
            self.assertTrue(any(row["paper"] == "Li" and row["status"] == "pass" for row in acceptance))
            self.assertTrue(
                any(
                    check["paper"] == "Yuan"
                    and "circle" in check["label"]
                    and check["status"] == "pass"
                    for check in checks
                )
            )
            self.assertTrue(
                any(
                    check["paper"] == "Li"
                    and check["field"] == "composition.cu_fraction"
                    and check["status"] == "pass"
                    for check in checks
                )
            )

    def test_cli_runs_single_paper(self):
        with tempfile.TemporaryDirectory() as tmp:
            outdir = Path(tmp) / "cli"
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "run_paper_algorithm_reproduction.py"),
                    "--paper",
                    "liu",
                    "--outdir",
                    str(outdir),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn("liu", result.stdout)
            self.assertTrue((outdir / "liu" / "liu_compaction_fits.csv").exists())
            self.assertTrue((outdir / "paper_reproduction_manifest.json").exists())
            self.assertTrue((outdir / "paper_reproduction_report.md").exists())
            self.assertTrue((outdir / "plots" / "liu_compaction_curve.svg").exists())
            self.assertFalse((outdir / "plots" / "zhang_density_pressure.svg").exists())
            self.assertTrue((outdir / "paper_acceptance_summary.csv").exists())
            manifest = json.loads(
                (outdir / "paper_reproduction_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual([paper["key"] for paper in manifest["papers"]], ["liu"])
            acceptance = read_csv(outdir / "paper_acceptance_summary.csv")
            self.assertEqual([row["paper"] for row in acceptance], ["Liu"])

    def test_paper_target_registry_covers_all_papers_and_outputs_manifest(self):
        targets = get_paper_targets()
        self.assertEqual({target.key for target in targets}, {"zhang", "yuan", "liu", "li"})
        self.assertTrue(
            any("contact-force Gini index" in target.paper_methods for target in targets)
        )

        manifest = build_manifest(["zhang", "yuan"])
        self.assertEqual([paper["key"] for paper in manifest["papers"]], ["zhang", "yuan"])
        zhang = manifest["papers"][0]
        self.assertIn("contact_gini decreasing", zhang["acceptance_gates"])
        self.assertIn("series_network_metrics.csv", zhang["expected_outputs"])

    def test_generate_manifest_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            outdir = Path(tmp) / "manifest"
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "generate_paper_reproduction_manifest.py"),
                    "--paper",
                    "yuan",
                    "--outdir",
                    str(outdir),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn("paper_reproduction_manifest.json", result.stdout)
            manifest = json.loads(
                (outdir / "paper_reproduction_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual([paper["key"] for paper in manifest["papers"]], ["yuan"])
            self.assertTrue((outdir / "paper_reproduction_manifest.md").exists())

    def test_render_dem_deck_supports_fast_demo_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            rendered = Path(tmp) / "demo.liggghts"
            subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "python" / "render_dem_deck.py"),
                    "--input",
                    str(REPO_ROOT / "liggghts" / "in.dia60al40_dem_staged.liggghts"),
                    "--output",
                    str(rendered),
                    "--diamond-size-case",
                    "C",
                    "--seed-index",
                    "0",
                    "--particle-count-scale",
                    "2",
                    "--top-vel-cm-s",
                    "50",
                    "--initial-settle-steps",
                    "20",
                    "--stage-settle-steps",
                    "30",
                    "--final-settle-steps",
                    "40",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=True,
            )
            text = rendered.read_text(encoding="utf-8")
            self.assertIn("variable        topVel equal 50", text)
            self.assertIn("particle_count_scale,2,1", text)
            self.assertIn("particle_count_total", text)
            self.assertIn("run             20", text)
            self.assertIn("run             30", text)
            self.assertIn("run             40", text)
            self.assertIn("compute         pairContacts all pair/gran/local", text)
            for stage in [
                "stage0_preload",
                "stage1_rho065",
                "stage2_rho072",
                "stage3_rho080",
                "stage4_rho088",
                "stage5_rho095",
            ]:
                self.assertIn(f"DEM/{stage}_contacts_*.local", text)

            base = DIAMOND_CASES["C"]
            refined = refined_diamond_case(base, 2)
            self.assertEqual(refined.ds_count, base.ds_count * 2)
            self.assertEqual(refined.dl_count, base.dl_count * 2)
            self.assertGreater(al_count(refined), al_count(base))
            self.assertAlmostEqual(
                total_solid_area_um2(refined),
                total_solid_area_um2(base),
                delta=total_solid_area_um2(base) * 0.02,
            )

    def test_particle_snapshot_network_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            particles_path = Path(tmp) / "particles.csv"
            particles_path.write_text(
                "particle_id,x_um,y_um,r_um,material\n"
                "1,0,0,10,Al\n"
                "2,18,0,10,Al\n"
                "3,9,15,10,Diamond\n"
                "4,9,30,10,Al\n",
                encoding="utf-8",
            )
            particles = read_particles(particles_path)
            contacts = infer_contacts(particles, normal_stiffness=2.0)
            metrics = summarize_contact_network(particles, contacts, width_um=40, height_um=50)
            particle_fields, contact_fields = run_electrothermal_network(particles, contacts)

            self.assertGreaterEqual(len(contacts), 4)
            self.assertGreater(metrics["mean_coordination"], 1.0)
            self.assertGreaterEqual(metrics["arch_count"], 1)
            self.assertIn("virial_stress_yy", metrics)
            self.assertIn("fabric_anisotropy", metrics)
            self.assertGreater(metrics["virial_von_mises"], 0.0)
            self.assertTrue(any(row["joule_heat"] > 0 for row in contact_fields))
            self.assertTrue(any(row["temperature_k"] > 293.15 for row in particle_fields))

    def test_process_particle_snapshot_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            particles_path = Path(tmp) / "particles.csv"
            outdir = Path(tmp) / "out"
            particles_path.write_text(
                "particle_id,x_um,y_um,r_um,material\n"
                "1,0,0,10,Al\n"
                "2,18,0,10,Al\n"
                "3,9,15,10,Diamond\n"
                "4,9,30,10,Al\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "process_particle_snapshot.py"),
                    "--particles",
                    str(particles_path),
                    "--outdir",
                    str(outdir),
                    "--width-um",
                    "40",
                    "--height-um",
                    "50",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn("contact_count", result.stdout)
            self.assertTrue((outdir / "contacts_inferred.csv").exists())
            self.assertTrue((outdir / "electrothermal_particles.csv").exists())
            summary = json.loads((outdir / "snapshot_summary.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(summary["metrics"]["arch_count"], 1)

    def test_stage_series_processing_outputs_fits_and_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_dir = root / "DEM"
            outdir = root / "series"
            snapshot_dir.mkdir()
            stages = [
                ("stage0_preload", 0.0, 0.56, 50.0, 0.0),
                ("stage1_rho065", 45.0, 0.65, 42.0, 2.0),
                ("stage2_rho072", 130.0, 0.72, 36.0, 3.5),
                ("stage3_rho080", 260.0, 0.80, 31.0, 5.0),
            ]
            pressure_curve = snapshot_dir / "pressure_density_curve.csv"
            pressure_curve.write_text(
                "stage_id,pressure_mpa,actual_rho_total,target_rho_total,current_height_um\n"
                + "\n".join(f"{stage},{pressure},{rho},{rho},{height}" for stage, pressure, rho, height, _ in stages)
                + "\n",
                encoding="utf-8",
            )
            for stage, _, _, _, compression in stages:
                write_stage_particles(snapshot_dir / f"dem_fem_handoff_{stage}.csv", compression)

            summary = process_stage_series(
                snapshot_dir=snapshot_dir,
                pressure_curve=pressure_curve,
                outdir=outdir,
                width_um=40.0,
            )

            self.assertEqual(summary["stage_count"], 4)
            metrics = read_csv(outdir / "series_network_metrics.csv")
            fits = read_csv(outdir / "series_compaction_fits.csv")
            acceptance = read_csv(outdir / "series_acceptance_summary.csv")
            trend_checks = json.loads((outdir / "series_trend_checks.json").read_text(encoding="utf-8"))
            report = (outdir / "series_report.md").read_text(encoding="utf-8")
            self.assertEqual(len(metrics), 4)
            self.assertIn("virial_stress_yy", metrics[0])
            self.assertIn("fabric_anisotropy", metrics[0])
            self.assertTrue(any(row["model"] == "Heckel" for row in fits))
            self.assertTrue(any(row["paper"] == "Zhang" for row in acceptance))
            self.assertTrue(
                any(
                    check["paper"] == "Zhang"
                    and check["field"] == "pressure_mpa"
                    and check["status"] == "pass"
                    for check in trend_checks
                )
            )
            self.assertIn("Acceptance Summary", report)
            self.assertIn("Zhang", report)
            self.assertIn("Yuan", report)
            self.assertTrue((outdir / "stage_details" / "stage3_rho080_contacts.csv").exists())

    def test_stage_series_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_dir = root / "DEM"
            outdir = root / "series_cli"
            snapshot_dir.mkdir()
            stages = [
                ("stage0_preload", 0.0, 0.56, 50.0, 0.0),
                ("stage1_rho065", 45.0, 0.65, 42.0, 2.0),
                ("stage2_rho072", 130.0, 0.72, 36.0, 3.5),
                ("stage3_rho080", 260.0, 0.80, 31.0, 5.0),
            ]
            pressure_curve = snapshot_dir / "pressure_density_curve.csv"
            pressure_curve.write_text(
                "stage_id,pressure_mpa,actual_rho_total,target_rho_total,current_height_um\n"
                + "\n".join(f"{stage},{pressure},{rho},{rho},{height}" for stage, pressure, rho, height, _ in stages)
                + "\n",
                encoding="utf-8",
            )
            for stage, _, _, _, compression in stages:
                write_stage_particles(snapshot_dir / f"dem_fem_handoff_{stage}.csv", compression)

            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "process_stage_series.py"),
                    "--snapshot-dir",
                    str(snapshot_dir),
                    "--pressure-curve",
                    str(pressure_curve),
                    "--outdir",
                    str(outdir),
                    "--width-um",
                    "40",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn("stage_count", result.stdout)
            self.assertTrue((outdir / "series_summary.json").exists())
            self.assertTrue((outdir / "series_trend_checks.json").exists())

    def test_validation_helpers_classify_trends_and_paper_gates(self):
        self.assertEqual(trend_direction([1.0, 2.0, 3.0]), "increasing")
        self.assertEqual(trend_direction([3.0, 2.0, 1.0]), "decreasing")
        self.assertEqual(trend_direction([1.0, 1.0]), "flat")
        self.assertIsNone(trend_direction([1.0]))

        metric_rows = [
            {
                "pressure_mpa": 0.0,
                "actual_rho_total": 0.56,
                "mean_coordination": 1.0,
                "contact_participation": 0.40,
                "force_chain_strength_inhomogeneity_d1": 0.50,
                "local_stress_inhomogeneity_d2": 0.60,
                "arch_count": 1,
                "arch_mean_strength": 10.0,
                "arch_mean_direction_angle_degrees": 88.0,
                "coupling_normal_force_vs_abs_current": 0.2,
                "coupling_normal_force_vs_joule_heat": 0.3,
                "coupling_particle_heat_vs_neck_ratio": 0.9,
                "contact_gini": 0.5,
            },
            {
                "pressure_mpa": 100.0,
                "actual_rho_total": 0.70,
                "mean_coordination": 2.0,
                "contact_participation": 0.60,
                "force_chain_strength_inhomogeneity_d1": 0.20,
                "local_stress_inhomogeneity_d2": 0.30,
                "arch_count": 2,
                "arch_mean_strength": 20.0,
                "arch_mean_direction_angle_degrees": 91.0,
                "coupling_normal_force_vs_abs_current": 0.4,
                "coupling_normal_force_vs_joule_heat": 0.5,
                "coupling_particle_heat_vs_neck_ratio": 0.95,
                "contact_gini": 0.3,
            },
        ]
        fit_rows = [{"model": "Heckel", "r2": 0.99}, {"model": "Kawakita", "r2": 0.98}]
        checks, summary = validate_stage_series(metric_rows, fit_rows)

        self.assertTrue(any(check["field"] == "actual_rho_total" and check["status"] == "pass" for check in checks))
        self.assertTrue(any(row["paper"] == "Zhang" and row["status"] == "pass" for row in summary))
        self.assertTrue(any(row["paper"] == "Liu" and row["status"] == "pass" for row in summary))

    def test_algorithm_acceptance_detects_li_and_yuan_trends(self):
        with tempfile.TemporaryDirectory() as tmp:
            outdir = Path(tmp) / "paper"
            reproduce_all(outdir)
            checks, summary = validate_algorithm_reproduction(outdir)

            self.assertTrue(any(row["paper"] == "Li" and row["status"] == "pass" for row in summary))
            self.assertTrue(any(row["paper"] == "Yuan" and row["status"] == "pass" for row in summary))
            self.assertTrue(
                any(
                    check["paper"] == "Li"
                    and check["label"] == "wall friction reduces density"
                    and check["status"] == "pass"
                    for check in checks
                )
            )
            self.assertTrue(
                any(
                    check["paper"] == "Li"
                    and check["label"] == "aspect ratio near 2 is favorable"
                    and check["status"] == "pass"
                    for check in checks
                )
            )

    def test_real_dem_workflow_runs_paper_stage_series_postprocess(self):
        workflow = (REPO_ROOT / ".github" / "workflows" / "dia60al40-dem.yml").read_text(
            encoding="utf-8"
        )
        paper_workflow = (
            REPO_ROOT / ".github" / "workflows" / "paper-algorithm-reproduction.yml"
        ).read_text(encoding="utf-8")
        cloud_script = (REPO_ROOT / "scripts" / "cloud_run_liggghts_routeb.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("github.event_name == 'workflow_dispatch' && github.run_id || 'push'", workflow)
        self.assertIn("cancel-in-progress: ${{ github.event_name != 'workflow_dispatch' }}", workflow)
        self.assertIn("runtime_profile", workflow)
        self.assertIn("allow_evidence_mismatch", workflow)
        self.assertIn("particle_count_scale_json", workflow)
        self.assertIn("--particle-count-scale", workflow)
        self.assertIn("pscale${{ matrix.particle_count_scale }}", workflow)
        self.assertIn("--allow-mismatch", workflow)
        self.assertIn("--top-vel-cm-s 50", workflow)
        self.assertIn("dem_seed: ${{ fromJSON(inputs.dem_seed_json || '[\"0\"]') }}", workflow)
        self.assertIn(
            "diamond_size_case: ${{ fromJSON(inputs.diamond_size_case_json || '[\"C\"]') }}",
            workflow,
        )
        for text in (workflow, cloud_script):
            self.assertIn("scripts/process_stage_series.py", text)
            self.assertIn("scripts/validate_dem_evidence.py", text)
            self.assertIn("dem_evidence_summary.csv", text)
            self.assertIn("liggghts/DEM/pressure_density_curve.csv", text)
            self.assertIn("liggghts/DEM/paper_reproduction", text)
            self.assertIn("--width-um 400", text)
        self.assertIn("python/paper_reproduction/registry.py", paper_workflow)
        self.assertIn("python/paper_reproduction/report.py", paper_workflow)
        self.assertIn("scripts/generate_paper_reproduction_manifest.py", paper_workflow)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_stage_particles(path: Path, compression: float) -> None:
    path.write_text(
        "particle_id,x_um,y_um,r_um,material\n"
        f"1,0,0,10,Al\n"
        f"2,18,0,10,Al\n"
        f"3,9,{15 - compression},10,Diamond\n"
        f"4,9,{30 - 2 * compression},10,Al\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
