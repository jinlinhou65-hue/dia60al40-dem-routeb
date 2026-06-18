from __future__ import annotations

import math
from dataclasses import dataclass


GAS_CONSTANT_J_PER_MOL_K = 8.314462618


@dataclass(frozen=True)
class SinteringLaw:
    name: str
    growth_exponent: float
    particle_size_exponent: float
    activation_energy_j_mol: float
    rate_prefactor: float
    description: str


SINTERING_LAWS: dict[str, SinteringLaw] = {
    "volume": SinteringLaw(
        name="volume",
        growth_exponent=5.0,
        particle_size_exponent=3.0,
        activation_energy_j_mol=240_000.0,
        rate_prefactor=3.0e-10,
        description="Wilson-Shewmon style initial-stage volume diffusion",
    ),
    "grain_boundary": SinteringLaw(
        name="grain_boundary",
        growth_exponent=6.0,
        particle_size_exponent=4.0,
        activation_energy_j_mol=180_000.0,
        rate_prefactor=8.0e-10,
        description="Johnson/Coble style grain-boundary diffusion",
    ),
    "surface": SinteringLaw(
        name="surface",
        growth_exponent=7.0,
        particle_size_exponent=4.0,
        activation_energy_j_mol=120_000.0,
        rate_prefactor=1.4e-9,
        description="Kuczynski style initial-stage surface diffusion",
    ),
    "coble": SinteringLaw(
        name="coble",
        growth_exponent=1.0,
        particle_size_exponent=4.0,
        activation_energy_j_mol=180_000.0,
        rate_prefactor=2.2e-5,
        description="middle-stage Coble grain-boundary diffusion rate",
    ),
    "nabarro_herring": SinteringLaw(
        name="nabarro_herring",
        growth_exponent=1.0,
        particle_size_exponent=3.0,
        activation_energy_j_mol=240_000.0,
        rate_prefactor=8.0e-6,
        description="middle-stage Nabarro-Herring lattice diffusion rate",
    ),
}


def sintering_neck_ratio(
    *,
    temperature_k: float,
    time_s: float,
    particle_radius_um: float,
    law: str = "surface",
    initial_neck_ratio: float = 0.02,
    reference_temperature_k: float = 293.15,
    reference_radius_um: float = 10.0,
    max_neck_ratio: float = 0.8,
    rate_scale: float = 1.0,
) -> float:
    """Return x/a from a normalized neck-growth law.

    The Liu review gives the physical law families and exponents but not the
    material constants for this Dia/Al run. This routine keeps the exponents,
    Arrhenius temperature dependence, and particle-size scaling explicit while
    exposing a dimensionless rate scale for later calibration.
    """
    selected = get_sintering_law(law)
    temperature = max(float(temperature_k), 1e-9)
    radius = max(float(particle_radius_um), 1e-9)
    elapsed = max(float(time_s), 0.0)
    initial = clamp(float(initial_neck_ratio), 0.0, max_neck_ratio)
    if elapsed == 0.0:
        return initial

    multiplier = arrhenius_multiplier(
        temperature,
        selected.activation_energy_j_mol,
        reference_temperature_k=reference_temperature_k,
    )
    size_scale = (reference_radius_um / radius) ** selected.particle_size_exponent
    thermal_term = selected.rate_prefactor * rate_scale * elapsed * multiplier * size_scale
    if selected.growth_exponent == 1.0:
        neck = initial + thermal_term
    else:
        neck = (initial**selected.growth_exponent + thermal_term) ** (
            1.0 / selected.growth_exponent
        )
    return clamp(neck, initial, max_neck_ratio)


def blended_neck_ratio(
    *,
    temperature_k: float,
    time_s: float,
    particle_radius_um: float,
    initial_neck_ratio: float = 0.02,
    reference_temperature_k: float = 293.15,
    rate_scale: float = 1.0,
) -> tuple[float, str, float]:
    """Blend initial-stage mechanisms and return the dominant contributor."""
    candidates = [
        (
            name,
            sintering_neck_ratio(
                temperature_k=temperature_k,
                time_s=time_s,
                particle_radius_um=particle_radius_um,
                law=name,
                initial_neck_ratio=initial_neck_ratio,
                reference_temperature_k=reference_temperature_k,
                rate_scale=rate_scale,
            ),
        )
        for name in ("surface", "grain_boundary", "volume")
    ]
    dominant, neck = max(candidates, key=lambda item: item[1])
    law = get_sintering_law(dominant)
    return neck, dominant, law.growth_exponent


def get_sintering_law(name: str) -> SinteringLaw:
    try:
        return SINTERING_LAWS[name]
    except KeyError as exc:
        choices = ", ".join(sorted(SINTERING_LAWS))
        raise ValueError(f"unknown sintering law {name!r}; choose one of {choices}") from exc


def arrhenius_multiplier(
    temperature_k: float,
    activation_energy_j_mol: float,
    *,
    reference_temperature_k: float,
    max_multiplier: float = 1.0e6,
) -> float:
    temperature = max(float(temperature_k), 1e-9)
    reference = max(float(reference_temperature_k), 1e-9)
    exponent = -activation_energy_j_mol / GAS_CONSTANT_J_PER_MOL_K * (
        1.0 / temperature - 1.0 / reference
    )
    exponent = clamp(exponent, -60.0, math.log(max_multiplier))
    return math.exp(exponent)


def clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))
