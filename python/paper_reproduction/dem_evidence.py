from __future__ import annotations

import json
from pathlib import Path

from .dem_evidence_checks import (
    exact_string_check,
    file_check,
    file_glob_check,
    format_value,
    int_value,
    missing_check,
    model_check,
    numeric_first,
    numeric_last,
    parse_runtime_controls,
    positive_scalar_check,
    read_csv_or_empty,
    read_model_parameters,
    scalar_check,
    set_check,
    summarize_checks,
    tolerance_check,
    trend_check,
)
from .validation import write_csv


EXPECTED_STAGES = [
    "stage0_preload",
    "stage1_rho065",
    "stage2_rho072",
    "stage3_rho080",
    "stage4_rho088",
    "stage5_rho095",
]
EXPECTED_PAPERS = ["Li", "Liu", "Yuan", "Zhang"]


def validate_dem_evidence(
    dem_dir: Path,
    *,
    expected_stage_count: int = 6,
    final_density_target: float = 0.95,
    density_tolerance: float = 1e-5,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    checks: list[dict[str, object]] = []
    curve_path = dem_dir / "pressure_density_curve.csv"
    summary_path = dem_dir / "pressure_density_summary.csv"
    model_path = dem_dir / "model_parameters.csv"
    paper_dir = dem_dir / "paper_reproduction"
    metrics_path = paper_dir / "series_network_metrics.csv"
    fits_path = paper_dir / "series_compaction_fits.csv"
    acceptance_path = paper_dir / "series_acceptance_summary.csv"
    rendered_deck = dem_dir.parent / "in.dia60al40_dem_staged.rendered.liggghts"

    for path in [
        model_path,
        curve_path,
        summary_path,
        metrics_path,
        fits_path,
        acceptance_path,
        paper_dir / "series_report.md",
        dem_dir / "plots" / "pressure_density_curve.png",
    ]:
        checks.append(file_check("files", path, dem_dir))

    model = read_model_parameters(model_path)
    expected_particles = (
        int_value(model, "Al_count")
        + int_value(model, "diamond_count_DS")
        + int_value(model, "diamond_count_DL")
    )
    curve_rows = read_csv_or_empty(curve_path)
    metric_rows = read_csv_or_empty(metrics_path)
    fit_rows = read_csv_or_empty(fits_path)
    acceptance_rows = read_csv_or_empty(acceptance_path)

    checks.extend(
        [
            scalar_check(
                "dem",
                "pressure-density curve has all stages",
                len(curve_rows),
                expected_stage_count,
                comparator="==",
                evidence=str(curve_path),
            ),
            set_check(
                "dem",
                "pressure-density curve includes expected stage ids",
                [row.get("stage_id", "") for row in curve_rows],
                EXPECTED_STAGES[:expected_stage_count],
                evidence=str(curve_path),
            ),
            trend_check(
                "dem",
                "density rises through compaction",
                curve_rows,
                "actual_rho_total",
                "increasing",
                evidence=str(curve_path),
            ),
            trend_check(
                "dem",
                "pressure rises overall",
                curve_rows,
                "pressure_mpa",
                "increasing",
                evidence=str(curve_path),
            ),
            tolerance_check(
                "dem",
                "final density reaches target",
                numeric_last(curve_rows, "actual_rho_total"),
                final_density_target,
                density_tolerance,
                evidence=str(curve_path),
            ),
            positive_scalar_check(
                "dem",
                "final pressure is finite and positive",
                numeric_last(curve_rows, "pressure_mpa"),
                evidence=str(curve_path),
            ),
            positive_scalar_check(
                "dem",
                "p_target_mpa is finite and positive",
                numeric_first(read_csv_or_empty(summary_path), "p_target_mpa"),
                evidence=str(summary_path),
            ),
        ]
    )

    for stage in EXPECTED_STAGES[:expected_stage_count]:
        handoff_path = dem_dir / f"dem_fem_handoff_{stage}.csv"
        checks.extend(
            [
                file_glob_check("stage", f"{stage} dump exists", dem_dir / f"{stage}_*.dump"),
                file_check("stage", dem_dir / f"{stage}.restart", dem_dir),
                file_check("stage", handoff_path, dem_dir),
            ]
        )
        if expected_particles > 0:
            checks.append(
                scalar_check(
                    "stage",
                    f"{stage} handoff particle count",
                    len(read_csv_or_empty(handoff_path)),
                    expected_particles,
                    comparator="==",
                    evidence=str(handoff_path),
                )
            )

    checks.extend(
        [
            scalar_check(
                "paper",
                "paper stage-series metrics cover all stages",
                len(metric_rows),
                expected_stage_count,
                comparator="==",
                evidence=str(metrics_path),
            ),
            set_check(
                "paper",
                "paper acceptance covers all papers",
                [row.get("paper", "") for row in acceptance_rows],
                EXPECTED_PAPERS,
                evidence=str(acceptance_path),
            ),
        ]
    )
    for row in acceptance_rows:
        checks.append(
            exact_string_check(
                "paper",
                f"{row.get('paper', 'unknown')} paper acceptance status",
                row.get("status"),
                "pass",
                evidence=str(acceptance_path),
            )
        )
    checks.extend(
        [
            model_check("paper", "Heckel fit is available", fit_rows, "Heckel", evidence=str(fits_path)),
            model_check("paper", "Kawakita fit is available", fit_rows, "Kawakita", evidence=str(fits_path)),
        ]
    )

    if rendered_deck.exists():
        runtime = parse_runtime_controls(rendered_deck)
        checks.extend(
            [
                positive_scalar_check(
                    "runtime",
                    "rendered top velocity is positive",
                    runtime.get("top_vel_cm_s"),
                    evidence=str(rendered_deck),
                ),
                positive_scalar_check(
                    "runtime",
                    "rendered timestep is positive",
                    runtime.get("dt_seconds"),
                    evidence=str(rendered_deck),
                ),
            ]
        )
    else:
        checks.append(missing_check("runtime", "rendered deck is available", str(rendered_deck)))

    return checks, summarize_checks(checks)


def write_dem_evidence_outputs(dem_dir: Path, outdir: Path | None = None) -> dict[str, Path]:
    target_dir = outdir or (dem_dir / "paper_reproduction")
    checks, summary = validate_dem_evidence(dem_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    checks_path = target_dir / "dem_evidence_checks.json"
    summary_path = target_dir / "dem_evidence_summary.csv"
    report_path = target_dir / "dem_evidence_report.md"
    checks_path.write_text(json.dumps(checks, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(summary_path, summary)
    report_path.write_text(render_dem_evidence_report(checks, summary, dem_dir=dem_dir), encoding="utf-8")
    return {"checks": checks_path, "summary": summary_path, "report": report_path}


def render_dem_evidence_report(
    checks: list[dict[str, object]],
    summary: list[dict[str, object]],
    *,
    dem_dir: Path,
) -> str:
    overall = summary[0] if summary else {"status": "missing"}
    lines = [
        "# DEM Evidence Validation Report",
        "",
        f"- DEM directory: `{dem_dir}`",
        f"- Overall status: `{overall['status']}`",
        "",
        "## Summary",
        "",
        "| Status | Pass | Review | Missing | Mismatch | Check Count |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            f"| {row['status']} | {row['pass']} | {row['review']} | "
            f"{row['missing']} | {row['mismatch']} | {row['check_count']} |"
        )
    lines.extend(
        [
            "",
            "## Checks",
            "",
            "| Domain | Check | Expected | Actual | Status | Evidence |",
            "|---|---|---|---|---|---|",
        ]
    )
    for check in checks:
        lines.append(
            "| {domain} | {label} | {expected} | {actual} | {status} | `{evidence}` |".format(
                domain=check["domain"],
                label=check["label"],
                expected=check["expected"],
                actual=format_value(check.get("actual")),
                status=check["status"],
                evidence=check.get("evidence", ""),
            )
        )
    lines.append("")
    return "\n".join(lines)
