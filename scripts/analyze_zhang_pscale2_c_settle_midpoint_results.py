"""Compare Zhang size-C settle scales 1, 2, and 4 on paired DEM seeds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from analyze_zhang_pscale2_c_pressure_lift_results import (
    normalize_baseline_row,
    unique_by_seed,
)
from analyze_zhang_pscale2_c_seed_recheck_results import (
    ZHANG_WINDOW,
    read_csv,
    sample_stdev,
    write_csv,
)
from analyze_zhang_pscale2_c_settle_results import normalize_settle_row


STEPS = {
    1: {"initial": 20000, "stage": 20000, "final": 50000},
    2: {"initial": 40000, "stage": 40000, "final": 100000},
    4: {"initial": 80000, "stage": 80000, "final": 200000},
}


def analyze_midpoint(
    *,
    evidence_root: Path,
    run_id: str,
    baseline_path: Path,
    settle4_path: Path,
    outdir: Path,
    figure_dir: Path,
    report: Path,
) -> dict[str, object]:
    run_dir = evidence_root / f"pscale2_c_settle_midpoint_run_{run_id}"
    raw_midpoint = read_csv(run_dir / "zhang_calibration_best_by_run.csv")
    raw_baseline = read_csv(baseline_path)
    raw_settle4 = read_csv(settle4_path)
    if not raw_midpoint:
        raise SystemExit(f"[FAIL] missing settle=2 rows: {run_dir}")
    if not raw_baseline or not raw_settle4:
        raise SystemExit("[FAIL] settle=1 or settle=4 comparison rows are missing")

    midpoint = [
        normalize_settle_row(row, run_id=run_id, run_dir=run_dir)
        for row in raw_midpoint
    ]
    baseline = [normalize_baseline_row(row) for row in raw_baseline]
    settle4 = [
        normalize_settle_row(
            row,
            run_id=str(row.get("source_run_id", "")),
            run_dir=Path(str(row.get("source_run_dir", ""))),
        )
        for row in raw_settle4
    ]
    validate_runtime(midpoint, scale=2)
    validate_runtime(settle4, scale=4)
    paired = pair_groups(baseline, midpoint, settle4)

    metrics = {
        "settle1": group_metrics(baseline),
        "settle2": group_metrics(midpoint),
        "settle4": group_metrics(settle4),
    }
    decision = midpoint_decision(metrics)
    summary = {
        "run_id": run_id,
        "baseline_run_id": str(paired[0]["settle1_run_id"]),
        "settle4_run_id": str(paired[0]["settle4_run_id"]),
        "diamond_size_case": "C",
        "particle_count_scale": 2,
        "seed_count": len(paired),
        "e_al_emax_gpa": 72.581,
        "mu_scale": 0.654,
        "top_velocity_cm_s": 50.0,
        "time_step_seconds": 2.0e-10,
        "pressure_window_mpa": list(ZHANG_WINDOW),
        "settle_steps": {str(scale): values for scale, values in STEPS.items()},
        "groups": metrics,
        "decision": decision,
        "recommended_next_step": recommendation(decision),
    }
    acceptance = [acceptance_row(summary)]

    outdir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    write_csv(outdir / "pscale2_c_settle_midpoint_candidates.csv", midpoint)
    write_csv(outdir / "pscale2_c_settle_midpoint_paired.csv", paired)
    write_csv(outdir / "pscale2_c_settle_midpoint_acceptance.csv", acceptance)
    (outdir / "pscale2_c_settle_midpoint_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_plot(paired, figure_dir=figure_dir)
    write_report(report, summary=summary, paired=paired, acceptance=acceptance[0])
    return summary


def validate_runtime(rows: list[dict[str, object]], *, scale: int) -> None:
    expected = {
        "top_velocity_cm_s": 50.0,
        "time_step_seconds": 2.0e-10,
        "initial_settle_steps": float(STEPS[scale]["initial"]),
        "stage_settle_steps": float(STEPS[scale]["stage"]),
        "final_settle_steps": float(STEPS[scale]["final"]),
    }
    by_seed = unique_by_seed(rows, f"settle={scale}")
    if set(by_seed) != set(range(5)):
        raise SystemExit(f"[FAIL] settle={scale} must contain seeds 0..4")
    for seed, row in by_seed.items():
        if str(row["diamond_size_case"]) != "C":
            raise SystemExit(f"[FAIL] settle={scale} seed {seed} is not size C")
        if int(float(row["particle_count_scale"])) != 2:
            raise SystemExit(f"[FAIL] settle={scale} seed {seed} changed particle scale")
        if float(row["e_al_emax_gpa"]) != 72.581 or float(row["mu_scale"]) != 0.654:
            raise SystemExit(f"[FAIL] settle={scale} seed {seed} changed contact controls")
        for field, value in expected.items():
            if float(row[field]) != value:
                raise SystemExit(
                    f"[FAIL] settle={scale} seed {seed} has {field}={row[field]}"
                )


def pair_groups(
    baseline: list[dict[str, object]],
    midpoint: list[dict[str, object]],
    settle4: list[dict[str, object]],
) -> list[dict[str, object]]:
    groups = {
        1: unique_by_seed(baseline, "settle=1"),
        2: unique_by_seed(midpoint, "settle=2"),
        4: unique_by_seed(settle4, "settle=4"),
    }
    seed_sets = {tuple(sorted(rows)) for rows in groups.values()}
    if seed_sets != {tuple(range(5))}:
        raise SystemExit(f"[FAIL] settle seed sets differ: {seed_sets}")

    paired: list[dict[str, object]] = []
    for seed in range(5):
        rows = {scale: groups[scale][seed] for scale in groups}
        for scale, row in rows.items():
            if float(row["e_al_emax_gpa"]) != 72.581 or float(row["mu_scale"]) != 0.654:
                raise SystemExit(f"[FAIL] settle={scale} seed {seed} changed Emax or mu")
        p1, p2, p4 = (float(rows[scale]["p95_mpa"]) for scale in (1, 2, 4))
        paired.append({
            "seed_index": seed,
            "settle1_run_id": rows[1]["source_run_id"],
            "settle2_run_id": rows[2]["source_run_id"],
            "settle4_run_id": rows[4]["source_run_id"],
            "settle1_p95_mpa": p1,
            "settle2_p95_mpa": p2,
            "settle4_p95_mpa": p4,
            "settle2_minus_1_mpa": p2 - p1,
            "settle4_minus_1_mpa": p4 - p1,
            "settle1_status": rows[1]["status"],
            "settle2_status": rows[2]["status"],
            "settle4_status": rows[4]["status"],
            "settle1_pressure_in_window": rows[1]["pressure_in_window"],
            "settle2_pressure_in_window": rows[2]["pressure_in_window"],
            "settle4_pressure_in_window": rows[4]["pressure_in_window"],
            "settle1_pass_and_window": both_pass(rows[1]),
            "settle2_pass_and_window": both_pass(rows[2]),
            "settle4_pass_and_window": both_pass(rows[4]),
        })
    return paired


def both_pass(row: dict[str, object]) -> bool:
    return row["status"] == "pass" and bool(row["pressure_in_window"])


def group_metrics(rows: list[dict[str, object]]) -> dict[str, object]:
    pressures = [float(row["p95_mpa"]) for row in rows]
    mean = sum(pressures) / len(pressures)
    stdev = sample_stdev(pressures)
    return {
        "p95_mean_mpa": mean,
        "p95_stdev_mpa": stdev,
        "p95_cv": stdev / mean,
        "p95_min_mpa": min(pressures),
        "p95_max_mpa": max(pressures),
        "trend_pass_count": sum(row["status"] == "pass" for row in rows),
        "pressure_window_count": sum(bool(row["pressure_in_window"]) for row in rows),
        "pass_and_window_count": sum(both_pass(row) for row in rows),
    }


def midpoint_decision(metrics: dict[str, dict[str, object]]) -> str:
    baseline = metrics["settle1"]
    midpoint = metrics["settle2"]
    if int(midpoint["pass_and_window_count"]) == 5:
        return "c_settle_midpoint_seed_robust"
    controlled_cv = float(midpoint["p95_cv"]) <= 1.25 * float(baseline["p95_cv"])
    mean_in_window = ZHANG_WINDOW[0] <= float(midpoint["p95_mean_mpa"]) <= ZHANG_WINDOW[1]
    improves_gates = (
        int(midpoint["trend_pass_count"]) > int(baseline["trend_pass_count"])
        and int(midpoint["pass_and_window_count"])
        >= int(baseline["pass_and_window_count"])
    )
    if controlled_cv and mean_in_window and improves_gates:
        return "c_settle_midpoint_improves_tradeoff"
    return "c_settle_midpoint_not_better"


def recommendation(decision: str) -> str:
    if decision == "c_settle_midpoint_seed_robust":
        return "Freeze C at settle scale 2 and continue D/E calibration before 4x particles."
    if decision == "c_settle_midpoint_improves_tradeoff":
        return (
            "Retain settle scale 2 as the current C loading-path candidate, but do not call "
            "it seed robust; continue D/E before any particle-count increase."
        )
    return (
        "Reject settle scale 2 as well as scale 4. Restore settle scale 1 and stop using dwell "
        "duration as the next C calibration variable; test one different loading/contact control."
    )


def acceptance_row(summary: dict[str, object]) -> dict[str, object]:
    metrics = summary["groups"]
    midpoint = metrics["settle2"]
    return {
        "diamond_size_case": "C",
        "artifact_imported": True,
        "workflow_completed": True,
        "paired_seed_gate": "pass" if int(summary["seed_count"]) == 5 else "review",
        "runtime_provenance_gate": "pass",
        "midpoint_mean_pressure_gate": (
            "pass"
            if ZHANG_WINDOW[0] <= float(midpoint["p95_mean_mpa"]) <= ZHANG_WINDOW[1]
            else "review"
        ),
        "midpoint_cv_gate": (
            "pass"
            if float(midpoint["p95_cv"]) <= 1.25 * float(metrics["settle1"]["p95_cv"])
            else "review"
        ),
        "midpoint_tradeoff_gate": (
            "pass"
            if summary["decision"] in {
                "c_settle_midpoint_seed_robust",
                "c_settle_midpoint_improves_tradeoff",
            }
            else "review"
        ),
        "decision": summary["decision"],
    }


def write_report(
    path: Path,
    *,
    summary: dict[str, object],
    paired: list[dict[str, object]],
    acceptance: dict[str, object],
) -> None:
    metrics = summary["groups"]
    lines = [
        "# Zhang pscale=2 C Settle Midpoint Results",
        "",
        "## Conclusion",
        "",
        str(summary["recommended_next_step"]),
        "",
        "## Three-Way Comparison",
        "",
        "| Settle scale | Mean P95 MPa | P95 CV | Trend pass | Pressure window | Pass + window |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for scale in (1, 2, 4):
        row = metrics[f"settle{scale}"]
        lines.append(
            "| {scale} | {mean:.3f} | {cv:.4f} | {trend}/5 | {window}/5 | {both}/5 |".format(
                scale=scale,
                mean=float(row["p95_mean_mpa"]),
                cv=float(row["p95_cv"]),
                trend=int(row["trend_pass_count"]),
                window=int(row["pressure_window_count"]),
                both=int(row["pass_and_window_count"]),
            )
        )
    lines.extend([
        "",
        "## Paired Seeds",
        "",
        "| Seed | Settle 1 P95 | Settle 2 P95 | Settle 4 P95 | 2-1 MPa | S2 trend | S2 pressure | S2 both |",
        "|---:|---:|---:|---:|---:|---|---|---|",
    ])
    for row in paired:
        lines.append(
            "| {seed} | {p1:.3f} | {p2:.3f} | {p4:.3f} | {delta:+.3f} | {trend} | {pressure} | {both} |".format(
                seed=row["seed_index"],
                p1=float(row["settle1_p95_mpa"]),
                p2=float(row["settle2_p95_mpa"]),
                p4=float(row["settle4_p95_mpa"]),
                delta=float(row["settle2_minus_1_mpa"]),
                trend=row["settle2_status"],
                pressure="pass" if row["settle2_pressure_in_window"] else "review",
                both="pass" if row["settle2_pass_and_window"] else "review",
            )
        )
    lines.extend([
        "",
        "## Acceptance",
        "",
        "| Artifact | Workflow | Paired seeds | Runtime | Mean pressure | CV | Tradeoff | Decision |",
        "|---|---|---|---|---|---|---|---|",
        "| pass | pass | {paired} | {runtime} | {mean} | {cv} | {tradeoff} | {decision} |".format(
            paired=acceptance["paired_seed_gate"],
            runtime=acceptance["runtime_provenance_gate"],
            mean=acceptance["midpoint_mean_pressure_gate"],
            cv=acceptance["midpoint_cv_gate"],
            tradeoff=acceptance["midpoint_tradeoff_gate"],
            decision=acceptance["decision"],
        ),
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def write_plot(paired: list[dict[str, object]], *, figure_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        (figure_dir / "pscale2_c_settle_midpoint_plots_skipped.txt").write_text(
            "matplotlib unavailable; plots were skipped.\n",
            encoding="utf-8",
        )
        return
    seeds = [int(row["seed_index"]) for row in paired]
    fig, ax = plt.subplots(figsize=(7.4, 4.3))
    ax.axhspan(ZHANG_WINDOW[0], ZHANG_WINDOW[1], color="#2f7d32", alpha=0.12)
    styles = {1: ("o", "#4c78a8"), 2: ("s", "#e09f3e"), 4: ("^", "#d1495b")}
    for scale in (1, 2, 4):
        marker, color = styles[scale]
        ax.plot(
            seeds,
            [float(row[f"settle{scale}_p95_mpa"]) for row in paired],
            marker=marker,
            color=color,
            label=f"settle scale {scale}",
        )
    ax.set_xticks(seeds)
    ax.set_xlabel("DEM seed")
    ax.set_ylabel("P95 pressure (MPa)")
    ax.set_title("Zhang pscale=2 C settle-duration midpoint test")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(figure_dir / "pscale2_c_settle_midpoint_paired.png", dpi=160)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    stage = Path("docs/reproduction_goal/03_zhang_particle_scale")
    parser.add_argument("--evidence-root", default=str(stage / "evidence"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--baseline",
        default=str(stage / "data" / "pscale2_c_pressure_lift_candidates.csv"),
    )
    parser.add_argument(
        "--settle4",
        default=str(stage / "data" / "pscale2_c_settle_candidates.csv"),
    )
    parser.add_argument("--outdir", default=str(stage / "data"))
    parser.add_argument("--figure-dir", default=str(stage / "figures"))
    parser.add_argument("--report", default=str(stage / "pscale2_c_settle_midpoint_report.md"))
    args = parser.parse_args()
    summary = analyze_midpoint(
        evidence_root=Path(args.evidence_root),
        run_id=args.run_id,
        baseline_path=Path(args.baseline),
        settle4_path=Path(args.settle4),
        outdir=Path(args.outdir),
        figure_dir=Path(args.figure_dir),
        report=Path(args.report),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
