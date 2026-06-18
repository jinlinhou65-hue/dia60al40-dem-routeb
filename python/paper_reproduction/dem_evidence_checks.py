from __future__ import annotations

import csv
import math
import re
from collections import Counter
from pathlib import Path

from .validation import trend_direction


def file_check(domain: str, path: Path, root: Path) -> dict[str, object]:
    if path.exists() and path.stat().st_size > 0:
        status = "pass"
        actual = path.stat().st_size
    elif path.exists():
        status = "mismatch"
        actual = 0
    else:
        status = "missing"
        actual = None
    return {
        "domain": domain,
        "label": f"{path.name} exists",
        "expected": "non-empty file",
        "actual": actual,
        "status": status,
        "evidence": relative(path, root),
    }


def file_glob_check(domain: str, label: str, pattern: Path) -> dict[str, object]:
    matches = sorted(pattern.parent.glob(pattern.name))
    return {
        "domain": domain,
        "label": label,
        "expected": "at least one file",
        "actual": len(matches),
        "status": "pass" if matches else "missing",
        "evidence": str(pattern),
    }


def trend_check(
    domain: str,
    label: str,
    rows: list[dict[str, object]],
    field: str,
    expected: str,
    *,
    evidence: str,
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
    return {
        "domain": domain,
        "label": label,
        "expected": expected,
        "actual": actual,
        "status": status,
        "evidence": evidence,
    }


def scalar_check(
    domain: str,
    label: str,
    actual: int | float | None,
    expected: int | float,
    *,
    comparator: str,
    evidence: str,
) -> dict[str, object]:
    if actual is None:
        status = "missing"
    elif comparator == "==" and actual == expected:
        status = "pass"
    elif comparator == ">=" and actual >= expected:
        status = "pass"
    else:
        status = "mismatch"
    return {
        "domain": domain,
        "label": label,
        "expected": f"{comparator} {expected}",
        "actual": actual,
        "status": status,
        "evidence": evidence,
    }


def tolerance_check(
    domain: str,
    label: str,
    actual: float | None,
    expected: float,
    tolerance: float,
    *,
    evidence: str,
) -> dict[str, object]:
    if actual is None or not math.isfinite(actual):
        status = "missing"
    elif abs(actual - expected) <= tolerance:
        status = "pass"
    else:
        status = "mismatch"
    return {
        "domain": domain,
        "label": label,
        "expected": f"{expected:g} +/- {tolerance:g}",
        "actual": actual,
        "status": status,
        "evidence": evidence,
    }


def positive_scalar_check(domain: str, label: str, actual: object, *, evidence: str) -> dict[str, object]:
    try:
        value = float(actual)
    except (TypeError, ValueError):
        value = math.nan
    if not math.isfinite(value):
        status = "missing"
        result = None
    elif value > 0.0:
        status = "pass"
        result = value
    else:
        status = "mismatch"
        result = value
    return {
        "domain": domain,
        "label": label,
        "expected": "> 0",
        "actual": result,
        "status": status,
        "evidence": evidence,
    }


def set_check(
    domain: str,
    label: str,
    actual_values: list[str],
    expected_values: list[str],
    *,
    evidence: str,
) -> dict[str, object]:
    actual = set(actual_values)
    expected = set(expected_values)
    missing = sorted(expected - actual)
    return {
        "domain": domain,
        "label": label,
        "expected": ",".join(expected_values),
        "actual": ",".join(actual_values),
        "status": "pass" if not missing else "missing",
        "evidence": evidence,
    }


def exact_string_check(domain: str, label: str, actual: object, expected: str, *, evidence: str) -> dict[str, object]:
    return {
        "domain": domain,
        "label": label,
        "expected": expected,
        "actual": actual,
        "status": "pass" if actual == expected else "mismatch",
        "evidence": evidence,
    }


def model_check(domain: str, label: str, rows: list[dict[str, object]], model: str, *, evidence: str) -> dict[str, object]:
    matches = [row for row in rows if row.get("model") == model]
    return {
        "domain": domain,
        "label": label,
        "expected": model,
        "actual": matches[0].get("r2") if matches else None,
        "status": "pass" if matches else "missing",
        "evidence": evidence,
    }


def missing_check(domain: str, label: str, evidence: str) -> dict[str, object]:
    return {
        "domain": domain,
        "label": label,
        "expected": "present",
        "actual": None,
        "status": "missing",
        "evidence": evidence,
    }


def summarize_checks(checks: list[dict[str, object]]) -> list[dict[str, object]]:
    counts = Counter(str(check["status"]) for check in checks)
    if counts.get("mismatch"):
        status = "mismatch"
    elif counts.get("missing"):
        status = "missing"
    elif counts.get("review"):
        status = "review"
    else:
        status = "pass"
    return [
        {
            "scope": "dem_evidence",
            "status": status,
            "pass": counts.get("pass", 0),
            "review": counts.get("review", 0),
            "missing": counts.get("missing", 0),
            "mismatch": counts.get("mismatch", 0),
            "check_count": len(checks),
        }
    ]


def read_model_parameters(path: Path) -> dict[str, str]:
    rows = read_csv_or_empty(path)
    return {str(row.get("parameter")): str(row.get("value")) for row in rows if row.get("parameter")}


def read_csv_or_empty(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def numeric_values(rows: list[dict[str, object]], field: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = row.get(field)
        if value in (None, ""):
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(number):
            values.append(number)
    return values


def numeric_first(rows: list[dict[str, object]], field: str) -> float | None:
    values = numeric_values(rows, field)
    return values[0] if values else None


def numeric_last(rows: list[dict[str, object]], field: str) -> float | None:
    values = numeric_values(rows, field)
    return values[-1] if values else None


def int_value(values: dict[str, str], key: str) -> int:
    try:
        return int(float(values.get(key, "0")))
    except ValueError:
        return 0


def parse_runtime_controls(path: Path) -> dict[str, float]:
    text = path.read_text(encoding="utf-8")
    return {
        "top_vel_cm_s": regex_float(text, r"variable\s+topVel\s+equal\s+([-+0-9.eE]+)"),
        "dt_seconds": regex_float(text, r"variable\s+dt\s+equal\s+([-+0-9.eE]+)"),
    }


def regex_float(text: str, pattern: str) -> float:
    match = re.search(pattern, text)
    if not match:
        return math.nan
    return float(match.group(1))


def relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def format_value(value) -> str:
    if value is None:
        return "missing"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)
