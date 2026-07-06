"""Analyze the preregistered Zhang size-E five-seed Emax pressure lift."""

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
    PINNED_LIGGGHTS_COMMIT,
    group_metrics,
)


TARGET_EMAX_GPA = 96.417
TARGET_MU_SCALE = 0.693
SOURCE_EMAX_GPA = 87.368
SOURCE_P95_MPA = 543.689453
EXPECTED_SEEDS = set(range(5))


def analyze_e_pressure_lift(
    *,
    evidence_root: Path,
    run_id: str,
    outdir: Path,
    figure_dir: Path,
    report: Path,
) -> dict[str, object]:
    run_dir = evidence_root / f"pscale2_e_pressure_lift_recheck_run_{run_id}"
    rows = [
        normalize_row(row, run_id=run_id, run_dir=run_dir)
        for row in read_csv(run_dir / "zhang_calibration_best_by_run.csv")
    ]
    validate_group(rows)
    metrics = group_metrics(rows)
    seed2 = next(row for row in rows if int(row["seed_index"]) == 2)
    seed2_delta = float(seed2["p95_mpa"]) - SOURCE_P95_MPA
    decision = decide(metrics, seed2)
    summary = {
        "run_id": run_id,
        "source_run_id": "27883035658",
        "diamond_size_case": "E",
        "particle_count_scale": 2,
        "seed_count": 5,
        "mu_scale": TARGET_MU_SCALE,
        "mu_wall_scale": 1.0,
        "liggghts_commit": PINNED_LIGGGHTS_COMMIT,
        "source_seed_index": 2,
        "source_e_al_emax_gpa": SOURCE_EMAX_GPA,
        "source_seed2_p95_mpa": SOURCE_P95_MPA,
        "source_seed2_status": "pass",
        "pressure_lift_e_al_emax_gpa": TARGET_EMAX_GPA,
        "target_pressure_mpa": 600.0,
        "pressure_window_mpa": list(ZHANG_WINDOW),
        "test": metrics,
        "seed2_test_p95_mpa": float(seed2["p95_mpa"]),
        "seed2_p95_delta_mpa": seed2_delta,
        "seed2_test_status": seed2["status"],
        "decision": decision,
        "recommended_next_step": recommendation(decision),
    }
    acceptance = acceptance_row(summary)

    outdir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    write_csv(outdir / "pscale2_e_pressure_lift_candidates.csv", rows)
    write_csv(outdir / "pscale2_e_pressure_lift_acceptance.csv", [acceptance])
    (outdir / "pscale2_e_pressure_lift_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_plot(rows, figure_dir)
    write_report(report, summary, rows, acceptance)
    return summary


def normalize_row(
    row: dict[str, str], *, run_id: str, run_dir: Path
) -> dict[str, object]:
    p95 = required_float(row, "p95_mpa")
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
        "p95_mpa": p95,
        "pressure_in_window": ZHANG_WINDOW[0] <= p95 <= ZHANG_WINDOW[1],
        "status": row.get("status", ""),
        "participation_delta": optional_float(row.get("participation_delta")),
        "d1_delta": optional_float(row.get("d1_delta")),
    }


def validate_group(rows: list[dict[str, object]]) -> None:
    by_seed = {int(row["seed_index"]): row for row in rows}
    if len(rows) != len(by_seed) or set(by_seed) != EXPECTED_SEEDS:
        raise SystemExit("[FAIL] E test must contain one row for each seed 0..4")
    expected_friction = {
        "mu_al_al": 0.2079,
        "mu_al_diamond": 0.2079,
        "mu_diamond_diamond": 0.0693,
        "mu_al_wall": 0.05544,
        "mu_diamond_wall": 0.05544,
        "mu_al_tool": 0.05544,
        "mu_diamond_tool": 0.05544,
    }
    expected_runtime = {
        "top_velocity_cm_s": 50.0,
        "time_step_seconds": 2.0e-10,
        "initial_settle_steps": 20_000,
        "stage_settle_steps": 20_000,
        "final_settle_steps": 50_000,
    }
    for seed, row in by_seed.items():
        if row["diamond_size_case"] != "E" or int(row["particle_count_scale"]) != 2:
            raise SystemExit(f"[FAIL] seed {seed} changed size or particle scale")
        if not math.isclose(float(row["e_al_emax_gpa"]), TARGET_EMAX_GPA, abs_tol=1e-9):
            raise SystemExit(f"[FAIL] seed {seed} changed target Emax")
        if not math.isclose(float(row["mu_scale"]), TARGET_MU_SCALE, abs_tol=1e-12):
            raise SystemExit(f"[FAIL] seed {seed} changed global mu")
        if float(row["mu_wall_scale"]) != 1.0:
            raise SystemExit(f"[FAIL] seed {seed} changed wall scale")
        if row["liggghts_commit"] != PINNED_LIGGGHTS_COMMIT:
            raise SystemExit(f"[FAIL] seed {seed} has unpinned solver provenance")
        for field, expected in expected_friction.items():
            if not math.isclose(float(row[field]), expected, abs_tol=1e-9):
                raise SystemExit(f"[FAIL] seed {seed} changed {field}")
        for field, expected in expected_runtime.items():
            if float(row[field]) != expected:
                raise SystemExit(f"[FAIL] seed {seed} changed {field}")


def decide(metrics: dict[str, object], seed2: dict[str, object]) -> str:
    mean_ok = ZHANG_WINDOW[0] <= float(metrics["p95_mean_mpa"]) <= ZHANG_WINDOW[1]
    trend_ok = int(metrics["trend_pass_count"]) >= 4
    combined_ok = int(metrics["pass_and_window_count"]) >= 3
    seed2_ok = (
        float(seed2["p95_mpa"]) > SOURCE_P95_MPA and seed2["status"] == "pass"
    )
    if mean_ok and int(metrics["pass_and_window_count"]) == 5:
        return "e_pressure_lift_seed_robust"
    if mean_ok and trend_ok and combined_ok and seed2_ok:
        return "e_pressure_lift_candidate"
    return "e_pressure_lift_not_sufficient"


def recommendation(decision: str) -> str:
    if decision == "e_pressure_lift_seed_robust":
        return "Freeze the E pscale=2 pressure candidate and move to D trend calibration."
    if decision == "e_pressure_lift_candidate":
        return "Retain Emax=96.417 GPa for E, but keep the stage in review until D is calibrated."
    return "Reject Emax=96.417 GPa as a robust E candidate and diagnose the pressure/trend tradeoff before another run."


def acceptance_row(summary: dict[str, object]) -> dict[str, object]:
    test = summary["test"]
    return {
        "artifact_imported": True,
        "workflow_completed": True,
        "solver_provenance_gate": "pass",
        "mean_pressure_gate": gate(
            ZHANG_WINDOW[0] <= float(test["p95_mean_mpa"]) <= ZHANG_WINDOW[1]
        ),
        "trend_gate": gate(int(test["trend_pass_count"]) >= 4),
        "combined_coverage_gate": gate(int(test["pass_and_window_count"]) >= 3),
        "seed2_pressure_direction_gate": gate(float(summary["seed2_p95_delta_mpa"]) > 0),
        "seed2_trend_gate": gate(summary["seed2_test_status"] == "pass"),
        "decision": summary["decision"],
    }


def gate(condition: bool) -> str:
    return "pass" if condition else "review"


def write_plot(rows: list[dict[str, object]], figure_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        (figure_dir / "pscale2_e_pressure_lift_plots_skipped.txt").write_text(
            "matplotlib unavailable; plots were skipped.\n", encoding="utf-8"
        )
        return
    rows = sorted(rows, key=lambda row: int(row["seed_index"]))
    seeds = [int(row["seed_index"]) for row in rows]
    pressures = [float(row["p95_mpa"]) for row in rows]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.axhspan(*ZHANG_WINDOW, color="#2f7d32", alpha=0.12)
    ax.plot(seeds, pressures, marker="s", label="Emax=96.417 GPa")
    ax.scatter([2], [SOURCE_P95_MPA], marker="o", color="#d1495b", label="source seed 2")
    ax.set_xticks(seeds)
    ax.set_xlabel("DEM seed")
    ax.set_ylabel("P95 pressure (MPa)")
    ax.set_title("Zhang pscale=2 E pressure-lift response")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(figure_dir / "pscale2_e_pressure_lift_p95.png", dpi=160)
    plt.close(fig)


def write_report(
    path: Path,
    summary: dict[str, object],
    rows: list[dict[str, object]],
    acceptance: dict[str, object],
) -> None:
    test = summary["test"]
    lines = [
        "# Zhang pscale=2 E Pressure-Lift Recheck Results",
        "",
        "## Conclusion",
        "",
        str(summary["recommended_next_step"]),
        "",
        "## Ensemble",
        "",
        "| Mean P95 MPa | CV | Trend pass | Pressure window | Pass + window | Seed-2 delta MPa |",
        "|---:|---:|---:|---:|---:|---:|",
        f"| {float(test['p95_mean_mpa']):.3f} | {float(test['p95_cv']):.4f} | {test['trend_pass_count']}/5 | {test['pressure_window_count']}/5 | {test['pass_and_window_count']}/5 | {float(summary['seed2_p95_delta_mpa']):+.3f} |",
        "",
        "## Seeds",
        "",
        "| Seed | P95 MPa | Pressure | Trend | Both | Participation delta | D1 delta |",
        "|---:|---:|---|---|---|---:|---:|",
    ]
    for row in sorted(rows, key=lambda item: int(item["seed_index"])):
        both = row["status"] == "pass" and bool(row["pressure_in_window"])
        lines.append(
            f"| {row['seed_index']} | {float(row['p95_mpa']):.3f} | "
            f"{'pass' if row['pressure_in_window'] else 'review'} | {row['status']} | "
            f"{'pass' if both else 'review'} | {float(row['participation_delta']):.4f} | "
            f"{float(row['d1_delta']):.4f} |"
        )
    lines.extend(
        [
            "",
            "## Acceptance",
            "",
            "| Solver | Mean pressure | Trend | Combined | Seed-2 pressure | Seed-2 trend | Decision |",
            "|---|---|---|---|---|---|---|",
            f"| {acceptance['solver_provenance_gate']} | {acceptance['mean_pressure_gate']} | {acceptance['trend_gate']} | {acceptance['combined_coverage_gate']} | {acceptance['seed2_pressure_direction_gate']} | {acceptance['seed2_trend_gate']} | {acceptance['decision']} |",
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
    parser.add_argument("--report", default=str(stage / "pscale2_e_pressure_lift_report.md"))
    args = parser.parse_args()
    summary = analyze_e_pressure_lift(
        evidence_root=Path(args.evidence_root),
        run_id=args.run_id,
        outdir=Path(args.outdir),
        figure_dir=Path(args.figure_dir),
        report=Path(args.report),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
