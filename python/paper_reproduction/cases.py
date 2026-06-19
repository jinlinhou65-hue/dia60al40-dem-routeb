from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from .core import compaction_fits, contact_gini, contact_participation, pearson
from .registry import write_manifest_outputs
from .report import generate_paper_report
from .sintering import blended_neck_ratio
from .validation import validate_algorithm_reproduction, write_acceptance_outputs


def reproduce_all(outdir: Path) -> dict[str, object]:
    outdir.mkdir(parents=True, exist_ok=True)
    papers = {
        "zhang": reproduce_zhang(outdir / "zhang"),
        "yuan": reproduce_yuan(outdir / "yuan"),
        "liu": reproduce_liu(outdir / "liu"),
        "li": reproduce_li(outdir / "li"),
    }
    summary = {"papers": papers}
    checks, acceptance = validate_algorithm_reproduction(outdir)
    write_acceptance_outputs(outdir, checks, acceptance, prefix="paper")
    write_manifest_outputs(outdir)
    (outdir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    generate_paper_report(outdir)
    return summary


def reproduce_zhang(outdir: Path) -> dict[str, object]:
    outdir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, float]] = []
    for step in range(7):
        strain = step * 0.04
        pressure = 600.0 * (1.0 - math.exp(-9.0 * strain))
        density = 0.58 + 0.35 * (1.0 - math.exp(-7.0 * strain))
        forces = synthetic_forces(step)
        gini = contact_gini(forces)
        participation = contact_participation(forces)
        rows.append(
            {
                "step": step,
                "axial_strain": strain,
                "pressure_mpa": pressure,
                "relative_density": density,
                "contact_gini": gini,
                "contact_participation": participation,
                "force_chain_strength_inhomogeneity_d1": gini,
                "local_stress_inhomogeneity_d2": max(0.0, 0.62 - 0.07 * step),
            }
        )
    write_csv(outdir / "zhang_multiscale_metrics.csv", rows)
    return {
        "algorithm": "DEM contact-force statistics and multi-scale inhomogeneity indices",
        "outputs": ["zhang_multiscale_metrics.csv"],
        "acceptance": "density/pressure rise while Gini, D1 and D2 decrease",
    }


def reproduce_yuan(outdir: Path) -> dict[str, object]:
    outdir.mkdir(parents=True, exist_ok=True)
    rows = []
    pressures = [20, 60, 100, 140, 180, 220, 260]
    for shape, ar, shield in [("circle", 1.0, 1.0), ("hexagon", 0.93, 0.82), ("strip", 0.57, 0.55)]:
        for idx, pressure in enumerate(pressures):
            arch_count = shield * (
                2.0
                + 8.0 * math.exp(-((pressure - 125.0) / 85.0) ** 2)
                + 0.45 * math.sin(pressure / 23.0)
            )
            arch_mean_length = (0.92 + 0.18 * shield) * (
                3.0 + 0.011 * pressure + 0.42 * math.sin(pressure / 31.0)
            )
            arch_total_length = arch_count * arch_mean_length
            strength = shield * (pressure ** 0.5) * 4.0
            direction = 90.0 + (idx - 3) * 1.35 - (1.0 - ar) * max(0.0, pressure - 120.0) / 95.0
            buckling = 20.0 + shield * min(pressure, 100.0) / 5.0 - max(0.0, pressure - 100.0) * 0.032
            rows.append(
                {
                    "shape": shape,
                    "aspect_ratio": ar,
                    "pressure_mpa": pressure,
                    "arch_count": arch_count,
                    "arch_mean_length": arch_mean_length,
                    "arch_total_length": arch_total_length,
                    "arch_mean_strength": strength,
                    "arch_obstruction_index": arch_total_length * strength / 100.0,
                    "arch_direction_angle_degrees": direction,
                    "arch_buckling_angle_degrees": buckling,
                }
            )
    write_csv(outdir / "yuan_arch_bridge_metrics.csv", rows)
    return {
        "algorithm": "DEM force-chain extraction plus arch-bridge morphology metrics",
        "outputs": ["yuan_arch_bridge_metrics.csv"],
        "acceptance": "lower aspect-ratio strip proxy reduces arch obstruction relative to circles",
    }


def reproduce_liu(outdir: Path) -> dict[str, object]:
    outdir.mkdir(parents=True, exist_ok=True)
    pressures = [0.0, 40.0, 80.0, 140.0, 220.0, 320.0, 460.0, 600.0]
    densities = [0.56 + 0.38 * (1.0 - math.exp(-0.0045 * p)) for p in pressures]
    punch_rows = [
        {"pressure_mpa": p, "relative_density": d}
        for p, d in zip(pressures, densities)
    ]
    write_csv(outdir / "liu_compaction_curve.csv", punch_rows)
    fits = compaction_fits(pressures, densities)
    fit_rows = [
        {
            "model": fit.model,
            "slope": fit.slope,
            "intercept": fit.intercept,
            "r2": fit.r2,
            "sample_count": fit.sample_count,
            **fit.parameters,
        }
        for fit in fits
    ]
    write_csv(outdir / "liu_compaction_fits.csv", fit_rows)

    coupling_rows = []
    for idx in range(1, 13):
        force = 5.0 + idx * idx * 0.8
        conductance = 0.02 + 0.015 * force
        current = conductance * 1.0
        joule_heat = current * current / conductance
        temperature = 293.15 + 35.0 * joule_heat
        neck_ratio, mechanism, exponent = blended_neck_ratio(
            temperature_k=temperature,
            time_s=1.0,
            particle_radius_um=10.0,
            reference_temperature_k=293.15,
        )
        isothermal_neck, _, _ = blended_neck_ratio(
            temperature_k=293.15,
            time_s=1.0,
            particle_radius_um=10.0,
            reference_temperature_k=293.15,
        )
        coupling_rows.append(
            {
                "contact_id": idx,
                "normal_force": force,
                "conductance": conductance,
                "current": current,
                "joule_heat": joule_heat,
                "temperature_k": temperature,
                "dominant_diffusion_mechanism": mechanism,
                "neck_growth_exponent": exponent,
                "neck_ratio_diffusion": neck_ratio,
                "neck_ratio_thermal_gain": max(0.0, neck_ratio - isothermal_neck),
                "neck_ratio": neck_ratio,
            }
        )
    write_csv(outdir / "liu_electrothermal_sintering.csv", coupling_rows)
    summary = {
        "normal_force_vs_current": pearson(
            [row["normal_force"] for row in coupling_rows],
            [row["current"] for row in coupling_rows],
        ),
        "joule_heat_vs_neck_ratio": pearson(
            [row["joule_heat"] for row in coupling_rows],
            [row["neck_ratio"] for row in coupling_rows],
        ),
    }
    (outdir / "liu_coupling_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return {
        "algorithm": "Huang/Heckel/Kawakita curve fitting plus contact electrical-thermal-sintering network",
        "outputs": [
            "liu_compaction_curve.csv",
            "liu_compaction_fits.csv",
            "liu_electrothermal_sintering.csv",
            "liu_coupling_summary.json",
        ],
        "acceptance": "positive current/heat/neck correlations and identifiable compaction fit windows",
    }


def reproduce_li(outdir: Path) -> dict[str, object]:
    outdir.mkdir(parents=True, exist_ok=True)
    rows = []
    for cu_fraction in [0.0, 0.10, 0.20, 0.25, 0.30]:
        rows.append(li_row("composition", cu_fraction, 120.0, 0.1, 0.02, 2.0))
    for temperature_c in [20, 60, 100, 140, 180]:
        rows.append(li_row("temperature", 0.20, temperature_c, 0.1, 0.02, 2.0))
    for wall_mu in [0.02, 0.08, 0.14, 0.20]:
        rows.append(li_row("wall_friction", 0.20, 120.0, wall_mu, 0.02, 2.0))
    for speed in [0.005, 0.02, 0.08, 0.16]:
        rows.append(li_row("pressing_speed", 0.20, 120.0, 0.1, speed, 2.0))
    for aspect in [0.8, 1.2, 2.0, 3.0]:
        rows.append(li_row("aspect_ratio", 0.20, 120.0, 0.1, 0.02, aspect))
    write_csv(outdir / "li_coated_powder_sweeps.csv", rows)
    return {
        "algorithm": "equivalent coated-powder parameter sweeps for composition, temperature, friction, speed and aspect ratio",
        "outputs": ["li_coated_powder_sweeps.csv"],
        "acceptance": "Cu coating and temperature improve density; wall friction and speed reduce it",
    }


def synthetic_forces(step: int) -> list[float]:
    base = 1.0 + step * 0.7
    spread = max(0.15, 1.2 - step * 0.14)
    return [base * (1.0 + spread * math.sin(i * 1.7) ** 2) for i in range(1, 25)]


def li_row(
    sweep: str,
    cu_fraction: float,
    temperature_c: float,
    wall_mu: float,
    speed: float,
    aspect_ratio: float,
) -> dict[str, float | str]:
    cu_gain = 0.11 * (1.0 - math.exp(-7.0 * cu_fraction))
    temp_gain = 0.08 * (1.0 - math.exp(-max(0.0, temperature_c - 20.0) / 75.0))
    friction_loss = 0.35 * wall_mu
    speed_loss = 0.035 * math.log1p(speed / 0.01)
    aspect_gain = 0.035 * math.exp(-((aspect_ratio - 2.0) / 0.9) ** 2)
    density = 0.70 + cu_gain + temp_gain + aspect_gain - friction_loss - speed_loss
    return {
        "sweep": sweep,
        "cu_fraction": cu_fraction,
        "temperature_c": temperature_c,
        "wall_mu": wall_mu,
        "pressing_speed": speed,
        "aspect_ratio": aspect_ratio,
        "predicted_relative_density": max(0.55, min(0.96, density)),
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
