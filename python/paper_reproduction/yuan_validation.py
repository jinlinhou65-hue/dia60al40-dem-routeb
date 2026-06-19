from __future__ import annotations

import csv
import math
from pathlib import Path


def validate_yuan_algorithm(path: Path) -> list[dict[str, object]]:
    rows = read_csv_or_empty(path)
    return [
        positive_check(rows, "arch candidates exist", "arch_count"),
        positive_check(rows, "arch length is positive", "arch_mean_length"),
        positive_check(rows, "arch obstruction is positive", "arch_obstruction_index"),
        grouped_order_check(
            rows,
            "circle has stronger arch obstruction than strip",
            group_field="shape",
            value_field="arch_obstruction_index",
            higher_group="circle",
            lower_group="strip",
        ),
        grouped_order_check(
            rows,
            "circle arch strength exceeds strip",
            group_field="shape",
            value_field="arch_mean_strength",
            higher_group="circle",
            lower_group="strip",
        ),
        nonmonotonic_peak_check(rows, "arch count increases then fluctuates", "arch_count"),
        oscillation_check(rows, "arch total length fluctuates", "arch_total_length"),
        growth_slowdown_check(
            rows,
            "arch strength growth slows after 100 MPa",
            "arch_mean_strength",
            split_pressure_mpa=100.0,
        ),
        direction_near_check(
            rows,
            "arch direction angle stays near 90 degrees",
            "arch_direction_angle_degrees",
            target_degrees=90.0,
            tolerance_degrees=8.0,
        ),
        finite_check(rows, "arch buckling angle is measured", "arch_buckling_angle_degrees"),
    ]


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


def finite_check(rows: list[dict[str, object]], label: str, field: str) -> dict[str, object]:
    values = numeric_values(rows, field)
    return check_row(label, field, "finite", len(values), "pass" if values else "missing", len(values))


def grouped_order_check(
    rows: list[dict[str, object]],
    label: str,
    *,
    group_field: str,
    value_field: str,
    higher_group: str,
    lower_group: str,
) -> dict[str, object]:
    high = mean_for_group(rows, group_field, higher_group, value_field)
    low = mean_for_group(rows, group_field, lower_group, value_field)
    if high is None or low is None:
        return check_row(label, value_field, f"{higher_group}>{lower_group}", None, "missing", len(rows))
    delta = high - low
    return check_row(label, value_field, f"{higher_group}>{lower_group}", delta, "pass" if delta > 0 else "mismatch", len(rows))


def nonmonotonic_peak_check(rows: list[dict[str, object]], label: str, field: str) -> dict[str, object]:
    groups = grouped_series(rows, field)
    if not groups:
        return check_row(label, field, "interior peak after early growth", None, "missing", 0)
    passed = 0
    for series in groups.values():
        values = [value for _, value in sorted(series)]
        if len(values) < 4:
            continue
        peak_idx = max(range(len(values)), key=values.__getitem__)
        grew_before_peak = values[peak_idx] > values[0]
        relaxed_after_peak = values[peak_idx] > values[-1]
        if 0 < peak_idx < len(values) - 1 and grew_before_peak and relaxed_after_peak:
            passed += 1
    status = "pass" if passed == len(groups) else "mismatch"
    return check_row(label, field, "all shapes show interior peak", passed, status, len(groups))


def oscillation_check(rows: list[dict[str, object]], label: str, field: str) -> dict[str, object]:
    groups = grouped_series(rows, field)
    if not groups:
        return check_row(label, field, "slope sign changes", None, "missing", 0)
    passed = 0
    for series in groups.values():
        values = [value for _, value in sorted(series)]
        deltas = [values[idx + 1] - values[idx] for idx in range(len(values) - 1)]
        signs = {1 if delta > 0 else -1 if delta < 0 else 0 for delta in deltas}
        if 1 in signs and -1 in signs:
            passed += 1
    status = "pass" if passed == len(groups) else "mismatch"
    return check_row(label, field, "positive and negative increments", passed, status, len(groups))


def growth_slowdown_check(
    rows: list[dict[str, object]],
    label: str,
    field: str,
    *,
    split_pressure_mpa: float,
) -> dict[str, object]:
    groups = grouped_series(rows, field)
    if not groups:
        return check_row(label, field, "early slope > late slope", None, "missing", 0)
    passed = 0
    ratios: list[float] = []
    for series in groups.values():
        ordered = sorted(series)
        early = [point for point in ordered if point[0] <= split_pressure_mpa]
        late = [point for point in ordered if point[0] >= split_pressure_mpa]
        if len(early) < 2 or len(late) < 2:
            continue
        early_slope = slope_between(early[0], early[-1])
        late_slope = slope_between(late[0], late[-1])
        if early_slope > late_slope > 0.0:
            passed += 1
        if late_slope > 0.0:
            ratios.append(early_slope / late_slope)
    status = "pass" if passed == len(groups) else "mismatch"
    actual = min(ratios) if ratios else None
    return check_row(label, field, "early/late slope ratio > 1", actual, status, len(groups))


def direction_near_check(
    rows: list[dict[str, object]],
    label: str,
    field: str,
    *,
    target_degrees: float,
    tolerance_degrees: float,
) -> dict[str, object]:
    values = numeric_values(rows, field)
    if not values:
        return check_row(label, field, f"{target_degrees:g}+/-{tolerance_degrees:g}", None, "missing", 0)
    max_deviation = max(abs(value - target_degrees) for value in values)
    status = "pass" if max_deviation <= tolerance_degrees else "mismatch"
    return check_row(label, field, f"{target_degrees:g}+/-{tolerance_degrees:g}", max_deviation, status, len(values))


def grouped_series(rows: list[dict[str, object]], field: str) -> dict[str, list[tuple[float, float]]]:
    groups: dict[str, list[tuple[float, float]]] = {}
    for row in rows:
        shape = str(row.get("shape", "all"))
        pressure = finite_float(row.get("pressure_mpa"))
        value = finite_float(row.get(field))
        if pressure is None or value is None:
            continue
        groups.setdefault(shape, []).append((pressure, value))
    return groups


def slope_between(start: tuple[float, float], end: tuple[float, float]) -> float:
    if abs(end[0] - start[0]) <= 1e-12:
        return math.nan
    return (end[1] - start[1]) / (end[0] - start[0])


def check_row(
    label: str,
    field: str,
    expected: str,
    actual: object,
    status: str,
    sample_count: int,
) -> dict[str, object]:
    return {
        "paper": "Yuan",
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


def mean_for_group(
    rows: list[dict[str, object]],
    group_field: str,
    group_value: str,
    value_field: str,
) -> float | None:
    values = [
        value
        for row in rows
        if row.get(group_field) == group_value
        for value in [finite_float(row.get(value_field))]
        if value is not None
    ]
    return sum(values) / len(values) if values else None


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
