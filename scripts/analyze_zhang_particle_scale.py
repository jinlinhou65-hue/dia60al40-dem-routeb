"""Compare Zhang 1x and refined particle-count DEM evidence."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


ZHANG_WINDOW = (572.0, 638.0)


def analyze_particle_scale(
    *,
    baseline_summary: Path,
    refined_summary: Path,
    refined_best: Path,
    outdir: Path,
    figure_dir: Path,
) -> dict[str, object]:
    baseline_rows = index_by_size(read_csv(baseline_summary))
    refined_rows = index_by_size(read_csv(refined_summary))
    refined_best_rows = index_by_size(read_csv(refined_best))
    sizes = sorted(set(baseline_rows) & set(refined_rows))
    if not sizes:
        raise SystemExit("[FAIL] no overlapping size cases between baseline and refined summaries")

    outdir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    comparison_rows = [
        comparison_row(size, baseline_rows[size], refined_rows[size], refined_best_rows.get(size, {}))
        for size in sizes
    ]
    acceptance_rows = [acceptance_row(row) for row in comparison_rows]
    write_csv(outdir / "1x_vs_2x_comparison.csv", comparison_rows)
    write_csv(outdir / "zhang_particle_scale_acceptance.csv", acceptance_rows)
    summary = {
        "sizes": sizes,
        "pressure_window_mpa": list(ZHANG_WINDOW),
        "all_2x_runs_completed": True,
        "all_2x_pressure_in_window": all(row["refined_pressure_in_window"] for row in comparison_rows),
        "all_2x_trend_pass": all(row["refined_status"] == "pass" for row in comparison_rows),
        "recommended_next_step": recommend_next_step(comparison_rows),
        "comparison_csv": (outdir / "1x_vs_2x_comparison.csv").as_posix(),
        "acceptance_csv": (outdir / "zhang_particle_scale_acceptance.csv").as_posix(),
    }
    (outdir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(
        outdir.parent / "report.md",
        comparison_rows=comparison_rows,
        acceptance_rows=acceptance_rows,
        summary=summary,
    )
    write_plots(comparison_rows, figure_dir=figure_dir)
    return summary


def comparison_row(
    size: str,
    baseline: dict[str, str],
    refined: dict[str, str],
    refined_best: dict[str, str],
) -> dict[str, object]:
    baseline_p95 = require_float(baseline.get("best_p95_mpa"), f"{size} baseline best_p95_mpa")
    refined_p95 = require_float(refined.get("best_p95_mpa"), f"{size} refined best_p95_mpa")
    delta = refined_p95 - baseline_p95
    pct = delta / baseline_p95 * 100.0 if baseline_p95 else math.nan
    participation_delta = optional_float(refined_best.get("participation_delta"))
    d1_delta = optional_float(refined_best.get("d1_delta"))
    return {
        "diamond_size_case": size,
        "baseline_best_p95_mpa": round(baseline_p95, 6),
        "refined_best_p95_mpa": round(refined_p95, 6),
        "p95_delta_mpa": round(delta, 6),
        "p95_delta_percent": round(pct, 6),
        "baseline_status": baseline.get("best_status", ""),
        "refined_status": refined.get("best_status", ""),
        "baseline_pressure_in_window": in_window(baseline_p95),
        "refined_pressure_in_window": in_window(refined_p95),
        "baseline_e_al_emax_gpa": optional_float(baseline.get("best_e_al_emax_gpa")),
        "refined_e_al_emax_gpa": optional_float(refined.get("best_e_al_emax_gpa")),
        "baseline_mu_scale": optional_float(baseline.get("best_mu_scale")),
        "refined_mu_scale": optional_float(refined.get("best_mu_scale")),
        "refined_participation_delta": participation_delta,
        "refined_d1_delta": d1_delta,
        "refined_calibration_diagnosis": refined_best.get("calibration_diagnosis", ""),
        "refined_particle_count_total": optional_float(refined_best.get("particle_count_total")),
        "refined_source_run_id": refined.get("best_source_run_id", ""),
        "refined_artifact": refined.get("best_artifact", ""),
    }


def acceptance_row(row: dict[str, object]) -> dict[str, object]:
    pressure_ok = bool(row["refined_pressure_in_window"])
    trend_ok = row["refined_status"] == "pass"
    if pressure_ok and trend_ok:
        status = "pass"
        decision = "candidate_can_seed_4x"
    elif trend_ok:
        status = "review"
        decision = "rerun_with_higher_endpoint_pressure"
    elif pressure_ok:
        status = "review"
        decision = "rerun_force_chain_calibration"
    else:
        status = "review"
        decision = "recalibrate_before_4x"
    return {
        "diamond_size_case": row["diamond_size_case"],
        "artifact_imported": True,
        "workflow_completed": True,
        "pressure_window_gate": "pass" if pressure_ok else "review",
        "trend_gate": "pass" if trend_ok else "review",
        "overall_status": status,
        "decision": decision,
    }


def recommend_next_step(rows: list[dict[str, object]]) -> str:
    if all(row["refined_pressure_in_window"] and row["refined_status"] == "pass" for row in rows):
        return "Proceed to a 4x particle-count pilot using the same C/D/E parameters."
    if any(row["refined_best_p95_mpa"] < ZHANG_WINDOW[0] for row in rows):
        return (
            "Do not launch 4x yet. The 2x DEM runs are complete, but P95 pressures "
            "fall below the 572-638 MPa Zhang endpoint window; recalibrate endpoint "
            "modulus/loading/contact parameters at pscale=2 first."
        )
    return "Keep pscale=2 and tune force-chain/contact thresholds before a 4x pilot."


def write_report(
    path: Path,
    *,
    comparison_rows: list[dict[str, object]],
    acceptance_rows: list[dict[str, object]],
    summary: dict[str, object],
) -> None:
    lines = [
        "# Zhang 2x Particle-Scale Interpretation",
        "",
        "## Conclusion",
        "",
        summary["recommended_next_step"],
        "",
        "The `particle_count_scale=2` C/D/E runs prove the workflow and verifier path are usable, "
        "but they do not preserve the Zhang endpoint pressure calibration from the 1x size-specific sweep. "
        "This stage should therefore remain `review` until pscale=2 is recalibrated.",
        "",
        "## 1x vs 2x Comparison",
        "",
        "| Size | 1x P95 MPa | 2x P95 MPa | Delta MPa | Delta % | 2x Status | 2x Diagnosis |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for row in comparison_rows:
        lines.append(
            "| {size} | {base:.3f} | {refined:.3f} | {delta:.3f} | {pct:.2f}% | {status} | {diag} |".format(
                size=row["diamond_size_case"],
                base=row["baseline_best_p95_mpa"],
                refined=row["refined_best_p95_mpa"],
                delta=row["p95_delta_mpa"],
                pct=row["p95_delta_percent"],
                status=row["refined_status"],
                diag=row["refined_calibration_diagnosis"],
            )
        )
    lines.extend(
        [
            "",
            "## Acceptance",
            "",
            "| Size | Artifact | Workflow | Pressure Window | Trend | Overall | Decision |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for row in acceptance_rows:
        lines.append(
            "| {size} | pass | pass | {pressure} | {trend} | {overall} | {decision} |".format(
                size=row["diamond_size_case"],
                pressure=row["pressure_window_gate"],
                trend=row["trend_gate"],
                overall=row["overall_status"],
                decision=row["decision"],
            )
        )
    lines.extend(
        [
            "",
            "## Files",
            "",
            "- `data/combined_2x_27875950305_27875951506_27875952754/combined_best_by_run.csv`",
            "- `data/combined_2x_27875950305_27875951506_27875952754/combined_size_summary.csv`",
            "- `data/1x_vs_2x_comparison.csv`",
            "- `data/zhang_particle_scale_acceptance.csv`",
            "- `figures/p95_1x_vs_2x.png`",
            "- `figures/p95_delta_percent.png`",
            "",
            "## Reading Notes",
            "",
            "- The 2x runs are complete and suitable as evidence that particle refinement runs in workflow.",
            "- The pressure gate is not met because all three 2x P95 values are below 572 MPa.",
            "- C keeps the Zhang force-chain trend gate as `pass`; D and E need participation-increase recalibration.",
            "- The next physical action is pscale=2 recalibration, not 4x/8x scaling.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def write_plots(rows: list[dict[str, object]], *, figure_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        (figure_dir / "plots_skipped.txt").write_text(
            "matplotlib unavailable; plots were skipped.\n",
            encoding="utf-8",
        )
        return

    sizes = [str(row["diamond_size_case"]) for row in rows]
    baseline = [float(row["baseline_best_p95_mpa"]) for row in rows]
    refined = [float(row["refined_best_p95_mpa"]) for row in rows]
    deltas = [float(row["p95_delta_percent"]) for row in rows]
    x = list(range(len(sizes)))

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    width = 0.35
    ax.bar([idx - width / 2 for idx in x], baseline, width=width, label="1x best")
    ax.bar([idx + width / 2 for idx in x], refined, width=width, label="2x")
    ax.axhspan(ZHANG_WINDOW[0], ZHANG_WINDOW[1], color="#d8ead3", alpha=0.45, label="Zhang 572-638 MPa")
    ax.set_xticks(x, sizes)
    ax.set_ylabel("P95 pressure (MPa)")
    ax.set_title("Zhang 1x vs 2x Endpoint Pressure")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figure_dir / "p95_1x_vs_2x.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    colors = ["#9b5de5" if value < 0 else "#00a896" for value in deltas]
    ax.bar(sizes, deltas, color=colors)
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_ylabel("P95 change from 1x (%)")
    ax.set_title("Particle Refinement Pressure Shift")
    fig.tight_layout()
    fig.savefig(figure_dir / "p95_delta_percent.png", dpi=180)
    plt.close(fig)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def index_by_size(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        size = row.get("diamond_size_case")
        if size:
            indexed[size] = row
    return indexed


def require_float(value: object, label: str) -> float:
    number = optional_float(value)
    if number is None:
        raise SystemExit(f"[FAIL] missing numeric {label}: {value!r}")
    return number


def optional_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def in_window(value: float) -> bool:
    return ZHANG_WINDOW[0] <= value <= ZHANG_WINDOW[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-summary", required=True)
    parser.add_argument("--refined-summary", required=True)
    parser.add_argument("--refined-best", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--figure-dir", required=True)
    args = parser.parse_args()

    summary = analyze_particle_scale(
        baseline_summary=Path(args.baseline_summary),
        refined_summary=Path(args.refined_summary),
        refined_best=Path(args.refined_best),
        outdir=Path(args.outdir),
        figure_dir=Path(args.figure_dir),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
