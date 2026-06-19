from __future__ import annotations

import math


COMPOSITIONS = [
    ("Fe", 0.0),
    ("Cu10@Fe90", 0.10),
    ("Cu20@Fe80", 0.20),
    ("Cu25@Fe75", 0.25),
    ("Cu30@Fe70", 0.30),
]


def li_sweep_rows() -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
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
    return rows


def li_core_shell_rows() -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    for label, cu_fraction in COMPOSITIONS:
        shell_ratio = cu_fraction
        flow = 0.62 + 1.15 * cu_fraction
        interface_friction = max(0.18, 0.82 - 1.55 * cu_fraction)
        wall_friction = max(0.12, 0.70 - 1.35 * cu_fraction)
        stress_uniformity = 0.30 - 0.58 * cu_fraction + 1.25 * (cu_fraction - 0.225) ** 2
        mean_stress = 615.0 - 135.0 * math.exp(-((cu_fraction - 0.225) / 0.13) ** 2)
        relative_density = 0.928 + 0.048 * (1.0 - math.exp(-6.5 * cu_fraction))
        rows.append(
            {
                "composition": label,
                "cu_fraction": cu_fraction,
                "fe_fraction": 1.0 - cu_fraction,
                "shell_thickness_ratio": shell_ratio,
                "relative_density_600mpa": min(relative_density, 0.976),
                "mean_von_mises_mpa": mean_stress,
                "stress_uniformity_index": max(0.10, stress_uniformity),
                "plastic_strain_proxy": 0.12 + 0.58 * cu_fraction,
                "interface_friction_proxy": interface_friction,
                "wall_friction_proxy": wall_friction,
                "flow_factor": flow,
            }
        )
    return rows


def li_temperature_pressure_rows() -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    for material, cu_fraction in [("Fe", 0.0), ("Cu20@Fe80", 0.20)]:
        for pressure in [100.0, 300.0, 500.0, 600.0]:
            for temperature in [20.0, 80.0, 140.0, 200.0, 300.0]:
                rows.append(li_temperature_pressure_row(material, cu_fraction, pressure, temperature))
    return rows


def li_particle_count_convergence_rows() -> list[dict[str, float | str]]:
    densities = {
        300.0: {100: 0.90020, 197: 0.91810},
        500.0: {100: 0.94854, 197: 0.95067},
        600.0: {100: 0.95994, 197: 0.96000},
    }
    rows: list[dict[str, float | str]] = []
    for pressure, by_count in densities.items():
        reference = by_count[197]
        for particle_count, density in by_count.items():
            rows.append(
                {
                    "pressure_mpa": pressure,
                    "particle_count": particle_count,
                    "relative_density": density,
                    "density_difference_from_197": abs(reference - density),
                    "rearrangement_contribution": max(0.0, 0.026 * (1.0 - pressure / 650.0)),
                    "plastic_deformation_contribution": 0.05 + 0.00012 * pressure,
                }
            )
    return rows


def li_row(
    sweep: str,
    cu_fraction: float,
    temperature_c: float,
    wall_mu: float,
    speed: float,
    aspect_ratio: float,
) -> dict[str, float | str]:
    cu_gain = 0.11 * (1.0 - math.exp(-7.0 * cu_fraction))
    temp_gain = temperature_gain(temperature_c, pressure_mpa=500.0)
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
        "interface_friction_proxy": max(0.18, 0.82 - 1.55 * cu_fraction),
        "wall_friction_proxy": max(0.12, 0.70 - 1.35 * cu_fraction + 0.45 * wall_mu),
        "flow_factor": 0.62 + 1.15 * cu_fraction - 0.35 * wall_mu,
        "thermal_softening_gain": temp_gain,
        "thermal_expansion_penalty": thermal_expansion_penalty(cu_fraction, temperature_c),
        "max_von_mises_mpa": 575.0 + 15.0 * aspect_ratio + 120.0 * wall_mu,
        "predicted_relative_density": max(0.55, min(0.96, density)),
    }


def li_temperature_pressure_row(
    material: str,
    cu_fraction: float,
    pressure_mpa: float,
    temperature_c: float,
) -> dict[str, float | str]:
    pressure_density = 0.81 + 0.15 * (1.0 - math.exp(-0.006 * pressure_mpa))
    coating_gain = 0.018 * (1.0 - math.exp(-7.0 * cu_fraction))
    softening = temperature_gain(temperature_c, pressure_mpa=pressure_mpa)
    expansion = thermal_expansion_penalty(cu_fraction, temperature_c)
    return {
        "material": material,
        "pressure_mpa": pressure_mpa,
        "temperature_c": temperature_c,
        "relative_density": min(0.985, pressure_density + coating_gain + softening - expansion),
        "thermal_softening_gain": softening,
        "thermal_expansion_penalty": expansion,
        "temperature_effect_attenuation": pressure_temperature_attenuation(pressure_mpa),
    }


def temperature_gain(temperature_c: float, *, pressure_mpa: float) -> float:
    thermal_span = max(0.0, temperature_c - 20.0)
    return 0.070 * (1.0 - math.exp(-thermal_span / 95.0)) * pressure_temperature_attenuation(pressure_mpa)


def pressure_temperature_attenuation(pressure_mpa: float) -> float:
    if pressure_mpa <= 500.0:
        return 1.0 - 0.25 * pressure_mpa / 500.0
    return max(0.35, 0.75 - 0.002 * (pressure_mpa - 500.0))


def thermal_expansion_penalty(cu_fraction: float, temperature_c: float) -> float:
    thermal_span = max(0.0, temperature_c - 140.0)
    return (0.002 + 0.010 * cu_fraction) * (1.0 - math.exp(-thermal_span / 110.0))
