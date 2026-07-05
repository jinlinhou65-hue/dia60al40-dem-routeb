"""Compare Zhang size-C 50 and 25 cm/s loading rates on paired DEM seeds."""

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


BASELINE_VELOCITY_CM_S = 50.0
TEST_VELOCITY_CM_S = 25.0
SETTLE_STEPS = {"initial": 20_000, "stage": 20_000, "final": 50_000}


def analyze_loading_rate(
    *,
    evidence_root: Path,
    run_id: str,
    baseline_path: Path,
    outdir: Path,
    figure_dir: Path,
    report: Path,
) -> dict[str, object]:
    run_dir = evidence_root / f"pscale2_c_loading_rate_recheck_run_{run_id}"
    raw_new = read_csv(run_dir / "zhang_calibration_best_by_run.csv")
    raw_baseline = read_csv(baseline_path)
    if not raw_new:
        raise SystemExit(f"[FAIL] missing loading-rate rows: {run_dir}")
    if not raw_baseline:
        raise SystemExit(f"[FAIL] missing 50 cm/s baseline rows: {baseline_path}")

    new_rows = [
        normalize_settle_row(row, run_id=run_id, run_dir=run_dir)
        for row in raw_new
    ]
    baseline_rows = [normalize_baseline_row(row) for row in raw_baseline]
    validate_runtime(new_rows)
    paired = pair_rows(baseline_rows, new_rows)
    baseline_metrics = group_metrics(baseline_rows)
    test_metrics = group_metrics(new_rows)
    decision = loading_rate_decision(baseline_metrics, test_metrics)
    summary = {
        "run_id": run_id,
        "baseline_run_id": str(paired[0]["baseline_run_id"]),
        "diamond_size_case": "C",
        "particle_count_scale": 2,
        "seed_count": len(paired),
        "e_al_emax_gpa": 72.581,
        "mu_scale": 0.654,
        "baseline_velocity_cm_s": BASELINE_VELOCITY_CM_S,
        "test_velocity_cm_s": TEST_VELOCITY_CM_S,
        "velocity_ratio": TEST_VELOCITY_CM_S / BASELINE_VELOCITY_CM_S,
        "time_step_seconds": 2.0e-10,
        "settle_scale": 1,
        "settle_steps": SETTLE_STEPS,
        "pressure_window_mpa": list(ZHANG_WINDOW),
        "baseline": baseline_metrics,
        "test": test_metrics,
        "p95_mean_delta_mpa": (
            float(test_metrics["p95_mean_mpa"])
            - float(baseline_metrics["p95_mean_mpa"])
        ),
        "p95_cv_change_percent": 100.0
        * (
            float(test_metrics["p95_cv"])
            - float(baseline_metrics["p95_cv"])
        )
        / float(baseline_metrics["p95_cv"]),
        "decision": decision,
        "recommended_next_step": recommendation(decision),
    }
    acceptance = [acceptance_row(summary)]

    outdir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    write_csv(outdir / "pscale2_c_loading_rate_candidates.csv", new_rows)
    write_csv(outdir / "pscale2_c_loading_rate_paired.csv", paired)
    write_csv(outdir / "pscale2_c_loading_rate_acceptance.csv", acceptance)
    (outdir / "pscale2_c_loading_rate_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_plot(paired, figure_dir=figure_dir)
    write_report(report, summary=summary, paired=paired, acceptance=acceptance[0])
    return summary


def validate_runtime(rows: list[dict[str, object]]) -> None:
    by_seed = unique_by_seed(rows, "25 cm/s loading-rate")
    if set(by_seed) != set(range(5)):
        raise SystemExit("[FAIL] loading-rate recheck must contain seeds 0..4")
    expected = {
        "top_velocity_cm_s": TEST_VELOCITY_CM_S,
        "time_step_seconds": 2.0e-10,
        "initial_settle_steps": float(SETTLE_STEPS["initial"]),
        "stage_settle_steps": float(SETTLE_STEPS["stage"]),
        "final_settle_steps": float(SETTLE_STEPS["final"]),
    }
    for seed, row in by_seed.items():
        if str(row["diamond_size_case"]) != "C":
            raise SystemExit(f"[FAIL] seed {seed} is not size C")
        if int(float(row["particle_count_scale"])) != 2:
            raise SystemExit(f"[FAIL] seed {seed} changed particle scale")
        if float(row["e_al_emax_gpa"]) != 72.581 or float(row["mu_scale"]) != 0.654:
            raise SystemExit(f"[FAIL] seed {seed} changed Emax or mu")
        for field, value in expected.items():
            if float(row[field]) != value:
                raise SystemExit(f"[FAIL] seed {seed} has unexpected {field}={row[field]}")


def pair_rows(
    baseline_rows: list[dict[str, object]],
    new_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    baseline = unique_by_seed(baseline_rows, "50 cm/s baseline")
    test = unique_by_seed(new_rows, "25 cm/s test")
    if set(baseline) != set(test) or set(test) != set(range(5)):
        raise SystemExit("[FAIL] 50 and 25 cm/s seed sets must both be 0..4")
    paired: list[dict[str, object]] = []
    for seed in range(5):
        old = baseline[seed]
        new = test[seed]
        if float(old["e_al_emax_gpa"]) != float(new["e_al_emax_gpa"]):
            raise SystemExit(f"[FAIL] Emax changed for seed {seed}")
        if float(old["mu_scale"]) != float(new["mu_scale"]):
            raise SystemExit(f"[FAIL] mu changed for seed {seed}")
        old_p95 = float(old["p95_mpa"])
        new_p95 = float(new["p95_mpa"])
        paired.append({
            "seed_index": seed,
            "baseline_run_id": old["source_run_id"],
            "test_run_id": new["source_run_id"],
            "baseline_velocity_cm_s": BASELINE_VELOCITY_CM_S,
            "test_velocity_cm_s": TEST_VELOCITY_CM_S,
            "baseline_p95_mpa": old_p95,
            "test_p95_mpa": new_p95,
            "p95_delta_mpa": new_p95 - old_p95,
            "p95_delta_percent": 100.0 * (new_p95 - old_p95) / old_p95,
            "baseline_status": old["status"],
            "test_status": new["status"],
            "baseline_pressure_in_window": old["pressure_in_window"],
            "test_pressure_in_window": new["pressure_in_window"],
            "baseline_pass_and_window": both_pass(old),
            "test_pass_and_window": both_pass(new),
            "test_participation_delta": new["participation_delta"],
            "test_d1_delta": new["d1_delta"],
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


def loading_rate_decision(
    baseline: dict[str, object],
    test: dict[str, object],
) -> str:
    if int(test["pass_and_window_count"]) == 5:
        return "c_loading_rate_seed_robust"
    improves = (
        ZHANG_WINDOW[0] <= float(test["p95_mean_mpa"]) <= ZHANG_WINDOW[1]
        and float(test["p95_cv"]) < float(baseline["p95_cv"])
        and int(test["trend_pass_count"]) >= int(baseline["trend_pass_count"])
        and int(test["pass_and_window_count"])
        > int(baseline["pass_and_window_count"])
    )
    if improves:
        return "c_loading_rate_improves_tradeoff"
    return "c_loading_rate_not_better"


def recommendation(decision: str) -> str:
    if decision == "c_loading_rate_seed_robust":
        return "Freeze C at 25 cm/s and continue D/E calibration before 4x particles."
    if decision == "c_loading_rate_improves_tradeoff":
        return (
            "Retain 25 cm/s as the current C loading-path candidate, but do not call it "
            "seed robust; continue D/E and preserve this five-seed evidence."
        )
    return (
        "Restore the 50 cm/s baseline and stop using loading rate as the next C variable; "
        "test one contact-law or damping control while keeping settle scale 1."
    )


def acceptance_row(summary: dict[str, object]) -> dict[str, object]:
    baseline = summary["baseline"]
    test = summary["test"]
    return {
        "diamond_size_case": "C",
        "artifact_imported": True,
        "workflow_completed": True,
        "runtime_provenance_gate": "pass",
        "mean_pressure_gate": (
            "pass"
            if ZHANG_WINDOW[0] <= float(test["p95_mean_mpa"]) <= ZHANG_WINDOW[1]
            else "review"
        ),
        "cv_improvement_gate": (
            "pass" if float(test["p95_cv"]) < float(baseline["p95_cv"]) else "review"
        ),
        "trend_preservation_gate": (
            "pass"
            if int(test["trend_pass_count"]) >= int(baseline["trend_pass_count"])
            else "review"
        ),
        "combined_coverage_improvement_gate": (
            "pass"
            if int(test["pass_and_window_count"])
            > int(baseline["pass_and_window_count"])
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
    baseline = summary["baseline"]
    test = summary["test"]
    lines = [
        "# Zhang pscale=2 C Loading-Rate Recheck Results",
        "",
        "## Conclusion",
        "",
        str(summary["recommended_next_step"]),
        "",
        "## Loading-Rate Comparison",
        "",
        "| Metric | 50 cm/s baseline | 25 cm/s test | Change |",
        "|---|---:|---:|---:|",
        "| Mean P95 MPa | {old:.3f} | {new:.3f} | {delta:+.3f} |".format(
            old=float(baseline["p95_mean_mpa"]),
            new=float(test["p95_mean_mpa"]),
            delta=float(summary["p95_mean_delta_mpa"]),
        ),
        "| P95 CV | {old:.4f} | {new:.4f} | {delta:+.2f}% |".format(
            old=float(baseline["p95_cv"]),
            new=float(test["p95_cv"]),
            delta=float(summary["p95_cv_change_percent"]),
        ),
        "| Trend pass | {old}/5 | {new}/5 | {delta:+d} |".format(
            old=int(baseline["trend_pass_count"]),
            new=int(test["trend_pass_count"]),
            delta=int(test["trend_pass_count"]) - int(baseline["trend_pass_count"]),
        ),
        "| Pressure window | {old}/5 | {new}/5 | {delta:+d} |".format(
            old=int(baseline["pressure_window_count"]),
            new=int(test["pressure_window_count"]),
            delta=int(test["pressure_window_count"])
            - int(baseline["pressure_window_count"]),
        ),
        "| Pass + window | {old}/5 | {new}/5 | {delta:+d} |".format(
            old=int(baseline["pass_and_window_count"]),
            new=int(test["pass_and_window_count"]),
            delta=int(test["pass_and_window_count"])
            - int(baseline["pass_and_window_count"]),
        ),
        "",
        "## Paired Seeds",
        "",
        "| Seed | 50 cm/s P95 | 25 cm/s P95 | Delta MPa | Delta % | Pressure | Trend | Both |",
        "|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for row in paired:
        lines.append(
            "| {seed} | {old:.3f} | {new:.3f} | {delta:+.3f} | {pct:+.2f}% | {pressure} | {trend} | {both} |".format(
                seed=row["seed_index"],
                old=float(row["baseline_p95_mpa"]),
                new=float(row["test_p95_mpa"]),
                delta=float(row["p95_delta_mpa"]),
                pct=float(row["p95_delta_percent"]),
                pressure="pass" if row["test_pressure_in_window"] else "review",
                trend=row["test_status"],
                both="pass" if row["test_pass_and_window"] else "review",
            )
        )
    lines.extend([
        "",
        "## Acceptance",
        "",
        "| Artifact | Workflow | Runtime | Mean pressure | CV | Trend | Combined coverage | Decision |",
        "|---|---|---|---|---|---|---|---|",
        "| pass | pass | {runtime} | {mean} | {cv} | {trend} | {combined} | {decision} |".format(
            runtime=acceptance["runtime_provenance_gate"],
            mean=acceptance["mean_pressure_gate"],
            cv=acceptance["cv_improvement_gate"],
            trend=acceptance["trend_preservation_gate"],
            combined=acceptance["combined_coverage_improvement_gate"],
            decision=acceptance["decision"],
        ),
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def write_plot(paired: list[dict[str, object]], *, figure_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        (figure_dir / "pscale2_c_loading_rate_plots_skipped.txt").write_text(
            "matplotlib unavailable; plots were skipped.\n",
            encoding="utf-8",
        )
        return
    seeds = [int(row["seed_index"]) for row in paired]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.axhspan(ZHANG_WINDOW[0], ZHANG_WINDOW[1], color="#2f7d32", alpha=0.12)
    ax.plot(
        seeds,
        [float(row["baseline_p95_mpa"]) for row in paired],
        marker="o",
        color="#4c78a8",
        label="50 cm/s",
    )
    ax.plot(
        seeds,
        [float(row["test_p95_mpa"]) for row in paired],
        marker="s",
        color="#e09f3e",
        label="25 cm/s",
    )
    ax.set_xticks(seeds)
    ax.set_xlabel("DEM seed")
    ax.set_ylabel("P95 pressure (MPa)")
    ax.set_title("Zhang pscale=2 C paired loading-rate response")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(figure_dir / "pscale2_c_loading_rate_paired.png", dpi=160)
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
    parser.add_argument("--outdir", default=str(stage / "data"))
    parser.add_argument("--figure-dir", default=str(stage / "figures"))
    parser.add_argument(
        "--report",
        default=str(stage / "pscale2_c_loading_rate_report.md"),
    )
    args = parser.parse_args()
    summary = analyze_loading_rate(
        evidence_root=Path(args.evidence_root),
        run_id=args.run_id,
        baseline_path=Path(args.baseline),
        outdir=Path(args.outdir),
        figure_dir=Path(args.figure_dir),
        report=Path(args.report),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
