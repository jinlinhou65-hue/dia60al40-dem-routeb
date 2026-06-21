"""Summarize Zhang pscale=2 C seed robustness recheck results."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


ZHANG_WINDOW = (572.0, 638.0)


def analyze_c_seed_recheck(
    *,
    evidence_root: Path,
    run_id: str,
    outdir: Path,
    figure_dir: Path,
    report: Path,
) -> dict[str, object]:
    run_dir = evidence_root / f"pscale2_c_seed_recheck_run_{run_id}"
    raw_rows = read_csv(run_dir / "zhang_calibration_best_by_run.csv")
    if not raw_rows:
        raise SystemExit(f"[FAIL] missing C seed recheck rows: {run_dir}")

    rows = [normalize_row(row, run_id=run_id, run_dir=run_dir) for row in raw_rows]
    outdir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    write_csv(outdir / "pscale2_c_seed_recheck_candidates.csv", rows)

    summary = summarize(rows, run_id=run_id)
    acceptance_rows = [acceptance_row(summary)]
    write_csv(outdir / "pscale2_c_seed_recheck_acceptance.csv", acceptance_rows)
    (outdir / "pscale2_c_seed_recheck_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_plot(rows, figure_dir=figure_dir)
    write_report(report, summary=summary, rows=rows, acceptance_rows=acceptance_rows)
    return summary


def normalize_row(row: dict[str, str], *, run_id: str, run_dir: Path) -> dict[str, object]:
    p95 = required_float(row, "p95_mpa")
    status = row.get("status", "")
    seed = optional_float(row.get("seed_index"))
    if seed is None:
        raise SystemExit(f"[FAIL] missing seed_index in row: {row}")
    return {
        "source_run_id": run_id,
        "source_run_dir": run_dir.as_posix(),
        "artifact": row.get("artifact", ""),
        "diamond_size_case": row.get("diamond_size_case", ""),
        "particle_count_scale": optional_float(row.get("particle_count_scale")),
        "particle_count_total": optional_float(row.get("particle_count_total")),
        "seed_index": int(seed),
        "e_al_emax_gpa": required_float(row, "e_al_emax_gpa"),
        "mu_scale": required_float(row, "mu_scale"),
        "p95_mpa": p95,
        "pressure_in_window": ZHANG_WINDOW[0] <= p95 <= ZHANG_WINDOW[1],
        "status": status,
        "trend_gate": "pass" if status == "pass" else "review",
        "calibration_diagnosis": row.get("calibration_diagnosis", ""),
        "threshold_factor": optional_float(row.get("threshold_factor")),
        "min_chain_length": optional_float(row.get("min_chain_length")),
        "participation_delta": optional_float(row.get("participation_delta")),
        "d1_delta": optional_float(row.get("d1_delta")),
        "zhang_stage_status": row.get("zhang_stage_status", ""),
    }


def summarize(rows: list[dict[str, object]], *, run_id: str) -> dict[str, object]:
    pressures = [float(row["p95_mpa"]) for row in rows]
    pass_count = sum(1 for row in rows if row["status"] == "pass")
    window_count = sum(1 for row in rows if row["pressure_in_window"])
    pass_window_count = sum(
        1 for row in rows if row["status"] == "pass" and row["pressure_in_window"]
    )
    mean = sum(pressures) / len(pressures)
    stdev = sample_stdev(pressures)
    summary = {
        "run_id": run_id,
        "row_count": len(rows),
        "diamond_size_case": "C",
        "particle_count_scale": 2,
        "e_al_emax_gpa": rows[0]["e_al_emax_gpa"],
        "mu_scale": rows[0]["mu_scale"],
        "pressure_window_mpa": list(ZHANG_WINDOW),
        "seed_count": len(rows),
        "pass_count": pass_count,
        "pressure_window_count": window_count,
        "pass_and_window_count": pass_window_count,
        "p95_min_mpa": min(pressures),
        "p95_max_mpa": max(pressures),
        "p95_mean_mpa": mean,
        "p95_stdev_mpa": stdev,
        "p95_range_mpa": max(pressures) - min(pressures),
        "p95_cv": stdev / mean if mean else None,
        "decision": decision(pass_count, window_count, pass_window_count, len(rows)),
        "recommended_next_step": recommend(pass_count, window_count, pass_window_count, len(rows)),
    }
    return summary


def decision(pass_count: int, window_count: int, pass_window_count: int, total: int) -> str:
    if pass_window_count == total:
        return "c_candidate_seed_robust"
    if pass_window_count > 0:
        return "c_candidate_not_seed_robust"
    if pass_count > 0 and window_count == 0:
        return "raise_pressure_without_losing_trend"
    return "retune_loading_path_or_contact_law"


def recommend(pass_count: int, window_count: int, pass_window_count: int, total: int) -> str:
    if pass_window_count == total:
        return "C is seed-robust at pscale=2; freeze C and continue D/E before 4x."
    return (
        f"C is not seed-robust: {pass_window_count}/{total} seeds both pass trend and fall "
        f"inside the Zhang pressure window, {window_count}/{total} are in the pressure window, "
        f"and {pass_count}/{total} pass trend. Raise pressure or adjust loading/contact law while "
        "preserving the trend gate before moving to 4x."
    )


def acceptance_row(summary: dict[str, object]) -> dict[str, object]:
    pressure_gate = "pass" if summary["pressure_window_count"] == summary["seed_count"] else "review"
    trend_gate = "pass" if summary["pass_count"] == summary["seed_count"] else "review"
    robust_gate = "pass" if summary["pass_and_window_count"] == summary["seed_count"] else "review"
    return {
        "diamond_size_case": "C",
        "artifact_imported": True,
        "workflow_completed": True,
        "seed_count": summary["seed_count"],
        "pressure_window_gate": pressure_gate,
        "trend_gate": trend_gate,
        "robust_gate": robust_gate,
        "decision": summary["decision"],
    }


def write_report(
    path: Path,
    *,
    summary: dict[str, object],
    rows: list[dict[str, object]],
    acceptance_rows: list[dict[str, object]],
) -> None:
    lines = [
        "# Zhang pscale=2 C Seed Recheck Results",
        "",
        "## Conclusion",
        "",
        str(summary["recommended_next_step"]),
        "",
        "## Seed Summary",
        "",
        "| Run | Seeds | Pass | In Pressure Window | Pass And Window | P95 Mean MPa | P95 Min | P95 Max | CV | Decision |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        "| {run} | {seeds} | {passes} | {window} | {both} | {mean:.3f} | {pmin:.3f} | {pmax:.3f} | {cv:.4f} | {decision} |".format(
            run=summary["run_id"],
            seeds=summary["seed_count"],
            passes=summary["pass_count"],
            window=summary["pressure_window_count"],
            both=summary["pass_and_window_count"],
            mean=float(summary["p95_mean_mpa"]),
            pmin=float(summary["p95_min_mpa"]),
            pmax=float(summary["p95_max_mpa"]),
            cv=float(summary["p95_cv"]),
            decision=summary["decision"],
        ),
        "",
        "## Seed Rows",
        "",
        "| Seed | P95 MPa | Pressure Gate | Trend | Participation Delta | D1 Delta | Diagnosis |",
        "|---:|---:|---|---|---:|---:|---|",
    ]
    for row in sorted(rows, key=lambda item: int(item["seed_index"])):
        lines.append(
            "| {seed} | {p95:.3f} | {pressure} | {trend} | {part} | {d1} | {diagnosis} |".format(
                seed=row["seed_index"],
                p95=float(row["p95_mpa"]),
                pressure="pass" if row["pressure_in_window"] else "review",
                trend=row["status"],
                part=format_number(row["participation_delta"]),
                d1=format_number(row["d1_delta"]),
                diagnosis=row["calibration_diagnosis"],
            )
        )
    lines.extend(
        [
            "",
            "## Acceptance",
            "",
            "| Size | Artifact | Workflow | Pressure Window | Trend | Robust | Decision |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for row in acceptance_rows:
        lines.append(
            "| {size} | pass | pass | {pressure} | {trend} | {robust} | {decision} |".format(
                size=row["diamond_size_case"],
                pressure=row["pressure_window_gate"],
                trend=row["trend_gate"],
                robust=row["robust_gate"],
                decision=row["decision"],
            )
        )
    lines.extend(
        [
            "",
            "## Files",
            "",
            "- `data/pscale2_c_seed_recheck_candidates.csv`",
            "- `data/pscale2_c_seed_recheck_acceptance.csv`",
            "- `data/pscale2_c_seed_recheck_summary.json`",
            "- `figures/pscale2_c_seed_recheck_p95.png`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def write_plot(rows: list[dict[str, object]], *, figure_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        (figure_dir / "pscale2_c_seed_recheck_plots_skipped.txt").write_text(
            "matplotlib unavailable; plots were skipped.\n",
            encoding="utf-8",
        )
        return
    ordered = sorted(rows, key=lambda item: int(item["seed_index"]))
    seeds = [int(row["seed_index"]) for row in ordered]
    pressures = [float(row["p95_mpa"]) for row in ordered]
    colors = ["#2f7d32" if row["pressure_in_window"] else "#b45309" for row in ordered]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar([str(seed) for seed in seeds], pressures, color=colors)
    ax.axhspan(ZHANG_WINDOW[0], ZHANG_WINDOW[1], color="#2f7d32", alpha=0.12)
    ax.axhline(ZHANG_WINDOW[0], color="#2f7d32", linestyle="--", linewidth=1)
    ax.axhline(ZHANG_WINDOW[1], color="#2f7d32", linestyle="--", linewidth=1)
    ax.set_xlabel("DEM seed")
    ax.set_ylabel("P95 pressure (MPa)")
    ax.set_title("Zhang pscale=2 C seed recheck")
    fig.tight_layout()
    fig.savefig(figure_dir / "pscale2_c_seed_recheck_p95.png", dpi=160)
    plt.close(fig)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def required_float(row: dict[str, str], field: str) -> float:
    number = optional_float(row.get(field))
    if number is None or not math.isfinite(number):
        raise SystemExit(f"[FAIL] row has invalid {field}: {row.get(field)!r}")
    return number


def optional_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def sample_stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))


def format_number(value: object) -> str:
    number = optional_float(value)
    if number is None:
        return "missing"
    return f"{number:.6g}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", default="docs/reproduction_goal/03_zhang_particle_scale/evidence")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--outdir", default="docs/reproduction_goal/03_zhang_particle_scale/data")
    parser.add_argument("--figure-dir", default="docs/reproduction_goal/03_zhang_particle_scale/figures")
    parser.add_argument(
        "--report",
        default="docs/reproduction_goal/03_zhang_particle_scale/pscale2_c_seed_recheck_report.md",
    )
    args = parser.parse_args()

    summary = analyze_c_seed_recheck(
        evidence_root=Path(args.evidence_root),
        run_id=args.run_id,
        outdir=Path(args.outdir),
        figure_dir=Path(args.figure_dir),
        report=Path(args.report),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
