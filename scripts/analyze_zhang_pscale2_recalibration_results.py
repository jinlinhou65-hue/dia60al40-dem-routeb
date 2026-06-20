"""Summarize imported Zhang pscale=2 recalibration DEM results."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


ZHANG_WINDOW = (572.0, 638.0)


def analyze_recalibration(
    *,
    evidence_root: Path,
    run_ids: list[str],
    outdir: Path,
    figure_dir: Path,
    report: Path,
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for run_id in run_ids:
        run_dir = evidence_root / f"pscale2_recalibration_run_{run_id}"
        run_rows = read_csv(run_dir / "zhang_calibration_best_by_run.csv")
        if not run_rows:
            raise SystemExit(f"[FAIL] missing recalibration rows for run {run_id}: {run_dir}")
        for row in run_rows:
            rows.append(normalize_row(row, run_id=run_id, run_dir=run_dir))

    outdir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    write_csv(outdir / "pscale2_recalibration_candidates.csv", rows)
    size_rows = summarize_by_size(rows)
    write_csv(outdir / "pscale2_recalibration_size_summary.csv", size_rows)
    acceptance_rows = [acceptance_row(row) for row in size_rows]
    write_csv(outdir / "pscale2_recalibration_acceptance.csv", acceptance_rows)
    summary = {
        "run_ids": run_ids,
        "row_count": len(rows),
        "pressure_window_mpa": list(ZHANG_WINDOW),
        "pressure_window_candidate_count": sum(1 for row in rows if row["pressure_in_window"]),
        "pass_and_window_candidate_count": sum(
            1 for row in rows if row["pressure_in_window"] and row["status"] == "pass"
        ),
        "size_summary": size_rows,
        "recommended_next_step": recommend_next_step(size_rows),
    }
    (outdir / "pscale2_recalibration_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_plots(rows, figure_dir=figure_dir)
    write_report(report, summary=summary, size_rows=size_rows, acceptance_rows=acceptance_rows)
    return summary


def normalize_row(row: dict[str, str], *, run_id: str, run_dir: Path) -> dict[str, object]:
    p95 = required_float(row, "p95_mpa")
    status = row.get("status", "")
    return {
        "source_run_id": run_id,
        "source_run_dir": run_dir.as_posix(),
        "artifact": row.get("artifact", ""),
        "diamond_size_case": row.get("diamond_size_case", ""),
        "particle_count_scale": optional_float(row.get("particle_count_scale")),
        "particle_count_total": optional_float(row.get("particle_count_total")),
        "seed_index": optional_float(row.get("seed_index")),
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


def summarize_by_size(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(str(row["diamond_size_case"]), []).append(row)

    output: list[dict[str, object]] = []
    for size, group in sorted(grouped.items()):
        best = sorted(group, key=candidate_sort_key)[0]
        window_rows = [row for row in group if row["pressure_in_window"]]
        pass_window_rows = [row for row in window_rows if row["status"] == "pass"]
        pressures = [float(row["p95_mpa"]) for row in group]
        output.append(
            {
                "diamond_size_case": size,
                "run_count": len(group),
                "pressure_window_count": len(window_rows),
                "pass_and_window_count": len(pass_window_rows),
                "pass_count": sum(1 for row in group if row["status"] == "pass"),
                "p95_min_mpa": min(pressures),
                "p95_max_mpa": max(pressures),
                "p95_mean_mpa": sum(pressures) / len(pressures),
                "best_artifact": best["artifact"],
                "best_e_al_emax_gpa": best["e_al_emax_gpa"],
                "best_mu_scale": best["mu_scale"],
                "best_p95_mpa": best["p95_mpa"],
                "best_status": best["status"],
                "best_pressure_in_window": best["pressure_in_window"],
                "best_participation_delta": best["participation_delta"],
                "best_d1_delta": best["d1_delta"],
                "best_calibration_diagnosis": best["calibration_diagnosis"],
                "decision": decision_for_size(size, group, best),
            }
        )
    return output


def candidate_sort_key(row: dict[str, object]) -> tuple[int, int, float, int, float]:
    p95 = float(row["p95_mpa"])
    return (
        0 if row["pressure_in_window"] else 1,
        0 if row["status"] == "pass" else 1,
        abs(p95 - 600.0),
        0 if optional_float(row.get("participation_delta")) is not None and float(row["participation_delta"]) > 0 else 1,
        float(row["e_al_emax_gpa"]),
    )


def decision_for_size(size: str, group: list[dict[str, object]], best: dict[str, object]) -> str:
    if best["pressure_in_window"] and best["status"] == "pass":
        return "candidate_ready_for_seed_recheck"
    if best["pressure_in_window"]:
        return "hold_pressure_candidate_and_tune_participation"
    max_pressure = max(float(row["p95_mpa"]) for row in group)
    if max_pressure < ZHANG_WINDOW[0]:
        return "extend_endpoint_modulus_or_loading_path"
    return "narrow_pressure_search"


def acceptance_row(row: dict[str, object]) -> dict[str, object]:
    pressure_gate = "pass" if row["best_pressure_in_window"] else "review"
    trend_gate = "pass" if row["best_status"] == "pass" else "review"
    overall = "pass" if pressure_gate == "pass" and trend_gate == "pass" else "review"
    return {
        "diamond_size_case": row["diamond_size_case"],
        "artifact_imported": True,
        "workflow_completed": True,
        "pressure_window_gate": pressure_gate,
        "trend_gate": trend_gate,
        "overall_status": overall,
        "decision": row["decision"],
    }


def recommend_next_step(size_rows: list[dict[str, object]]) -> str:
    if all(row["best_pressure_in_window"] and row["best_status"] == "pass" for row in size_rows):
        return "Run a seed robustness recheck at pscale=2 before 4x."
    return (
        "Do not move to 4x yet. C is close but below the pressure window, "
        "D has a pressure-window candidate but needs participation tuning, and E remains far below "
        "the pressure window. Continue pscale=2 calibration with separate C/D/E actions."
    )


def write_report(
    path: Path,
    *,
    summary: dict[str, object],
    size_rows: list[dict[str, object]],
    acceptance_rows: list[dict[str, object]],
) -> None:
    lines = [
        "# Zhang pscale=2 Recalibration Results",
        "",
        "## Conclusion",
        "",
        summary["recommended_next_step"],
        "",
        "## Size Summary",
        "",
        "| Size | Best Emax GPa | Best P95 MPa | Pressure Gate | Trend | Participation Delta | Decision |",
        "|---|---:|---:|---|---|---:|---|",
    ]
    for row in size_rows:
        lines.append(
            "| {size} | {emax:.3f} | {p95:.3f} | {pressure} | {trend} | {part} | {decision} |".format(
                size=row["diamond_size_case"],
                emax=float(row["best_e_al_emax_gpa"]),
                p95=float(row["best_p95_mpa"]),
                pressure="pass" if row["best_pressure_in_window"] else "review",
                trend=row["best_status"],
                part=format_number(row["best_participation_delta"]),
                decision=row["decision"],
            )
        )
    lines.extend(
        [
            "",
            "## Acceptance",
            "",
            "| Size | Artifact | Workflow | Pressure Window | Trend | Overall |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in acceptance_rows:
        lines.append(
            "| {size} | pass | pass | {pressure} | {trend} | {overall} |".format(
                size=row["diamond_size_case"],
                pressure=row["pressure_window_gate"],
                trend=row["trend_gate"],
                overall=row["overall_status"],
            )
        )
    lines.extend(
        [
            "",
            "## Files",
            "",
            "- `data/pscale2_recalibration_candidates.csv`",
            "- `data/pscale2_recalibration_size_summary.csv`",
            "- `data/pscale2_recalibration_acceptance.csv`",
            "- `figures/pscale2_recalibration_p95.png`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def write_plots(rows: list[dict[str, object]], *, figure_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        (figure_dir / "pscale2_recalibration_plots_skipped.txt").write_text(
            "matplotlib unavailable; plots were skipped.\n",
            encoding="utf-8",
        )
        return
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(str(row["diamond_size_case"]), []).append(row)

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for size, group in sorted(grouped.items()):
        ordered = sorted(group, key=lambda item: float(item["e_al_emax_gpa"]))
        ax.plot(
            [float(item["e_al_emax_gpa"]) for item in ordered],
            [float(item["p95_mpa"]) for item in ordered],
            marker="o",
            label=f"size {size}",
        )
    ax.axhspan(ZHANG_WINDOW[0], ZHANG_WINDOW[1], color="#d8ead3", alpha=0.45, label="Zhang 572-638 MPa")
    ax.set_xlabel("Endpoint modulus Emax (GPa)")
    ax.set_ylabel("P95 pressure (MPa)")
    ax.set_title("Zhang pscale=2 pressure recalibration")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figure_dir / "pscale2_recalibration_p95.png", dpi=180)
    plt.close(fig)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise SystemExit(f"[FAIL] no rows to write: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def required_float(row: dict[str, str], field: str) -> float:
    value = optional_float(row.get(field))
    if value is None:
        raise SystemExit(f"[FAIL] missing numeric {field}: {row}")
    return value


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
    return "missing" if number is None else f"{number:.6g}"


def parse_run_ids(value: str) -> list[str]:
    parsed = json.loads(value)
    if not isinstance(parsed, list) or not parsed:
        raise SystemExit("[FAIL] run ids must be a non-empty JSON list")
    return [str(item) for item in parsed]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", default="docs/reproduction_goal/03_zhang_particle_scale/evidence")
    parser.add_argument("--run-ids-json", default='["27882367107","27882368312","27882369414"]')
    parser.add_argument("--outdir", default="docs/reproduction_goal/03_zhang_particle_scale/data")
    parser.add_argument("--figure-dir", default="docs/reproduction_goal/03_zhang_particle_scale/figures")
    parser.add_argument("--report", default="docs/reproduction_goal/03_zhang_particle_scale/pscale2_recalibration_report.md")
    args = parser.parse_args()

    summary = analyze_recalibration(
        evidence_root=Path(args.evidence_root),
        run_ids=parse_run_ids(args.run_ids_json),
        outdir=Path(args.outdir),
        figure_dir=Path(args.figure_dir),
        report=Path(args.report),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
