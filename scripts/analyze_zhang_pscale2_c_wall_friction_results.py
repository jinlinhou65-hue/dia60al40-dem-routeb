"""Compare paired Zhang size-C baseline and low-sidewall-friction DEM runs."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from analyze_zhang_pscale2_c_seed_recheck_results import (
    ZHANG_WINDOW,
    optional_float,
    read_csv,
    required_float,
    sample_stdev,
    write_csv,
)


BASELINE_WALL_SCALE = 1.0
TEST_WALL_SCALE = 0.019113
BASELINE_EFFECTIVE_WALL_MU = 0.05232
TEST_EFFECTIVE_WALL_MU = 0.000999992
HISTORICAL_BASELINE_CV = 0.03957423315
PINNED_LIGGGHTS_COMMIT = "3d5c00f20519e6bb6eb6756f51f1ad36564e649d"
EXPECTED_SEEDS = set(range(5))


def analyze_wall_friction(
    *,
    evidence_root: Path,
    run_id: str,
    outdir: Path,
    figure_dir: Path,
    report: Path,
) -> dict[str, object]:
    run_dir = evidence_root / f"pscale2_c_wall_friction_recheck_run_{run_id}"
    raw_rows = read_csv(run_dir / "zhang_calibration_best_by_run.csv")
    if not raw_rows:
        raise SystemExit(f"[FAIL] missing wall-friction rows: {run_dir}")
    rows = [normalize_row(row, run_id=run_id, run_dir=run_dir) for row in raw_rows]
    baseline_rows = select_scale(rows, BASELINE_WALL_SCALE, "baseline")
    test_rows = select_scale(rows, TEST_WALL_SCALE, "low-wall-friction")
    validate_groups(baseline_rows, test_rows)
    paired = pair_rows(baseline_rows, test_rows)
    baseline = group_metrics(baseline_rows)
    test = group_metrics(test_rows)
    decision = decide(baseline, test)
    summary = {
        "run_id": run_id,
        "diamond_size_case": "C",
        "particle_count_scale": 2,
        "seed_count_per_group": 5,
        "e_al_emax_gpa": 72.581,
        "mu_scale": 0.654,
        "baseline_mu_wall_scale": BASELINE_WALL_SCALE,
        "test_mu_wall_scale": TEST_WALL_SCALE,
        "baseline_effective_mu_wall": BASELINE_EFFECTIVE_WALL_MU,
        "test_effective_mu_wall": TEST_EFFECTIVE_WALL_MU,
        "liggghts_commit": PINNED_LIGGGHTS_COMMIT,
        "pressure_window_mpa": list(ZHANG_WINDOW),
        "historical_baseline_cv": HISTORICAL_BASELINE_CV,
        "baseline": baseline,
        "test": test,
        "p95_mean_delta_mpa": float(test["p95_mean_mpa"]) - float(baseline["p95_mean_mpa"]),
        "p95_cv_change_percent": percent_change(
            float(baseline["p95_cv"]), float(test["p95_cv"])
        ),
        "decision": decision,
        "recommended_next_step": recommendation(decision),
    }
    acceptance = acceptance_row(summary)

    outdir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    write_csv(outdir / "pscale2_c_wall_friction_candidates.csv", rows)
    write_csv(outdir / "pscale2_c_wall_friction_paired.csv", paired)
    write_csv(outdir / "pscale2_c_wall_friction_acceptance.csv", [acceptance])
    (outdir / "pscale2_c_wall_friction_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_plot(paired, figure_dir)
    write_report(report, summary, paired, acceptance)
    return summary


def normalize_row(
    row: dict[str, str], *, run_id: str, run_dir: Path
) -> dict[str, object]:
    p95 = required_float(row, "p95_mpa")
    seed = int(required_float(row, "seed_index"))
    return {
        "source_run_id": run_id,
        "source_run_dir": run_dir.as_posix(),
        "artifact": row.get("artifact", ""),
        "diamond_size_case": row.get("diamond_size_case", ""),
        "particle_count_scale": int(required_float(row, "particle_count_scale")),
        "seed_index": seed,
        "e_al_emax_gpa": required_float(row, "e_al_emax_gpa"),
        "mu_scale": required_float(row, "mu_scale"),
        "mu_wall_scale": required_float(row, "mu_wall_scale"),
        "mu_al_wall": required_float(row, "mu_al_wall"),
        "mu_diamond_wall": required_float(row, "mu_diamond_wall"),
        "mu_al_tool": required_float(row, "mu_al_tool"),
        "mu_diamond_tool": required_float(row, "mu_diamond_tool"),
        "liggghts_commit": row.get("liggghts_commit", ""),
        "top_velocity_cm_s": required_float(row, "top_velocity_cm_s"),
        "time_step_seconds": required_float(row, "time_step_seconds"),
        "initial_settle_steps": int(required_float(row, "initial_settle_steps")),
        "stage_settle_steps": int(required_float(row, "stage_settle_steps")),
        "final_settle_steps": int(required_float(row, "final_settle_steps")),
        "p95_mpa": p95,
        "pressure_in_window": ZHANG_WINDOW[0] <= p95 <= ZHANG_WINDOW[1],
        "status": row.get("status", ""),
        "participation_delta": optional_float(row.get("participation_delta")),
        "d1_delta": optional_float(row.get("d1_delta")),
    }


def select_scale(
    rows: list[dict[str, object]], target: float, label: str
) -> list[dict[str, object]]:
    selected = [
        row
        for row in rows
        if math.isclose(float(row["mu_wall_scale"]), target, rel_tol=0.0, abs_tol=5.0e-7)
    ]
    by_seed = {int(row["seed_index"]): row for row in selected}
    if len(selected) != len(by_seed) or set(by_seed) != EXPECTED_SEEDS:
        raise SystemExit(f"[FAIL] {label} must contain one row for each seed 0..4")
    return [by_seed[seed] for seed in sorted(by_seed)]


def validate_groups(
    baseline: list[dict[str, object]], test: list[dict[str, object]]
) -> None:
    for group, wall_mu in (
        (baseline, BASELINE_EFFECTIVE_WALL_MU),
        (test, TEST_EFFECTIVE_WALL_MU),
    ):
        for row in group:
            seed = int(row["seed_index"])
            if row["diamond_size_case"] != "C" or int(row["particle_count_scale"]) != 2:
                raise SystemExit(f"[FAIL] seed {seed} changed size or particle scale")
            if float(row["e_al_emax_gpa"]) != 72.581 or float(row["mu_scale"]) != 0.654:
                raise SystemExit(f"[FAIL] seed {seed} changed Emax or global mu")
            if row["liggghts_commit"] != PINNED_LIGGGHTS_COMMIT:
                raise SystemExit(f"[FAIL] seed {seed} has unpinned solver provenance")
            if not math.isclose(float(row["mu_al_wall"]), wall_mu, abs_tol=1.0e-9):
                raise SystemExit(f"[FAIL] seed {seed} has unexpected Al-wall coefficient")
            if not math.isclose(float(row["mu_diamond_wall"]), wall_mu, abs_tol=1.0e-9):
                raise SystemExit(f"[FAIL] seed {seed} has unexpected diamond-wall coefficient")
            if float(row["mu_al_tool"]) != 0.05232 or float(row["mu_diamond_tool"]) != 0.05232:
                raise SystemExit(f"[FAIL] seed {seed} changed particle-tool friction")
            expected_runtime = {
                "top_velocity_cm_s": 50.0,
                "time_step_seconds": 2.0e-10,
                "initial_settle_steps": 20_000,
                "stage_settle_steps": 20_000,
                "final_settle_steps": 50_000,
            }
            for field, expected in expected_runtime.items():
                if float(row[field]) != expected:
                    raise SystemExit(f"[FAIL] seed {seed} has unexpected {field}")


def pair_rows(
    baseline: list[dict[str, object]], test: list[dict[str, object]]
) -> list[dict[str, object]]:
    paired: list[dict[str, object]] = []
    for old, new in zip(baseline, test, strict=True):
        if old["seed_index"] != new["seed_index"]:
            raise SystemExit("[FAIL] paired seed order differs")
        old_p95 = float(old["p95_mpa"])
        new_p95 = float(new["p95_mpa"])
        paired.append(
            {
                "seed_index": old["seed_index"],
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
            }
        )
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


def decide(baseline: dict[str, object], test: dict[str, object]) -> str:
    baseline_regression = not (
        ZHANG_WINDOW[0] <= float(baseline["p95_mean_mpa"]) <= ZHANG_WINDOW[1]
        and int(baseline["trend_pass_count"]) >= 4
        and int(baseline["pass_and_window_count"]) >= 2
    )
    if baseline_regression:
        return "c_wall_friction_solver_baseline_regression"
    improves = (
        ZHANG_WINDOW[0] <= float(test["p95_mean_mpa"]) <= ZHANG_WINDOW[1]
        and float(test["p95_cv"]) < float(baseline["p95_cv"])
        and float(test["p95_cv"]) < HISTORICAL_BASELINE_CV
        and int(test["trend_pass_count"]) >= 4
        and int(test["pass_and_window_count"]) > 2
    )
    if improves and int(test["pass_and_window_count"]) == 5:
        return "c_wall_friction_seed_robust"
    return "c_wall_friction_improves_tradeoff" if improves else "c_wall_friction_not_better"


def recommendation(decision: str) -> str:
    if decision == "c_wall_friction_solver_baseline_regression":
        return "Stop interpretation and diagnose the pinned-solver baseline before changing physics."
    if decision == "c_wall_friction_seed_robust":
        return "Freeze the low-sidewall-friction C candidate and continue D/E calibration."
    if decision == "c_wall_friction_improves_tradeoff":
        return "Retain mu_w=0.001 as the C contact candidate, but do not call it seed robust."
    return "Reject mu_w=0.001, restore wall scale 1, and return to the contact-model audit before another variable."


def acceptance_row(summary: dict[str, object]) -> dict[str, object]:
    baseline = summary["baseline"]
    test = summary["test"]
    return {
        "artifact_imported": True,
        "workflow_completed": True,
        "solver_provenance_gate": "pass",
        "baseline_regression_gate": (
            "pass"
            if summary["decision"] != "c_wall_friction_solver_baseline_regression"
            else "review"
        ),
        "mean_pressure_gate": gate(
            ZHANG_WINDOW[0] <= float(test["p95_mean_mpa"]) <= ZHANG_WINDOW[1]
        ),
        "cv_gate": gate(
            float(test["p95_cv"]) < float(baseline["p95_cv"])
            and float(test["p95_cv"]) < HISTORICAL_BASELINE_CV
        ),
        "trend_gate": gate(int(test["trend_pass_count"]) >= 4),
        "combined_coverage_gate": gate(int(test["pass_and_window_count"]) > 2),
        "decision": summary["decision"],
    }


def gate(condition: bool) -> str:
    return "pass" if condition else "review"


def percent_change(old: float, new: float) -> float:
    return 100.0 * (new - old) / old if old else math.inf


def write_plot(paired: list[dict[str, object]], figure_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        (figure_dir / "pscale2_c_wall_friction_plots_skipped.txt").write_text(
            "matplotlib unavailable; plots were skipped.\n", encoding="utf-8"
        )
        return
    seeds = [int(row["seed_index"]) for row in paired]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.axhspan(*ZHANG_WINDOW, color="#2f7d32", alpha=0.12)
    ax.plot(seeds, [row["baseline_p95_mpa"] for row in paired], marker="o", label="mu_w=0.05232")
    ax.plot(seeds, [row["test_p95_mpa"] for row in paired], marker="s", label="mu_w=0.001")
    ax.set_xticks(seeds)
    ax.set_xlabel("DEM seed")
    ax.set_ylabel("P95 pressure (MPa)")
    ax.set_title("Zhang C paired sidewall-friction response")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(figure_dir / "pscale2_c_wall_friction_paired.png", dpi=160)
    plt.close(fig)


def write_report(
    path: Path,
    summary: dict[str, object],
    paired: list[dict[str, object]],
    acceptance: dict[str, object],
) -> None:
    baseline = summary["baseline"]
    test = summary["test"]
    lines = [
        "# Zhang pscale=2 C Sidewall-Friction Recheck Results",
        "",
        "## Conclusion",
        "",
        str(summary["recommended_next_step"]),
        "",
        "## Paired Comparison",
        "",
        "| Metric | mu_w=0.05232 | mu_w=0.001 | Change |",
        "|---|---:|---:|---:|",
        f"| Mean P95 MPa | {float(baseline['p95_mean_mpa']):.3f} | {float(test['p95_mean_mpa']):.3f} | {float(summary['p95_mean_delta_mpa']):+.3f} |",
        f"| P95 CV | {float(baseline['p95_cv']):.4f} | {float(test['p95_cv']):.4f} | {float(summary['p95_cv_change_percent']):+.2f}% |",
        f"| Trend pass | {baseline['trend_pass_count']}/5 | {test['trend_pass_count']}/5 | |",
        f"| Pressure window | {baseline['pressure_window_count']}/5 | {test['pressure_window_count']}/5 | |",
        f"| Pass + window | {baseline['pass_and_window_count']}/5 | {test['pass_and_window_count']}/5 | |",
        "",
        "## Paired Seeds",
        "",
        "| Seed | Baseline P95 | Test P95 | Delta MPa | Test pressure | Test trend | Test both |",
        "|---:|---:|---:|---:|---|---|---|",
    ]
    for row in paired:
        lines.append(
            f"| {row['seed_index']} | {float(row['baseline_p95_mpa']):.3f} | {float(row['test_p95_mpa']):.3f} | {float(row['p95_delta_mpa']):+.3f} | "
            f"{'pass' if row['test_pressure_in_window'] else 'review'} | {row['test_status']} | "
            f"{'pass' if row['test_pass_and_window'] else 'review'} |"
        )
    lines.extend(
        [
            "",
            "## Acceptance",
            "",
            "| Solver | Baseline | Mean pressure | CV | Trend | Combined | Decision |",
            "|---|---|---|---|---|---|---|",
            f"| {acceptance['solver_provenance_gate']} | {acceptance['baseline_regression_gate']} | {acceptance['mean_pressure_gate']} | {acceptance['cv_gate']} | {acceptance['trend_gate']} | {acceptance['combined_coverage_gate']} | {acceptance['decision']} |",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    stage = Path("docs/reproduction_goal/03_zhang_particle_scale")
    parser.add_argument("--evidence-root", default=str(stage / "evidence"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--outdir", default=str(stage / "data"))
    parser.add_argument("--figure-dir", default=str(stage / "figures"))
    parser.add_argument("--report", default=str(stage / "pscale2_c_wall_friction_report.md"))
    args = parser.parse_args()
    summary = analyze_wall_friction(
        evidence_root=Path(args.evidence_root),
        run_id=args.run_id,
        outdir=Path(args.outdir),
        figure_dir=Path(args.figure_dir),
        report=Path(args.report),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
