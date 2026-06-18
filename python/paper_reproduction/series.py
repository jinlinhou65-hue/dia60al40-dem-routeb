from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict
from pathlib import Path

from .core import compaction_fits
from .network import (
    arch_bridges,
    coupling_summary,
    infer_contacts,
    read_particles,
    run_electrothermal_network,
    summarize_contact_network,
)
from .validation import validate_stage_series


STAGE_PATTERN = re.compile(r"(stage\d+_[A-Za-z0-9]+)")


def process_stage_series(
    *,
    snapshot_dir: Path,
    pressure_curve: Path,
    outdir: Path,
    snapshot_glob: str = "dem_fem_handoff_stage*.csv",
    length_unit: str = "um",
    width_um: float | None = None,
    gap_tolerance_um: float = 0.0,
    normal_stiffness: float = 1.0,
    force_exponent: float = 1.5,
    min_contact_force: float = 0.0,
) -> dict[str, object]:
    curve_by_stage = read_pressure_curve(pressure_curve)
    stage_paths = sorted(snapshot_dir.glob(snapshot_glob), key=lambda path: stage_sort_key(stage_id_from_path(path)))
    if not stage_paths:
        raise ValueError(f"no snapshot files matched {snapshot_dir / snapshot_glob}")

    metric_rows: list[dict[str, object]] = []
    details_dir = outdir / "stage_details"
    details_dir.mkdir(parents=True, exist_ok=True)
    for path in stage_paths:
        stage_id = stage_id_from_path(path)
        curve = curve_by_stage.get(stage_id, {})
        height_um = optional_float(curve.get("current_height_um"))
        particles = read_particles(path, length_unit=length_unit)
        contacts = infer_contacts(
            particles,
            gap_tolerance_um=gap_tolerance_um,
            normal_stiffness=normal_stiffness,
            force_exponent=force_exponent,
            min_contact_force=min_contact_force,
        )
        metrics = summarize_contact_network(
            particles,
            contacts,
            width_um=width_um,
            height_um=height_um,
        )
        particle_fields, contact_fields = run_electrothermal_network(particles, contacts)
        coupling = coupling_summary(contact_fields, particle_fields)
        arches = arch_bridges(particles, contacts)
        write_csv(details_dir / f"{stage_id}_contacts.csv", [asdict(contact) for contact in contacts])
        write_csv(details_dir / f"{stage_id}_arches.csv", [asdict(arch) for arch in arches])
        row = {
            "stage_id": stage_id,
            "snapshot_file": path.name,
            "pressure_mpa": optional_float(curve.get("pressure_mpa")),
            "target_rho_total": optional_float(curve.get("target_rho_total")),
            "actual_rho_total": optional_float(curve.get("actual_rho_total")),
            "current_height_um": height_um,
            **metrics,
            **{f"coupling_{key}": value for key, value in coupling.items()},
        }
        metric_rows.append(row)

    fit_rows = fit_rows_from_metrics(metric_rows)
    outdir.mkdir(parents=True, exist_ok=True)
    write_csv(outdir / "series_network_metrics.csv", metric_rows)
    write_csv(outdir / "series_compaction_fits.csv", fit_rows)
    (outdir / "series_compaction_fits.json").write_text(
        json.dumps(fit_rows, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    trend_checks, acceptance_rows = validate_stage_series(metric_rows, fit_rows)
    write_csv(outdir / "series_acceptance_summary.csv", acceptance_rows)
    (outdir / "series_trend_checks.json").write_text(
        json.dumps(trend_checks, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    report = render_series_report(
        metric_rows,
        fit_rows,
        trend_checks,
        acceptance_rows,
        snapshot_dir=snapshot_dir,
        pressure_curve=pressure_curve,
    )
    (outdir / "series_report.md").write_text(report, encoding="utf-8")
    summary = {
        "stage_count": len(metric_rows),
        "stages": [row["stage_id"] for row in metric_rows],
        "metrics_csv": str(outdir / "series_network_metrics.csv"),
        "fits_csv": str(outdir / "series_compaction_fits.csv"),
        "acceptance_csv": str(outdir / "series_acceptance_summary.csv"),
        "trend_checks_json": str(outdir / "series_trend_checks.json"),
        "report": str(outdir / "series_report.md"),
    }
    (outdir / "series_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return summary


def read_pressure_curve(path: Path) -> dict[str, dict[str, str]]:
    rows = read_csv(path)
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        stage_id = row.get("stage_id")
        if stage_id:
            result[stage_id] = row
    return result


def fit_rows_from_metrics(metric_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    pairs = [
        (float(row["pressure_mpa"]), float(row["actual_rho_total"]))
        for row in metric_rows
        if row.get("pressure_mpa") is not None and row.get("actual_rho_total") is not None
    ]
    if len(pairs) < 3:
        return []
    pressures = [pressure for pressure, _ in pairs]
    densities = [density for _, density in pairs]
    rows: list[dict[str, object]] = []
    for fit in compaction_fits(pressures, densities):
        rows.append(
            {
                "model": fit.model,
                "slope": fit.slope,
                "intercept": fit.intercept,
                "r2": fit.r2,
                "sample_count": fit.sample_count,
                **fit.parameters,
            }
        )
    return rows


def render_series_report(
    metric_rows: list[dict[str, object]],
    fit_rows: list[dict[str, object]],
    trend_checks: list[dict[str, object]],
    acceptance_rows: list[dict[str, object]],
    *,
    snapshot_dir: Path,
    pressure_curve: Path,
) -> str:
    lines = [
        "# Stage-Series Paper Reproduction Report",
        "",
        f"- Snapshot directory: `{snapshot_dir}`",
        f"- Pressure curve: `{pressure_curve}`",
        f"- Stage count: `{len(metric_rows)}`",
        "",
        "## Paper Evidence Map",
        "",
        "| Paper | Evidence in this run |",
        "|---|---|",
        "| Zhang | pressure/density trajectory plus contact Gini, participation, D1, and local-stress D2 by stage |",
        "| Yuan | arch count, arch strength, direction angle, and buckling angle by stage |",
        "| Liu | Heckel/Huang/Kawakita fits plus contact current, Joule heat, temperature, and neck-growth proxy |",
        "| Li | same stage schema can compare coated-powder parameter sweeps across composition, temperature, friction, speed, and aspect ratio |",
        "",
        "## Acceptance Summary",
        "",
        "| Paper | Status | Pass | Review | Missing | Mismatch |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in acceptance_rows:
        lines.append(
            f"| {row['paper']} | {row['status']} | {row['pass']} | {row['review']} | {row['missing']} | {row['mismatch']} |"
        )
    lines.extend(
        [
            "",
            "## Trend Checks",
            "",
            "| Paper | Check | Expected | Actual | Status |",
            "|---|---|---|---|---|",
        ]
    )
    for check in trend_checks:
        lines.append(
            f"| {check['paper']} | {check['label']} | {check['expected']} | {format_optional(check.get('actual'))} | {check['status']} |"
        )
    lines.extend(
        [
            "",
            "## Stage Metrics",
            "",
            "| Stage | Pressure MPa | Density | Contacts | Gini | D2 | Arches | Force-current corr |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in metric_rows:
        lines.append(
            "| {stage} | {pressure} | {density} | {contacts} | {gini} | {d2} | {arches} | {corr} |".format(
                stage=row["stage_id"],
                pressure=format_optional(row.get("pressure_mpa")),
                density=format_optional(row.get("actual_rho_total")),
                contacts=format_optional(row.get("contact_count")),
                gini=format_optional(row.get("contact_gini")),
                d2=format_optional(row.get("local_stress_inhomogeneity_d2")),
                arches=format_optional(row.get("arch_count")),
                corr=format_optional(row.get("coupling_normal_force_vs_abs_current")),
            )
        )
    lines.extend(["", "## Compaction Fits", "", "| Model | R2 | Samples | Parameters |", "|---|---:|---:|---|"])
    if fit_rows:
        for row in fit_rows:
            params = {key: value for key, value in row.items() if key not in {"model", "slope", "intercept", "r2", "sample_count"}}
            lines.append(
                f"| {row['model']} | {format_optional(row.get('r2'))} | {row['sample_count']} | `{json.dumps(params, sort_keys=True)}` |"
            )
    else:
        lines.append("| missing | missing | 0 | not enough pressure-density samples |")
    lines.extend(
        [
            "",
            "## Interpretation Notes",
            "",
            "- Contact forces inferred from overlap are a reproducibility bridge; calibrated DEM contact forces should replace them when available.",
            "- Positive force-current and heat-neck correlations support the mechanical-contact-electrothermal-densification chain.",
            "- Trend mismatches should be resolved by changing one assumption at a time: contact law, electrode selection, thermal scaling, or arch threshold.",
            "",
        ]
    )
    return "\n".join(lines)


def stage_id_from_path(path: Path) -> str:
    match = STAGE_PATTERN.search(path.stem)
    if match:
        return match.group(1)
    return path.stem


def stage_sort_key(stage_id: str) -> tuple[int, str]:
    match = re.match(r"stage(\d+)_", stage_id)
    if match:
        return int(match.group(1)), stage_id
    return 9999, stage_id


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


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


def optional_float(value) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def format_optional(value) -> str:
    if value is None:
        return "missing"
    if isinstance(value, float):
        return f"{value:.5g}"
    return str(value)
