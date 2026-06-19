from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path

from .zhang_validation import validate_zhang_algorithm
from .yuan_validation import validate_yuan_algorithm


def validate_stage_series(
    metric_rows: list[dict[str, object]],
    fit_rows: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    checks: list[dict[str, object]] = []
    checks.extend(
        [
            trend_check(metric_rows, "Zhang", "pressure rises with compaction", "pressure_mpa", "increasing"),
            trend_check(metric_rows, "Zhang", "density rises with pressure", "actual_rho_total", "increasing"),
            trend_check(metric_rows, "Zhang", "coordination increases", "mean_coordination", "increasing"),
            trend_check(metric_rows, "Zhang", "contact participation increases", "contact_participation", "increasing"),
            trend_check(metric_rows, "Zhang", "force-chain D1 decreases", "force_chain_strength_inhomogeneity_d1", "decreasing"),
            trend_check(metric_rows, "Zhang", "local-stress D2 decreases", "local_stress_inhomogeneity_d2", "decreasing"),
            positive_check(metric_rows, "Yuan", "arch candidates exist", "arch_count"),
            positive_check(metric_rows, "Yuan", "arch strength is positive", "arch_mean_strength"),
            finite_check(metric_rows, "Yuan", "arch direction angle is measured", "arch_mean_direction_angle_degrees"),
            model_check(fit_rows, "Liu", "Heckel fit exists", "Heckel"),
            model_check(fit_rows, "Liu", "Kawakita fit exists", "Kawakita"),
            positive_check(metric_rows, "Liu", "force-current coupling is positive", "coupling_normal_force_vs_abs_current"),
            positive_check(metric_rows, "Liu", "force-Joule coupling is positive", "coupling_normal_force_vs_joule_heat"),
            positive_check(metric_rows, "Liu", "particle heat-diffusion-neck coupling is positive", "coupling_particle_heat_vs_neck_ratio"),
            schema_check(metric_rows, "Li", "stage schema can support coated-powder sweeps", ["pressure_mpa", "actual_rho_total", "contact_gini"]),
        ]
    )
    return checks, summarize_by_paper(checks)


def validate_algorithm_reproduction(
    outdir: Path,
    *,
    papers: list[str] | None = None,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    requested = set(papers or ["zhang", "yuan", "liu", "li"])
    checks: list[dict[str, object]] = []
    if "zhang" in requested:
        checks.extend(
            validate_zhang_algorithm(
                outdir / "zhang" / "zhang_multiscale_metrics.csv",
                outdir / "zhang" / "zhang_friction_sensitivity.csv",
            )
        )
    if "yuan" in requested:
        checks.extend(validate_yuan_algorithm(outdir / "yuan" / "yuan_arch_bridge_metrics.csv"))
    if "liu" in requested:
        checks.extend(
            validate_liu_algorithm(
                outdir / "liu" / "liu_compaction_curve.csv",
                outdir / "liu" / "liu_compaction_fits.csv",
                outdir / "liu" / "liu_coupling_summary.json",
            )
        )
    if "li" in requested:
        checks.extend(validate_li_algorithm(outdir / "li" / "li_coated_powder_sweeps.csv"))
    return checks, summarize_by_paper(checks)


def write_acceptance_outputs(
    outdir: Path,
    checks: list[dict[str, object]],
    summary: list[dict[str, object]],
    *,
    prefix: str,
) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / f"{prefix}_trend_checks.json").write_text(
        json.dumps(checks, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_csv(outdir / f"{prefix}_acceptance_summary.csv", summary)
    (outdir / f"{prefix}_acceptance_report.md").write_text(
        render_acceptance_report(checks, summary, title=f"{prefix} acceptance report"),
        encoding="utf-8",
    )


def validate_liu_algorithm(curve_path: Path, fits_path: Path, coupling_path: Path) -> list[dict[str, object]]:
    curve_rows = read_csv_or_empty(curve_path)
    fit_rows = read_csv_or_empty(fits_path)
    coupling = read_json_or_empty(coupling_path)
    return [
        trend_check(curve_rows, "Liu", "density rises with pressure", "relative_density", "increasing"),
        model_check(fit_rows, "Liu", "Heckel fit exists", "Heckel"),
        model_check(fit_rows, "Liu", "Kawakita fit exists", "Kawakita"),
        model_check(fit_rows, "Liu", "Huang fit exists", "Huang"),
        scalar_positive_check(coupling, "Liu", "force-current correlation is positive", "normal_force_vs_current"),
        scalar_positive_check(coupling, "Liu", "Joule heat-neck correlation is positive", "joule_heat_vs_neck_ratio"),
    ]


def validate_li_algorithm(path: Path) -> list[dict[str, object]]:
    rows = read_csv_or_empty(path)
    return [
        sweep_order_check(rows, "Li", "Cu coating improves density", "composition", "cu_fraction", 0.0, 0.25, "increasing"),
        sweep_order_check(rows, "Li", "temperature improves density", "temperature", "temperature_c", 20.0, 140.0, "increasing"),
        sweep_order_check(rows, "Li", "wall friction reduces density", "wall_friction", "wall_mu", 0.02, 0.20, "decreasing"),
        sweep_order_check(rows, "Li", "pressing speed reduces density", "pressing_speed", "pressing_speed", 0.005, 0.16, "decreasing"),
        sweep_peak_check(rows, "Li", "aspect ratio near 2 is favorable", "aspect_ratio", "aspect_ratio", 2.0),
    ]


def trend_check(
    rows: list[dict[str, object]],
    paper: str,
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
    return {
        "paper": paper,
        "label": label,
        "field": field,
        "expected": expected,
        "actual": actual,
        "status": status,
        "sample_count": len(values),
        "first": values[0] if values else None,
        "last": values[-1] if values else None,
    }


def positive_check(
    rows: list[dict[str, object]],
    paper: str,
    label: str,
    field: str,
    *,
    threshold: float = 0.0,
) -> dict[str, object]:
    values = numeric_values(rows, field)
    positives = [value for value in values if value > threshold]
    if not values:
        status = "missing"
    elif positives:
        status = "pass"
    else:
        status = "mismatch"
    return {
        "paper": paper,
        "label": label,
        "field": field,
        "expected": f">{threshold:g}",
        "actual": max(values) if values else None,
        "status": status,
        "sample_count": len(values),
    }


def scalar_positive_check(
    values: dict[str, object],
    paper: str,
    label: str,
    field: str,
    *,
    threshold: float = 0.0,
) -> dict[str, object]:
    value = values.get(field)
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = math.nan
    if not math.isfinite(number):
        status = "missing"
    elif number > threshold:
        status = "pass"
    else:
        status = "mismatch"
    return {
        "paper": paper,
        "label": label,
        "field": field,
        "expected": f">{threshold:g}",
        "actual": number if math.isfinite(number) else None,
        "status": status,
        "sample_count": 1 if math.isfinite(number) else 0,
    }


def sweep_order_check(
    rows: list[dict[str, object]],
    paper: str,
    label: str,
    sweep: str,
    x_field: str,
    low_x: float,
    high_x: float,
    expected: str,
) -> dict[str, object]:
    sweep_rows = [row for row in rows if row.get("sweep") == sweep]
    low = value_at(sweep_rows, x_field, low_x, "predicted_relative_density")
    high = value_at(sweep_rows, x_field, high_x, "predicted_relative_density")
    if low is None or high is None:
        status = "missing"
        actual = None
    else:
        actual = high - low
        status = "pass" if (actual > 0 if expected == "increasing" else actual < 0) else "mismatch"
    return {
        "paper": paper,
        "label": label,
        "field": f"{sweep}.{x_field}",
        "expected": expected,
        "actual": actual,
        "status": status,
        "sample_count": len(sweep_rows),
    }


def sweep_peak_check(
    rows: list[dict[str, object]],
    paper: str,
    label: str,
    sweep: str,
    x_field: str,
    expected_peak_x: float,
) -> dict[str, object]:
    sweep_rows = [row for row in rows if row.get("sweep") == sweep]
    if not sweep_rows:
        return {
            "paper": paper,
            "label": label,
            "field": f"{sweep}.{x_field}",
            "expected": f"peak at {expected_peak_x:g}",
            "actual": None,
            "status": "missing",
            "sample_count": 0,
        }
    best = max(
        sweep_rows,
        key=lambda row: float(row.get("predicted_relative_density", "-inf")),
    )
    actual_peak = float(best[x_field])
    return {
        "paper": paper,
        "label": label,
        "field": f"{sweep}.{x_field}",
        "expected": f"peak at {expected_peak_x:g}",
        "actual": actual_peak,
        "status": "pass" if abs(actual_peak - expected_peak_x) <= 1e-9 else "review",
        "sample_count": len(sweep_rows),
    }


def finite_check(
    rows: list[dict[str, object]],
    paper: str,
    label: str,
    field: str,
) -> dict[str, object]:
    values = numeric_values(rows, field)
    return {
        "paper": paper,
        "label": label,
        "field": field,
        "expected": "finite",
        "actual": len(values),
        "status": "pass" if values else "missing",
        "sample_count": len(values),
    }


def model_check(
    fit_rows: list[dict[str, object]],
    paper: str,
    label: str,
    model: str,
) -> dict[str, object]:
    rows = [row for row in fit_rows if row.get("model") == model]
    status = "pass" if rows else "missing"
    r2 = rows[0].get("r2") if rows else None
    return {
        "paper": paper,
        "label": label,
        "field": "series_compaction_fits",
        "expected": model,
        "actual": r2,
        "status": status,
        "sample_count": len(rows),
    }


def schema_check(
    rows: list[dict[str, object]],
    paper: str,
    label: str,
    fields: list[str],
) -> dict[str, object]:
    if not rows:
        status = "missing"
        missing = fields
    else:
        present = set().union(*(row.keys() for row in rows))
        missing = [field for field in fields if field not in present]
        status = "pass" if not missing else "missing"
    return {
        "paper": paper,
        "label": label,
        "field": ",".join(fields),
        "expected": "schema fields present",
        "actual": ",".join(missing) if missing else "all present",
        "status": status,
        "sample_count": len(rows),
    }


def summarize_by_paper(checks: list[dict[str, object]]) -> list[dict[str, object]]:
    papers = sorted({str(check["paper"]) for check in checks})
    summaries: list[dict[str, object]] = []
    for paper in papers:
        paper_checks = [check for check in checks if check["paper"] == paper]
        counts = Counter(str(check["status"]) for check in paper_checks)
        if counts.get("mismatch"):
            status = "mismatch"
        elif counts.get("missing"):
            status = "missing"
        elif counts.get("review"):
            status = "review"
        else:
            status = "pass"
        summaries.append(
            {
                "paper": paper,
                "status": status,
                "pass": counts.get("pass", 0),
                "review": counts.get("review", 0),
                "missing": counts.get("missing", 0),
                "mismatch": counts.get("mismatch", 0),
                "check_count": len(paper_checks),
            }
        )
    return summaries


def render_acceptance_report(
    checks: list[dict[str, object]],
    summary: list[dict[str, object]],
    *,
    title: str,
) -> str:
    lines = [
        f"# {title}",
        "",
        "## Summary",
        "",
        "| Paper | Status | Pass | Review | Missing | Mismatch |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            f"| {row['paper']} | {row['status']} | {row['pass']} | {row['review']} | {row['missing']} | {row['mismatch']} |"
        )
    lines.extend(
        [
            "",
            "## Checks",
            "",
            "| Paper | Check | Expected | Actual | Status |",
            "|---|---|---|---|---|",
        ]
    )
    for check in checks:
        lines.append(
            f"| {check['paper']} | {check['label']} | {check['expected']} | {format_optional(check.get('actual'))} | {check['status']} |"
        )
    lines.append("")
    return "\n".join(lines)


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


def value_at(
    rows: list[dict[str, object]],
    x_field: str,
    x_value: float,
    value_field: str,
) -> float | None:
    for row in rows:
        try:
            x = float(row.get(x_field))
        except (TypeError, ValueError):
            continue
        if abs(x - x_value) <= 1e-9:
            try:
                return float(row[value_field])
            except (TypeError, ValueError):
                return None
    return None


def read_csv_or_empty(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json_or_empty(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        if not fieldnames:
            handle.write("")
            return
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def format_optional(value) -> str:
    if value is None:
        return "missing"
    if isinstance(value, float):
        return f"{value:.5g}"
    return str(value)


def trend_direction(values: list[float]) -> str | None:
    if len(values) < 2:
        return None
    delta = values[-1] - values[0]
    scale = max(1.0, abs(values[0]), abs(values[-1]))
    if abs(delta) <= 1e-9 * scale:
        return "flat"
    return "increasing" if delta > 0 else "decreasing"
