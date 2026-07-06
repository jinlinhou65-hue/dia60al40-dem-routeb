"""Compare a verified Zhang C baseline with a low interparticle-friction run."""

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
    write_csv,
)
from analyze_zhang_pscale2_c_wall_friction_results import (
    HISTORICAL_BASELINE_CV,
    PINNED_LIGGGHTS_COMMIT,
    group_metrics,
    normalize_row as normalize_wall_row,
    select_scale,
    validate_groups,
)


BASELINE_RUN_ID = "28747847286"
TARGET_PARTICLE_MU = 0.001
EXPECTED_SEEDS = set(range(5))


def analyze_particle_friction(
    *,
    evidence_root: Path,
    baseline_run_id: str,
    test_run_id: str,
    outdir: Path,
    figure_dir: Path,
    report: Path,
) -> dict[str, object]:
    baseline_dir = evidence_root / f"pscale2_c_wall_friction_recheck_run_{baseline_run_id}"
    prior_raw = read_csv(baseline_dir / "zhang_calibration_best_by_run.csv")
    prior = [
        normalize_wall_row(row, run_id=baseline_run_id, run_dir=baseline_dir)
        for row in prior_raw
    ]
    baseline_rows = select_scale(prior, 1.0, "baseline")
    prior_low_wall = select_scale(prior, 0.019113, "prior-low-wall")
    validate_groups(baseline_rows, prior_low_wall)

    test_dir = evidence_root / f"pscale2_c_particle_friction_recheck_run_{test_run_id}"
    test_rows = [normalize_test_row(row, test_run_id, test_dir) for row in read_csv(
        test_dir / "zhang_calibration_best_by_run.csv"
    )]
    validate_test_group(test_rows)

    paired = pair_rows(baseline_rows, test_rows)
    baseline = group_metrics(baseline_rows)
    test = group_metrics(test_rows)
    decision = decide(baseline, test)
    summary = {
        "baseline_run_id": baseline_run_id,
        "test_run_id": test_run_id,
        "diamond_size_case": "C",
        "particle_count_scale": 2,
        "seed_count": 5,
        "e_al_emax_gpa": 72.581,
        "mu_scale": 0.654,
        "mu_wall_scale": 1.0,
        "liggghts_commit": PINNED_LIGGGHTS_COMMIT,
        "pressure_window_mpa": list(ZHANG_WINDOW),
        "historical_baseline_cv": HISTORICAL_BASELINE_CV,
        "baseline_effective_particle_mu": {
            "al_al": 0.1962,
            "al_diamond": 0.1962,
            "diamond_diamond": 0.0654,
        },
        "test_effective_particle_mu": TARGET_PARTICLE_MU,
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
    write_csv(outdir / "pscale2_c_particle_friction_candidates.csv", test_rows)
    write_csv(outdir / "pscale2_c_particle_friction_paired.csv", paired)
    write_csv(outdir / "pscale2_c_particle_friction_acceptance.csv", [acceptance])
    (outdir / "pscale2_c_particle_friction_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_plot(paired, figure_dir)
    write_report(report, summary, paired, acceptance)
    return summary


def normalize_test_row(
    row: dict[str, str], run_id: str, run_dir: Path
) -> dict[str, object]:
    return {
        "source_run_id": run_id,
        "source_run_dir": run_dir.as_posix(),
        "artifact": row.get("artifact", ""),
        "diamond_size_case": row.get("diamond_size_case", ""),
        "particle_count_scale": int(required_float(row, "particle_count_scale")),
        "seed_index": int(required_float(row, "seed_index")),
        "e_al_emax_gpa": required_float(row, "e_al_emax_gpa"),
        "mu_scale": required_float(row, "mu_scale"),
        "mu_wall_scale": required_float(row, "mu_wall_scale"),
        "mu_al_al": required_float(row, "mu_al_al"),
        "mu_al_diamond": required_float(row, "mu_al_diamond"),
        "mu_diamond_diamond": required_float(row, "mu_diamond_diamond"),
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
        "p95_mpa": required_float(row, "p95_mpa"),
        "pressure_in_window": ZHANG_WINDOW[0]
        <= required_float(row, "p95_mpa")
        <= ZHANG_WINDOW[1],
        "status": row.get("status", ""),
        "participation_delta": optional_float(row.get("participation_delta")),
        "d1_delta": optional_float(row.get("d1_delta")),
    }


def validate_test_group(rows: list[dict[str, object]]) -> None:
    by_seed = {int(row["seed_index"]): row for row in rows}
    if len(rows) != len(by_seed) or set(by_seed) != EXPECTED_SEEDS:
        raise SystemExit("[FAIL] test must contain one row for each seed 0..4")
    for seed, row in by_seed.items():
        if row["diamond_size_case"] != "C" or int(row["particle_count_scale"]) != 2:
            raise SystemExit(f"[FAIL] seed {seed} changed size or particle scale")
        if float(row["e_al_emax_gpa"]) != 72.581 or float(row["mu_scale"]) != 0.654:
            raise SystemExit(f"[FAIL] seed {seed} changed Emax or global mu")
        if float(row["mu_wall_scale"]) != 1.0:
            raise SystemExit(f"[FAIL] seed {seed} changed wall scale")
        if row["liggghts_commit"] != PINNED_LIGGGHTS_COMMIT:
            raise SystemExit(f"[FAIL] seed {seed} has unpinned solver provenance")
        for field in ("mu_al_al", "mu_al_diamond", "mu_diamond_diamond"):
            if not math.isclose(float(row[field]), TARGET_PARTICLE_MU, abs_tol=1.0e-9):
                raise SystemExit(f"[FAIL] seed {seed} has unexpected {field}")
        for field in ("mu_al_wall", "mu_diamond_wall", "mu_al_tool", "mu_diamond_tool"):
            if not math.isclose(float(row[field]), 0.05232, abs_tol=1.0e-9):
                raise SystemExit(f"[FAIL] seed {seed} changed {field}")
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
    baseline_by_seed = {int(row["seed_index"]): row for row in baseline}
    test_by_seed = {int(row["seed_index"]): row for row in test}
    paired: list[dict[str, object]] = []
    for seed in sorted(EXPECTED_SEEDS):
        old = baseline_by_seed[seed]
        new = test_by_seed[seed]
        old_p95 = float(old["p95_mpa"])
        new_p95 = float(new["p95_mpa"])
        old_both = old["status"] == "pass" and bool(old["pressure_in_window"])
        new_both = new["status"] == "pass" and bool(new["pressure_in_window"])
        paired.append(
            {
                "seed_index": seed,
                "baseline_p95_mpa": old_p95,
                "test_p95_mpa": new_p95,
                "p95_delta_mpa": new_p95 - old_p95,
                "p95_delta_percent": 100.0 * (new_p95 - old_p95) / old_p95,
                "baseline_status": old["status"],
                "test_status": new["status"],
                "baseline_pressure_in_window": old["pressure_in_window"],
                "test_pressure_in_window": new["pressure_in_window"],
                "baseline_pass_and_window": old_both,
                "test_pass_and_window": new_both,
                "test_participation_delta": new["participation_delta"],
                "test_d1_delta": new["d1_delta"],
            }
        )
    return paired


def decide(baseline: dict[str, object], test: dict[str, object]) -> str:
    baseline_ok = (
        ZHANG_WINDOW[0] <= float(baseline["p95_mean_mpa"]) <= ZHANG_WINDOW[1]
        and int(baseline["trend_pass_count"]) >= 4
        and int(baseline["pass_and_window_count"]) >= 2
    )
    if not baseline_ok:
        return "c_particle_friction_solver_baseline_regression"
    improves = (
        ZHANG_WINDOW[0] <= float(test["p95_mean_mpa"]) <= ZHANG_WINDOW[1]
        and float(test["p95_cv"]) < float(baseline["p95_cv"])
        and float(test["p95_cv"]) < HISTORICAL_BASELINE_CV
        and int(test["trend_pass_count"]) >= 4
        and int(test["pass_and_window_count"]) > 2
    )
    if improves and int(test["pass_and_window_count"]) == 5:
        return "c_particle_friction_seed_robust"
    return "c_particle_friction_improves_tradeoff" if improves else "c_particle_friction_not_better"


def recommendation(decision: str) -> str:
    if decision == "c_particle_friction_solver_baseline_regression":
        return "Stop interpretation and diagnose the reused baseline."
    if decision == "c_particle_friction_seed_robust":
        return "Freeze mu_p=0.001 as the C contact candidate and continue D/E calibration."
    if decision == "c_particle_friction_improves_tradeoff":
        return "Retain mu_p=0.001 for C, but do not call it seed robust."
    return "Reject mu_p=0.001 and retain the verified C baseline before another mechanism."


def acceptance_row(summary: dict[str, object]) -> dict[str, object]:
    baseline = summary["baseline"]
    test = summary["test"]
    return {
        "artifact_imported": True,
        "workflow_completed": True,
        "solver_provenance_gate": "pass",
        "baseline_reuse_gate": "pass",
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
        (figure_dir / "pscale2_c_particle_friction_plots_skipped.txt").write_text(
            "matplotlib unavailable; plots were skipped.\n", encoding="utf-8"
        )
        return
    seeds = [int(row["seed_index"]) for row in paired]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.axhspan(*ZHANG_WINDOW, color="#2f7d32", alpha=0.12)
    ax.plot(seeds, [row["baseline_p95_mpa"] for row in paired], marker="o", label="verified baseline")
    ax.plot(seeds, [row["test_p95_mpa"] for row in paired], marker="s", label="mu_p=0.001")
    ax.set_xticks(seeds)
    ax.set_xlabel("DEM seed")
    ax.set_ylabel("P95 pressure (MPa)")
    ax.set_title("Zhang C paired interparticle-friction response")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(figure_dir / "pscale2_c_particle_friction_paired.png", dpi=160)
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
        "# Zhang pscale=2 C Interparticle-Friction Recheck Results",
        "",
        "## Conclusion",
        "",
        str(summary["recommended_next_step"]),
        "",
        "## Paired Comparison",
        "",
        "| Metric | Verified baseline | mu_p=0.001 | Change |",
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
            "| Solver | Baseline reuse | Mean pressure | CV | Trend | Combined | Decision |",
            "|---|---|---|---|---|---|---|",
            f"| {acceptance['solver_provenance_gate']} | {acceptance['baseline_reuse_gate']} | {acceptance['mean_pressure_gate']} | {acceptance['cv_gate']} | {acceptance['trend_gate']} | {acceptance['combined_coverage_gate']} | {acceptance['decision']} |",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    stage = Path("docs/reproduction_goal/03_zhang_particle_scale")
    parser.add_argument("--evidence-root", default=str(stage / "evidence"))
    parser.add_argument("--baseline-run-id", default=BASELINE_RUN_ID)
    parser.add_argument("--test-run-id", required=True)
    parser.add_argument("--outdir", default=str(stage / "data"))
    parser.add_argument("--figure-dir", default=str(stage / "figures"))
    parser.add_argument("--report", default=str(stage / "pscale2_c_particle_friction_report.md"))
    args = parser.parse_args()
    summary = analyze_particle_friction(
        evidence_root=Path(args.evidence_root),
        baseline_run_id=args.baseline_run_id,
        test_run_id=args.test_run_id,
        outdir=Path(args.outdir),
        figure_dir=Path(args.figure_dir),
        report=Path(args.report),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
