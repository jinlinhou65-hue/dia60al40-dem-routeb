"""Summarize imported Zhang size-specific DEM sweep evidence."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = REPO_ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from paper_reproduction.zhang_calibration_ensemble import (  # noqa: E402
    ZHANG_ENDPOINT_WINDOW_MPA,
    pressure_in_endpoint_window,
)


DEFAULT_RUN_IDS = ["27874059503", "27874061902", "27874064063"]


def summarize_size_specific_imports(
    *,
    docs_root: Path,
    run_ids: list[str],
    outdir: Path,
) -> dict[str, object]:
    imported_runs = []
    best_rows: list[dict[str, object]] = []
    for run_id in run_ids:
        run_dir = docs_root / f"run_{run_id}"
        rows = read_csv(run_dir / "zhang_calibration_best_by_run.csv")
        if not rows:
            raise SystemExit(f"[FAIL] missing best-by-run rows for {run_id}: {run_dir}")
        metadata = read_json(run_dir / "import_metadata.json")
        imported_runs.append(
            {
                "run_id": run_id,
                "workflow_url": metadata.get(
                    "workflow_url",
                    f"https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/{run_id}",
                ),
                "run_dir": run_dir.as_posix(),
                "row_count": len(rows),
            }
        )
        for row in rows:
            row = dict(row)
            row["source_run_id"] = run_id
            best_rows.append(normalize_row(row))

    size_summary = summarize_by_size(best_rows)
    overall = summarize_overall(best_rows)
    outdir.mkdir(parents=True, exist_ok=True)
    write_csv(outdir / "combined_best_by_run.csv", best_rows)
    write_csv(outdir / "combined_size_summary.csv", size_summary)
    summary = {
        "run_ids": run_ids,
        "imported_runs": imported_runs,
        "row_count": len(best_rows),
        "status_pass_count": overall["status_pass_count"],
        "pressure_window_count": overall["pressure_window_count"],
        "passing_window_count": overall["passing_window_count"],
        "zhang_pressure_window_mpa": list(ZHANG_ENDPOINT_WINDOW_MPA),
        "size_summary": size_summary,
    }
    (outdir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (outdir / "README.md").write_text(
        render_summary(summary),
        encoding="utf-8",
        newline="\n",
    )
    return summary


def summarize_by_size(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("diamond_size_case")), []).append(row)

    output: list[dict[str, object]] = []
    for size, group in sorted(grouped.items()):
        pressures = finite_values(group, "p95_mpa")
        passing_window = [
            row
            for row in group
            if row.get("status") == "pass"
            and pressure_in_endpoint_window(optional_float(row.get("p95_mpa")))
        ]
        best = sorted(group, key=size_candidate_sort_key)[0]
        output.append(
            {
                "diamond_size_case": size,
                "run_count": len(group),
                "pass_run_count": sum(1 for row in group if row.get("status") == "pass"),
                "pressure_window_count": sum(
                    1
                    for row in group
                    if pressure_in_endpoint_window(optional_float(row.get("p95_mpa")))
                ),
                "passing_window_count": len(passing_window),
                "p95_mean_mpa": mean(pressures),
                "p95_min_mpa": min(pressures) if pressures else None,
                "p95_max_mpa": max(pressures) if pressures else None,
                "best_artifact": best.get("artifact"),
                "best_e_al_emax_gpa": best.get("e_al_emax_gpa"),
                "best_mu_scale": best.get("mu_scale"),
                "best_p95_mpa": best.get("p95_mpa"),
                "best_status": best.get("status"),
                "best_source_run_id": best.get("source_run_id"),
            }
        )
    return output


def summarize_overall(rows: list[dict[str, object]]) -> dict[str, int]:
    pressure_window_count = sum(
        1
        for row in rows
        if pressure_in_endpoint_window(optional_float(row.get("p95_mpa")))
    )
    status_pass_count = sum(1 for row in rows if row.get("status") == "pass")
    passing_window_count = sum(
        1
        for row in rows
        if row.get("status") == "pass"
        and pressure_in_endpoint_window(optional_float(row.get("p95_mpa")))
    )
    return {
        "status_pass_count": status_pass_count,
        "pressure_window_count": pressure_window_count,
        "passing_window_count": passing_window_count,
    }


def size_candidate_sort_key(row: dict[str, object]) -> tuple[int, int, float, int, float]:
    pressure = optional_float(row.get("p95_mpa"))
    status_rank = 0 if row.get("status") == "pass" else 1
    pressure_rank = 0 if pressure_in_endpoint_window(pressure) else 1
    pressure_distance = abs(pressure - 600.0) if pressure is not None else math.inf
    d1_delta = optional_float(row.get("d1_delta"))
    participation_delta = optional_float(row.get("participation_delta"))
    return (
        status_rank,
        pressure_rank,
        pressure_distance,
        0 if participation_delta is not None and participation_delta > 0 else 1,
        d1_delta if d1_delta is not None else math.inf,
    )


def render_summary(summary: dict[str, object]) -> str:
    lines = [
        "# Zhang Size-Specific Sweep Summary",
        "",
        f"- Imported DEM runs: `{', '.join(summary['run_ids'])}`",
        f"- Best-row count: `{summary['row_count']}`",
        f"- Zhang pass rows: `{summary['status_pass_count']}`",
        f"- Pressure-window rows: `{summary['pressure_window_count']}`",
        f"- Pass + pressure-window rows: `{summary['passing_window_count']}`",
        f"- Pressure window: `{summary['zhang_pressure_window_mpa'][0]}-{summary['zhang_pressure_window_mpa'][1]} MPa`",
        "",
        "## Imported Runs",
        "",
        "| Run | Rows | URL |",
        "|---|---:|---|",
    ]
    for run in summary["imported_runs"]:
        lines.append(
            f"| {run['run_id']} | {run['row_count']} | {run['workflow_url']} |"
        )
    lines.extend(
        [
            "",
            "## Size Summary",
            "",
            "| Size | Runs | Pass | Pressure Window | Pass + Window | P95 Mean MPa | P95 Min | P95 Max | Best Artifact |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in summary["size_summary"]:
        lines.append(
            "| {size} | {runs} | {passes} | {window} | {passing_window} | {mean} | {pmin} | {pmax} | {best} |".format(
                size=row.get("diamond_size_case"),
                runs=row.get("run_count"),
                passes=row.get("pass_run_count"),
                window=row.get("pressure_window_count"),
                passing_window=row.get("passing_window_count"),
                mean=format_number(row.get("p95_mean_mpa")),
                pmin=format_number(row.get("p95_min_mpa")),
                pmax=format_number(row.get("p95_max_mpa")),
                best=row.get("best_artifact"),
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This report combines the C, D, and E size-specific light DEM sweeps. "
            "Rows that pass both the Zhang force-chain trend gate and the 572-638 MPa "
            "endpoint pressure window are the immediate candidates for the next "
            "higher-fidelity Zhang reproduction step.",
            "",
        ]
    )
    return "\n".join(lines)


def normalize_row(row: dict[str, object]) -> dict[str, object]:
    output = dict(row)
    for field in (
        "seed_index",
        "e_al_emax_gpa",
        "mu_scale",
        "p95_mpa",
        "threshold_factor",
        "min_chain_length",
        "participation_delta",
        "d1_delta",
    ):
        value = optional_float(output.get(field))
        if value is not None:
            output[field] = value
    return output


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = sorted({field for row in rows for field in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def finite_values(rows: list[dict[str, object]], field: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = optional_float(row.get(field))
        if value is not None and math.isfinite(value):
            values.append(value)
    return values


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def optional_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def format_number(value: object) -> str:
    number = optional_float(value)
    if number is None:
        return "missing"
    return f"{number:.6g}"


def parse_run_ids(value: str) -> list[str]:
    parsed = json.loads(value)
    if not isinstance(parsed, list) or not parsed:
        raise SystemExit("[FAIL] run ids must be a non-empty JSON list")
    return [str(item) for item in parsed]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs-root", default="docs/zhang_sweep_evidence")
    parser.add_argument("--run-ids-json", default=json.dumps(DEFAULT_RUN_IDS))
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()

    summary = summarize_size_specific_imports(
        docs_root=Path(args.docs_root),
        run_ids=parse_run_ids(args.run_ids_json),
        outdir=Path(args.outdir),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
