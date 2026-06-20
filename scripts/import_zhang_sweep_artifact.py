"""Import a Zhang DEM sweep ensemble artifact into versioned docs."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path


SELECTED_FILES = [
    "ensemble_runs.csv",
    "ensemble_pressure_summary.csv",
    "ensemble_pressure_summary_by_size_case.csv",
    "zhang_calibration_candidates.csv",
    "zhang_calibration_best_by_run.csv",
    "zhang_calibration_group_summary.csv",
    "zhang_calibration_ensemble_report.md",
    "zhang_next_sweep_recommendation.json",
    "zhang_next_sweep_recommendation.md",
]


def import_zhang_sweep_artifact(
    *,
    artifact_dir: Path,
    run_id: str,
    workflow_url: str,
    outdir: Path,
) -> dict[str, object]:
    if not artifact_dir.exists():
        raise SystemExit(f"[FAIL] artifact directory does not exist: {artifact_dir}")
    best_rows = read_csv(artifact_dir / "zhang_calibration_best_by_run.csv")
    group_rows = read_csv(artifact_dir / "zhang_calibration_group_summary.csv")
    pressure_rows = read_csv(artifact_dir / "ensemble_pressure_summary.csv")
    recommendation = read_json(artifact_dir / "zhang_next_sweep_recommendation.json")
    if not best_rows:
        raise SystemExit("[FAIL] artifact is missing Zhang best-by-run rows")

    outdir.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for name in SELECTED_FILES:
        source = artifact_dir / name
        if source.exists():
            shutil.copy2(source, outdir / name)
            copied.append(name)

    summary = render_summary(
        run_id=run_id,
        workflow_url=workflow_url,
        best_rows=best_rows,
        group_rows=group_rows,
        pressure_rows=pressure_rows,
        recommendation=recommendation,
        copied=copied,
    )
    readme = outdir / "README.md"
    readme.write_text(summary, encoding="utf-8", newline="\n")
    metadata = {
        "run_id": run_id,
        "workflow_url": workflow_url,
        "source_artifact": "dia60al40-dem-ensemble-summary",
        "best_row_count": len(best_rows),
        "group_row_count": len(group_rows),
        "copied_files": copied,
        "readme": str(readme),
    }
    (outdir / "import_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metadata


def render_summary(
    *,
    run_id: str,
    workflow_url: str,
    best_rows: list[dict[str, str]],
    group_rows: list[dict[str, str]],
    pressure_rows: list[dict[str, str]],
    recommendation: dict[str, object],
    copied: list[str],
) -> str:
    lines = [
        "# Zhang Sweep Artifact Report",
        "",
        f"- DEM workflow run: [{run_id}]({workflow_url})",
        "- Source artifact: `dia60al40-dem-ensemble-summary`",
        f"- DEM runs summarized: `{len(best_rows)}`",
        "",
    ]
    if pressure_rows:
        pressure = pressure_rows[0]
        lines.extend(
            [
                "## Pressure Ensemble",
                "",
                "| Runs | Mean P95 MPa | Min | Max | Range | CV |",
                "|---:|---:|---:|---:|---:|---:|",
                "| {runs} | {mean} | {pmin} | {pmax} | {prange} | {cv} |".format(
                    runs=pressure.get("n_runs", "missing"),
                    mean=format_cell(pressure.get("p95_mean_mpa")),
                    pmin=format_cell(pressure.get("p95_min_mpa")),
                    pmax=format_cell(pressure.get("p95_max_mpa")),
                    prange=format_cell(pressure.get("p95_range_mpa")),
                    cv=format_cell(pressure.get("p95_cv")),
                ),
                "",
            ]
        )

    lines.extend(
        [
            "## Best Zhang Candidate By DEM Run",
            "",
            "| Artifact | Emax GPa | Mu | P95 MPa | Status | Diagnosis | Threshold | Min Chain | Participation Delta | D1 Delta |",
            "|---|---:|---:|---:|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in sorted(best_rows, key=best_sort_key):
        lines.append(
            "| {artifact} | {emax} | {mu} | {p95} | {status} | {diagnosis} | {threshold} | {chain} | {participation} | {d1} |".format(
                artifact=row.get("artifact", "missing"),
                emax=format_cell(row.get("e_al_emax_gpa")),
                mu=format_cell(row.get("mu_scale")),
                p95=format_cell(row.get("p95_mpa")),
                status=row.get("status", "missing"),
                diagnosis=row.get("calibration_diagnosis", "missing"),
                threshold=format_cell(row.get("threshold_factor")),
                chain=format_cell(row.get("min_chain_length")),
                participation=format_cell(row.get("participation_delta")),
                d1=format_cell(row.get("d1_delta")),
            )
        )
    lines.append("")

    if group_rows:
        lines.extend(
            [
                "## Group Summary",
                "",
                "| Group | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |",
                "|---|---|---:|---:|---:|---:|",
            ]
        )
        for row in group_rows:
            lines.append(
                "| {group} | {value} | {runs} | {passes} | {participation} | {d1} |".format(
                    group=row.get("group_by", "missing"),
                    value=row.get("group_value", "missing"),
                    runs=row.get("run_count", "missing"),
                    passes=row.get("pass_run_count", "missing"),
                    participation=format_cell(row.get("participation_delta_mean")),
                    d1=format_cell(row.get("d1_delta_mean")),
                )
            )
        lines.append("")

    if recommendation:
        inputs = recommendation.get("workflow_dispatch_inputs", {})
        lines.extend(
            [
                "## Next Recommendation",
                "",
                f"- Diagnosis: `{recommendation.get('diagnosis', 'missing')}`",
                f"- Estimated run count: `{recommendation.get('estimated_run_count', 'missing')}`",
                f"- Reason: {recommendation.get('reason', 'missing')}",
                "",
                "```json",
                json.dumps(inputs, ensure_ascii=False, indent=2, sort_keys=True),
                "```",
                "",
            ]
        )

    lines.extend(
        [
            "## Imported Files",
            "",
            *[f"- `{name}`" for name in copied],
            "",
        ]
    )
    return "\n".join(lines)


def best_sort_key(row: dict[str, str]) -> tuple[float, float, str]:
    return (
        optional_float(row.get("e_al_emax_gpa")) or 0.0,
        optional_float(row.get("mu_scale")) or 0.0,
        row.get("artifact", ""),
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def optional_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def format_cell(value: object) -> str:
    number = optional_float(value)
    if number is None:
        return "missing" if value in (None, "") else str(value)
    return f"{number:.6g}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--workflow-url", required=True)
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()

    metadata = import_zhang_sweep_artifact(
        artifact_dir=Path(args.artifact_dir),
        run_id=args.run_id,
        workflow_url=args.workflow_url,
        outdir=Path(args.outdir),
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
