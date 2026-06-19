from __future__ import annotations

import csv
import math
from pathlib import Path


def validate_li_algorithm(
    sweep_path: Path,
    core_shell_path: Path,
    temperature_path: Path,
    convergence_path: Path,
) -> list[dict[str, object]]:
    sweeps = read_csv_or_empty(sweep_path)
    core_shell = read_csv_or_empty(core_shell_path)
    temperature = read_csv_or_empty(temperature_path)
    convergence = read_csv_or_empty(convergence_path)
    return [
        sweep_order_check(sweeps, "Cu coating improves density", "composition", "cu_fraction", 0.0, 0.25, "increasing"),
        sweep_order_check(sweeps, "temperature improves density", "temperature", "temperature_c", 20.0, 140.0, "increasing"),
        sweep_order_check(sweeps, "wall friction reduces density", "wall_friction", "wall_mu", 0.02, 0.20, "decreasing"),
        sweep_order_check(sweeps, "pressing speed reduces density", "pressing_speed", "pressing_speed", 0.005, 0.16, "decreasing"),
        sweep_peak_check(sweeps, "aspect ratio near 2 is favorable", "aspect_ratio", "aspect_ratio", 2.0),
        sweep_order_check(
            sweeps,
            "maximum stress rises with large aspect ratio",
            "aspect_ratio",
            "aspect_ratio",
            0.8,
            3.0,
            "increasing",
            value_field="max_von_mises_mpa",
        ),
        density_ranking_check(core_shell),
        composition_order_check(core_shell, "Cu20 stress is more uniform than Fe", "stress_uniformity_index", "Fe", "Cu20@Fe80", "decreasing"),
        composition_order_check(core_shell, "Cu20 plasticity is higher than Fe", "plastic_strain_proxy", "Fe", "Cu20@Fe80", "increasing"),
        monotone_by_composition_check(core_shell, "interface friction decreases with Cu fraction", "interface_friction_proxy", "decreasing"),
        monotone_by_composition_check(core_shell, "wall friction decreases with Cu fraction", "wall_friction_proxy", "decreasing"),
        temperature_gain_check(temperature, "temperature raises density at 300 MPa", "Cu20@Fe80", 300.0),
        temperature_attenuation_check(temperature, "temperature effect weakens after 500 MPa", "Cu20@Fe80"),
        particle_convergence_check(convergence),
    ]


def sweep_order_check(
    rows: list[dict[str, object]],
    label: str,
    sweep: str,
    x_field: str,
    low_x: float,
    high_x: float,
    expected: str,
    *,
    value_field: str = "predicted_relative_density",
) -> dict[str, object]:
    sweep_rows = [row for row in rows if row.get("sweep") == sweep]
    low = value_at(sweep_rows, x_field, low_x, value_field)
    high = value_at(sweep_rows, x_field, high_x, value_field)
    if low is None or high is None:
        return check_row(label, f"{sweep}.{x_field}", expected, None, "missing", len(sweep_rows))
    actual = high - low
    passed = actual > 0 if expected == "increasing" else actual < 0
    return check_row(label, f"{sweep}.{x_field}", expected, actual, "pass" if passed else "mismatch", len(sweep_rows))


def sweep_peak_check(
    rows: list[dict[str, object]],
    label: str,
    sweep: str,
    x_field: str,
    expected_peak_x: float,
) -> dict[str, object]:
    sweep_rows = [row for row in rows if row.get("sweep") == sweep]
    if not sweep_rows:
        return check_row(label, f"{sweep}.{x_field}", f"peak at {expected_peak_x:g}", None, "missing", 0)
    best = max(sweep_rows, key=lambda row: finite_float(row.get("predicted_relative_density")) or -math.inf)
    actual_peak = finite_float(best.get(x_field))
    status = "pass" if actual_peak is not None and abs(actual_peak - expected_peak_x) <= 1e-9 else "review"
    return check_row(label, f"{sweep}.{x_field}", f"peak at {expected_peak_x:g}", actual_peak, status, len(sweep_rows))


def density_ranking_check(rows: list[dict[str, object]]) -> dict[str, object]:
    fe = composition_value(rows, "Fe", "relative_density_600mpa")
    cu10 = composition_value(rows, "Cu10@Fe90", "relative_density_600mpa")
    cu20 = composition_value(rows, "Cu20@Fe80", "relative_density_600mpa")
    cu30 = composition_value(rows, "Cu30@Fe70", "relative_density_600mpa")
    values = [fe, cu10, cu20, cu30]
    if any(value is None for value in values):
        return check_row("experimental density ranking is reproduced", "relative_density_600mpa", "Cu30>Cu20>Cu10>Fe", None, "missing", len(rows))
    passed = bool(cu30 > cu20 > cu10 > fe)
    actual = f"{fe:.5f},{cu10:.5f},{cu20:.5f},{cu30:.5f}"
    return check_row("experimental density ranking is reproduced", "relative_density_600mpa", "Cu30>Cu20>Cu10>Fe", actual, "pass" if passed else "mismatch", len(rows))


def composition_order_check(
    rows: list[dict[str, object]],
    label: str,
    field: str,
    low_composition: str,
    high_composition: str,
    expected: str,
) -> dict[str, object]:
    low = composition_value(rows, low_composition, field)
    high = composition_value(rows, high_composition, field)
    if low is None or high is None:
        return check_row(label, field, expected, None, "missing", len(rows))
    actual = high - low
    passed = actual > 0 if expected == "increasing" else actual < 0
    return check_row(label, field, expected, actual, "pass" if passed else "mismatch", len(rows))


def monotone_by_composition_check(
    rows: list[dict[str, object]],
    label: str,
    field: str,
    expected: str,
) -> dict[str, object]:
    points = [
        (cu, value)
        for row in rows
        for cu in [finite_float(row.get("cu_fraction"))]
        for value in [finite_float(row.get(field))]
        if cu is not None and value is not None
    ]
    if len(points) < 2:
        return check_row(label, field, expected, None, "missing", len(points))
    ordered = [value for _, value in sorted(points)]
    delta = ordered[-1] - ordered[0]
    passed = delta > 0 if expected == "increasing" else delta < 0
    return check_row(label, field, expected, delta, "pass" if passed else "mismatch", len(points))


def temperature_gain_check(
    rows: list[dict[str, object]],
    label: str,
    material: str,
    pressure_mpa: float,
) -> dict[str, object]:
    low = temperature_value(rows, material, pressure_mpa, 20.0)
    high = temperature_value(rows, material, pressure_mpa, 140.0)
    if low is None or high is None:
        return check_row(label, "relative_density", "temperature gain >0", None, "missing", len(rows))
    delta = high - low
    return check_row(label, "relative_density", ">0", delta, "pass" if delta > 0 else "mismatch", len(rows))


def temperature_attenuation_check(
    rows: list[dict[str, object]],
    label: str,
    material: str,
) -> dict[str, object]:
    low_pressure_delta = temperature_delta(rows, material, 300.0, 20.0, 300.0)
    high_pressure_delta = temperature_delta(rows, material, 600.0, 20.0, 300.0)
    if low_pressure_delta is None or high_pressure_delta is None:
        return check_row(label, "temperature_effect_attenuation", "delta_600 < delta_300", None, "missing", len(rows))
    actual = high_pressure_delta - low_pressure_delta
    return check_row(label, "temperature_effect_attenuation", "delta_600 < delta_300", actual, "pass" if actual < 0 else "mismatch", len(rows))


def particle_convergence_check(rows: list[dict[str, object]]) -> dict[str, object]:
    early = pressure_count_delta(rows, 300.0)
    final = pressure_count_delta(rows, 600.0)
    if early is None or final is None:
        return check_row("100 and 197 particle models converge at high pressure", "relative_density", "final delta < early delta and <0.001", None, "missing", len(rows))
    actual = final - early
    passed = final < early and final < 0.001
    return check_row("100 and 197 particle models converge at high pressure", "relative_density", "final delta < early delta and <0.001", actual, "pass" if passed else "mismatch", len(rows))


def pressure_count_delta(rows: list[dict[str, object]], pressure_mpa: float) -> float | None:
    low = count_value(rows, pressure_mpa, 100)
    high = count_value(rows, pressure_mpa, 197)
    if low is None or high is None:
        return None
    return abs(high - low)


def count_value(rows: list[dict[str, object]], pressure_mpa: float, particle_count: int) -> float | None:
    for row in rows:
        pressure = finite_float(row.get("pressure_mpa"))
        count = finite_float(row.get("particle_count"))
        if pressure == pressure_mpa and count == particle_count:
            return finite_float(row.get("relative_density"))
    return None


def temperature_delta(
    rows: list[dict[str, object]],
    material: str,
    pressure_mpa: float,
    low_temperature: float,
    high_temperature: float,
) -> float | None:
    low = temperature_value(rows, material, pressure_mpa, low_temperature)
    high = temperature_value(rows, material, pressure_mpa, high_temperature)
    if low is None or high is None:
        return None
    return high - low


def temperature_value(
    rows: list[dict[str, object]],
    material: str,
    pressure_mpa: float,
    temperature_c: float,
) -> float | None:
    for row in rows:
        pressure = finite_float(row.get("pressure_mpa"))
        temperature = finite_float(row.get("temperature_c"))
        if row.get("material") == material and pressure == pressure_mpa and temperature == temperature_c:
            return finite_float(row.get("relative_density"))
    return None


def composition_value(rows: list[dict[str, object]], composition: str, field: str) -> float | None:
    for row in rows:
        if row.get("composition") == composition:
            return finite_float(row.get(field))
    return None


def value_at(
    rows: list[dict[str, object]],
    x_field: str,
    x_value: float,
    value_field: str,
) -> float | None:
    for row in rows:
        x = finite_float(row.get(x_field))
        if x is not None and abs(x - x_value) <= 1e-9:
            return finite_float(row.get(value_field))
    return None


def check_row(
    label: str,
    field: str,
    expected: str,
    actual: object,
    status: str,
    sample_count: int,
) -> dict[str, object]:
    return {
        "paper": "Li",
        "label": label,
        "field": field,
        "expected": expected,
        "actual": actual,
        "status": status,
        "sample_count": sample_count,
    }


def finite_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def read_csv_or_empty(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))
