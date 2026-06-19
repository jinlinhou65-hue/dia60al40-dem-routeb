from __future__ import annotations

import csv
import math
from pathlib import Path


def validate_zhang_algorithm(
    metrics_path: Path,
    friction_path: Path,
) -> list[dict[str, object]]:
    metrics = read_csv_or_empty(metrics_path)
    friction = read_csv_or_empty(friction_path)
    return [
        trend_check(metrics, "pressure rises with axial strain", "pressure_mpa", "increasing"),
        trend_check(metrics, "relative density rises", "relative_density", "increasing"),
        trend_check(metrics, "contact Gini decreases", "contact_gini", "decreasing"),
        trend_check(metrics, "contact participation increases", "contact_participation", "increasing"),
        trend_check(metrics, "force-chain D1 decreases", "force_chain_strength_inhomogeneity_d1", "decreasing"),
        trend_check(metrics, "local-stress D2 decreases", "local_stress_inhomogeneity_d2", "decreasing"),
        positive_check(metrics, "force chains are extracted", "force_chain_count"),
        positive_check(metrics, "local stress measurement circles are populated", "local_stress_mean"),
        friction_order_check(friction, "wall friction increases contact Gini", "wall", "wall_mu", "contact_gini"),
        friction_order_check(friction, "particle friction increases contact Gini", "particle", "particle_mu", "contact_gini"),
        friction_order_check(friction, "wall friction increases local-stress D2", "wall", "wall_mu", "local_stress_inhomogeneity_d2"),
        friction_order_check(friction, "particle friction increases force-chain D1", "particle", "particle_mu", "force_chain_strength_inhomogeneity_d1"),
        friction_dominance_check(
            friction,
            "particle friction has stronger micro contact effect",
            "contact_gini",
            dominant="particle",
        ),
        friction_dominance_check(
            friction,
            "particle friction has stronger meso force-chain effect",
            "force_chain_strength_inhomogeneity_d1",
            dominant="particle",
        ),
    ]


def trend_check(
    rows: list[dict[str, object]],
    label: str,
    field: str,
    expected: str,
) -> dict[str, object]:
    values = numeric_values(rows, field)
    actual = trend_direction(values)
    if actual is None:
        status = "missing"
    elif actual == expected:
        status = "pass"
    elif actual == "flat":
        status = "review"
    else:
        status = "mismatch"
    return check_row(label, field, expected, actual, status, len(values))


def positive_check(
    rows: list[dict[str, object]],
    label: str,
    field: str,
    *,
    threshold: float = 0.0,
) -> dict[str, object]:
    values = numeric_values(rows, field)
    positives = [value for value in values if value > threshold]
    status = "missing" if not values else "pass" if positives else "mismatch"
    return check_row(label, field, f">{threshold:g}", max(values) if values else None, status, len(values))


def friction_order_check(
    rows: list[dict[str, object]],
    label: str,
    friction_type: str,
    x_field: str,
    value_field: str,
) -> dict[str, object]:
    sweep = [row for row in rows if row.get("friction_type") == friction_type]
    low, high = endpoint_values(sweep, x_field, value_field)
    if low is None or high is None:
        return check_row(label, value_field, "higher friction gives higher nonuniformity", None, "missing", len(sweep))
    delta = high - low
    return check_row(label, value_field, ">0", delta, "pass" if delta > 0 else "mismatch", len(sweep))


def friction_dominance_check(
    rows: list[dict[str, object]],
    label: str,
    value_field: str,
    *,
    dominant: str,
) -> dict[str, object]:
    particle_delta = friction_delta(rows, "particle", "particle_mu", value_field)
    wall_delta = friction_delta(rows, "wall", "wall_mu", value_field)
    if particle_delta is None or wall_delta is None:
        return check_row(label, value_field, f"{dominant} effect largest", None, "missing", len(rows))
    actual = particle_delta - wall_delta if dominant == "particle" else wall_delta - particle_delta
    return check_row(label, value_field, f"{dominant} effect largest", actual, "pass" if actual > 0 else "mismatch", len(rows))


def endpoint_values(
    rows: list[dict[str, object]],
    x_field: str,
    value_field: str,
) -> tuple[float | None, float | None]:
    points = [
        (x, value)
        for row in rows
        for x in [finite_float(row.get(x_field))]
        for value in [finite_float(row.get(value_field))]
        if x is not None and value is not None
    ]
    if len(points) < 2:
        return None, None
    ordered = sorted(points)
    return ordered[0][1], ordered[-1][1]


def friction_delta(
    rows: list[dict[str, object]],
    friction_type: str,
    x_field: str,
    value_field: str,
) -> float | None:
    low, high = endpoint_values([row for row in rows if row.get("friction_type") == friction_type], x_field, value_field)
    if low is None or high is None:
        return None
    return high - low


def check_row(
    label: str,
    field: str,
    expected: str,
    actual: object,
    status: str,
    sample_count: int,
) -> dict[str, object]:
    return {
        "paper": "Zhang",
        "label": label,
        "field": field,
        "expected": expected,
        "actual": actual,
        "status": status,
        "sample_count": sample_count,
    }


def numeric_values(rows: list[dict[str, object]], field: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = finite_float(row.get(field))
        if value is not None:
            values.append(value)
    return values


def finite_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def trend_direction(values: list[float]) -> str | None:
    if len(values) < 2:
        return None
    delta = values[-1] - values[0]
    scale = max(1.0, abs(values[0]), abs(values[-1]))
    if abs(delta) <= 1e-9 * scale:
        return "flat"
    return "increasing" if delta > 0 else "decreasing"


def read_csv_or_empty(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))
