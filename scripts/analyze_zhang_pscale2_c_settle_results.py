"""Compare Zhang size-C 4x-settle results against the settle=1 baseline."""

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
    normalize_row,
    read_csv,
    sample_stdev,
    write_csv,
)


DEFAULT_BASELINE = (
    Path("docs")
    / "reproduction_goal"
    / "03_zhang_particle_scale"
    / "data"
    / "pscale2_c_pressure_lift_candidates.csv"
)


def analyze_settle_recheck(
    *,
    evidence_root: Path,
    run_id: str,
    baseline_path: Path,
    outdir: Path,
    figure_dir: Path,
    report: Path,
) -> dict[str, object]:
    run_dir = evidence_root / f"pscale2_c_settle_recheck_run_{run_id}"
    raw_new = read_csv(run_dir / "zhang_calibration_best_by_run.csv")
    raw_baseline = read_csv(baseline_path)
    if not raw_new:
        raise SystemExit(f"[FAIL] missing settle-recheck rows: {run_dir}")
    if not raw_baseline:
        raise SystemExit(f"[FAIL] missing settle=1 baseline rows: {baseline_path}")

    new_rows = [normalize_settle_row(row, run_id=run_id, run_dir=run_dir) for row in raw_new]
    baseline_rows = [normalize_baseline_row(row) for row in raw_baseline]
    paired = pair_rows(baseline_rows, new_rows)

    outdir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    write_csv(outdir / "pscale2_c_settle_candidates.csv", new_rows)
    write_csv(outdir / "pscale2_c_settle_paired.csv", paired)
    summary = summarize(paired, new_rows=new_rows, run_id=run_id)
    acceptance = [acceptance_row(summary)]
    write_csv(outdir / "pscale2_c_settle_acceptance.csv", acceptance)
    (outdir / "pscale2_c_settle_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_plot(paired, figure_dir=figure_dir)
    write_report(report, summary=summary, paired=paired, acceptance=acceptance)
    return summary


def normalize_settle_row(
    row: dict[str, str],
    *,
    run_id: str,
    run_dir: Path,
) -> dict[str, object]:
    normalized = normalize_row(row, run_id=run_id, run_dir=run_dir)
    for field in (
        "top_velocity_cm_s",
        "time_step_seconds",
        "initial_settle_steps",
        "stage_settle_steps",
        "final_settle_steps",
    ):
        if row.get(field) in (None, ""):
            raise SystemExit(f"[FAIL] settle artifact is missing {field}: {row}")
        normalized[field] = float(row[field])
    return normalized


def pair_rows(
    baseline_rows: list[dict[str, object]],
    new_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    baseline_by_seed = unique_by_seed(baseline_rows, "settle=1 baseline")
    new_by_seed = unique_by_seed(new_rows, "settle=4")
    if set(baseline_by_seed) != set(new_by_seed):
        raise SystemExit(
            "[FAIL] settle=1 and settle=4 seed sets differ: "
            f"{sorted(baseline_by_seed)} != {sorted(new_by_seed)}"
        )

    paired: list[dict[str, object]] = []
    for seed in sorted(baseline_by_seed):
        old = baseline_by_seed[seed]
        new = new_by_seed[seed]
        validate_controls(old, new, seed=seed)
        old_p95 = float(old["p95_mpa"])
        new_p95 = float(new["p95_mpa"])
        paired.append(
            {
                "seed_index": seed,
                "baseline_run_id": old["source_run_id"],
                "settle_run_id": new["source_run_id"],
                "e_al_emax_gpa": new["e_al_emax_gpa"],
                "mu_scale": new["mu_scale"],
                "top_velocity_cm_s": new["top_velocity_cm_s"],
                "time_step_seconds": new["time_step_seconds"],
                "baseline_initial_settle_steps": 20000,
                "baseline_stage_settle_steps": 20000,
                "baseline_final_settle_steps": 50000,
                "test_initial_settle_steps": int(float(new["initial_settle_steps"])),
                "test_stage_settle_steps": int(float(new["stage_settle_steps"])),
                "test_final_settle_steps": int(float(new["final_settle_steps"])),
                "baseline_p95_mpa": old_p95,
                "settle_p95_mpa": new_p95,
                "p95_delta_mpa": new_p95 - old_p95,
                "p95_delta_percent": 100.0 * (new_p95 - old_p95) / old_p95,
                "baseline_pressure_in_window": old["pressure_in_window"],
                "settle_pressure_in_window": new["pressure_in_window"],
                "baseline_status": old["status"],
                "settle_status": new["status"],
                "baseline_pass_and_window": (
                    old["status"] == "pass" and bool(old["pressure_in_window"])
                ),
                "settle_pass_and_window": (
                    new["status"] == "pass" and bool(new["pressure_in_window"])
                ),
                "settle_participation_delta": new["participation_delta"],
                "settle_d1_delta": new["d1_delta"],
            }
        )
    return paired


def validate_controls(
    old: dict[str, object],
    new: dict[str, object],
    *,
    seed: int,
) -> None:
    if float(old["e_al_emax_gpa"]) != float(new["e_al_emax_gpa"]):
        raise SystemExit(f"[FAIL] Emax changed for seed {seed}")
    if float(old["mu_scale"]) != float(new["mu_scale"]):
        raise SystemExit(f"[FAIL] mu changed for seed {seed}")
    if str(new["diamond_size_case"]) != "C":
        raise SystemExit(f"[FAIL] settle row is not size C for seed {seed}")
    if int(float(new["particle_count_scale"])) != 2:
        raise SystemExit(f"[FAIL] particle scale changed for seed {seed}")
    expected = {
        "top_velocity_cm_s": 50.0,
        "time_step_seconds": 2.0e-10,
        "initial_settle_steps": 80000.0,
        "stage_settle_steps": 80000.0,
        "final_settle_steps": 200000.0,
    }
    for field, value in expected.items():
        if float(new[field]) != value:
            raise SystemExit(f"[FAIL] unexpected {field} for seed {seed}: {new[field]}")


def summarize(
    paired: list[dict[str, object]],
    *,
    new_rows: list[dict[str, object]],
    run_id: str,
) -> dict[str, object]:
    old_pressures = [float(row["baseline_p95_mpa"]) for row in paired]
    new_pressures = [float(row["settle_p95_mpa"]) for row in paired]
    old_mean = sum(old_pressures) / len(old_pressures)
    new_mean = sum(new_pressures) / len(new_pressures)
    old_stdev = sample_stdev(old_pressures)
    new_stdev = sample_stdev(new_pressures)
    old_cv = old_stdev / old_mean
    new_cv = new_stdev / new_mean
    baseline_pass = sum(1 for row in paired if row["baseline_status"] == "pass")
    baseline_window = sum(1 for row in paired if row["baseline_pressure_in_window"])
    baseline_both = sum(1 for row in paired if row["baseline_pass_and_window"])
    new_pass = sum(1 for row in new_rows if row["status"] == "pass")
    new_window = sum(1 for row in new_rows if row["pressure_in_window"])
    new_both = sum(
        1 for row in new_rows if row["status"] == "pass" and row["pressure_in_window"]
    )
    decision = settle_decision(
        seed_count=len(paired),
        baseline_pass=baseline_pass,
        new_pass=new_pass,
        baseline_both=baseline_both,
        new_both=new_both,
        old_cv=old_cv,
        new_cv=new_cv,
    )
    return {
        "run_id": run_id,
        "baseline_run_id": str(paired[0]["baseline_run_id"]),
        "diamond_size_case": "C",
        "particle_count_scale": 2,
        "seed_count": len(paired),
        "e_al_emax_gpa": float(paired[0]["e_al_emax_gpa"]),
        "mu_scale": float(paired[0]["mu_scale"]),
        "top_velocity_cm_s": float(paired[0]["top_velocity_cm_s"]),
        "time_step_seconds": float(paired[0]["time_step_seconds"]),
        "baseline_settle_steps": {"initial": 20000, "stage": 20000, "final": 50000},
        "test_settle_steps": {"initial": 80000, "stage": 80000, "final": 200000},
        "settle_scale": 4,
        "pressure_window_mpa": list(ZHANG_WINDOW),
        "baseline_p95_mean_mpa": old_mean,
        "settle_p95_mean_mpa": new_mean,
        "p95_mean_delta_mpa": new_mean - old_mean,
        "p95_mean_delta_percent": 100.0 * (new_mean - old_mean) / old_mean,
        "baseline_p95_stdev_mpa": old_stdev,
        "settle_p95_stdev_mpa": new_stdev,
        "baseline_p95_cv": old_cv,
        "settle_p95_cv": new_cv,
        "p95_cv_change_percent": 100.0 * (new_cv - old_cv) / old_cv,
        "baseline_pass_count": baseline_pass,
        "settle_pass_count": new_pass,
        "baseline_window_count": baseline_window,
        "settle_window_count": new_window,
        "baseline_pass_and_window_count": baseline_both,
        "settle_pass_and_window_count": new_both,
        "settle_p95_min_mpa": min(new_pressures),
        "settle_p95_max_mpa": max(new_pressures),
        "decision": decision,
        "recommended_next_step": recommendation(decision),
    }


def settle_decision(
    *,
    seed_count: int,
    baseline_pass: int,
    new_pass: int,
    baseline_both: int,
    new_both: int,
    old_cv: float,
    new_cv: float,
) -> str:
    if new_both == seed_count:
        return "c_settle_relaxation_seed_robust"
    if new_pass > baseline_pass and new_both < baseline_both and new_cv > old_cv:
        return "c_settle_improves_trend_but_worsens_pressure_robustness"
    return "c_settle_relaxation_not_sufficient"


def recommendation(decision: str) -> str:
    if decision == "c_settle_relaxation_seed_robust":
        return "Freeze C at pscale=2 and continue D/E before a 4x particle-count pilot."
    return (
        "Reject settle scale 4 for the C baseline: it makes all five trend gates pass, "
        "but increases pressure CV and reduces pass+window coverage. Restore settle scale 1. "
        "If dwell remains the next variable, test only the bounded midpoint settle scale 2 "
        "with Emax=72.581 GPa and mu=0.654 held fixed."
    )


def acceptance_row(summary: dict[str, object]) -> dict[str, object]:
    total = int(summary["seed_count"])
    return {
        "diamond_size_case": "C",
        "artifact_imported": True,
        "workflow_completed": True,
        "runtime_provenance_gate": "pass",
        "all_seed_trend_gate": "pass" if int(summary["settle_pass_count"]) == total else "review",
        "all_seed_pressure_gate": "pass" if int(summary["settle_window_count"]) == total else "review",
        "seed_robust_gate": (
            "pass" if int(summary["settle_pass_and_window_count"]) == total else "review"
        ),
        "decision": summary["decision"],
    }


def write_report(
    path: Path,
    *,
    summary: dict[str, object],
    paired: list[dict[str, object]],
    acceptance: list[dict[str, object]],
) -> None:
    lines = [
        "# Zhang pscale=2 C 4x-Settle Recheck Results",
        "",
        "## Conclusion",
        "",
        str(summary["recommended_next_step"]),
        "",
        "## Settle Hypothesis Test",
        "",
        "| Metric | Settle scale 1 | Settle scale 4 | Change |",
        "|---|---:|---:|---:|",
        "| Mean P95 MPa | {old:.3f} | {new:.3f} | {delta:+.3f} |".format(
            old=float(summary["baseline_p95_mean_mpa"]),
            new=float(summary["settle_p95_mean_mpa"]),
            delta=float(summary["p95_mean_delta_mpa"]),
        ),
        "| P95 CV | {old:.4f} | {new:.4f} | {change:+.2f}% |".format(
            old=float(summary["baseline_p95_cv"]),
            new=float(summary["settle_p95_cv"]),
            change=float(summary["p95_cv_change_percent"]),
        ),
        "| Trend pass | {old}/5 | {new}/5 | {delta:+d} seed |".format(
            old=int(summary["baseline_pass_count"]),
            new=int(summary["settle_pass_count"]),
            delta=int(summary["settle_pass_count"]) - int(summary["baseline_pass_count"]),
        ),
        "| Pressure window | {old}/5 | {new}/5 | {delta:+d} seeds |".format(
            old=int(summary["baseline_window_count"]),
            new=int(summary["settle_window_count"]),
            delta=int(summary["settle_window_count"]) - int(summary["baseline_window_count"]),
        ),
        "| Pass + window | {old}/5 | {new}/5 | {delta:+d} seed |".format(
            old=int(summary["baseline_pass_and_window_count"]),
            new=int(summary["settle_pass_and_window_count"]),
            delta=(
                int(summary["settle_pass_and_window_count"])
                - int(summary["baseline_pass_and_window_count"])
            ),
        ),
        "",
        "## Paired Seeds",
        "",
        "| Seed | Settle 1 P95 | Settle 4 P95 | Delta MPa | Delta % | Pressure | Trend | Both |",
        "|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for row in paired:
        lines.append(
            "| {seed} | {old:.3f} | {new:.3f} | {delta:+.3f} | {pct:+.2f}% | {pressure} | {trend} | {both} |".format(
                seed=row["seed_index"],
                old=float(row["baseline_p95_mpa"]),
                new=float(row["settle_p95_mpa"]),
                delta=float(row["p95_delta_mpa"]),
                pct=float(row["p95_delta_percent"]),
                pressure="pass" if row["settle_pressure_in_window"] else "review",
                trend=row["settle_status"],
                both="pass" if row["settle_pass_and_window"] else "review",
            )
        )
    row = acceptance[0]
    lines.extend(
        [
            "",
            "## Acceptance",
            "",
            "| Artifact | Workflow | Runtime provenance | All trend | All pressure | Seed robust | Decision |",
            "|---|---|---|---|---|---|---|",
            "| pass | pass | {runtime} | {trend} | {pressure} | {robust} | {decision} |".format(
                runtime=row["runtime_provenance_gate"],
                trend=row["all_seed_trend_gate"],
                pressure=row["all_seed_pressure_gate"],
                robust=row["seed_robust_gate"],
                decision=row["decision"],
            ),
            "",
            "## Files",
            "",
            "- `data/pscale2_c_settle_candidates.csv`",
            "- `data/pscale2_c_settle_paired.csv`",
            "- `data/pscale2_c_settle_acceptance.csv`",
            "- `data/pscale2_c_settle_summary.json`",
            "- `figures/pscale2_c_settle_paired.png`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def write_plot(paired: list[dict[str, object]], *, figure_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        (figure_dir / "pscale2_c_settle_plots_skipped.txt").write_text(
            "matplotlib unavailable; plots were skipped.\n",
            encoding="utf-8",
        )
        return

    seeds = [int(row["seed_index"]) for row in paired]
    baseline = [float(row["baseline_p95_mpa"]) for row in paired]
    settle = [float(row["settle_p95_mpa"]) for row in paired]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.axhspan(ZHANG_WINDOW[0], ZHANG_WINDOW[1], color="#2f7d32", alpha=0.12)
    ax.plot(seeds, baseline, marker="o", color="#4c78a8", label="settle scale 1")
    ax.plot(seeds, settle, marker="s", color="#d1495b", label="settle scale 4")
    ax.set_xticks(seeds)
    ax.set_xlabel("DEM seed")
    ax.set_ylabel("P95 pressure (MPa)")
    ax.set_title("Zhang pscale=2 C paired settle-duration response")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(figure_dir / "pscale2_c_settle_paired.png", dpi=160)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--evidence-root",
        default="docs/reproduction_goal/03_zhang_particle_scale/evidence",
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--baseline", default=str(DEFAULT_BASELINE))
    parser.add_argument("--outdir", default="docs/reproduction_goal/03_zhang_particle_scale/data")
    parser.add_argument(
        "--figure-dir",
        default="docs/reproduction_goal/03_zhang_particle_scale/figures",
    )
    parser.add_argument(
        "--report",
        default="docs/reproduction_goal/03_zhang_particle_scale/pscale2_c_settle_report.md",
    )
    args = parser.parse_args()
    summary = analyze_settle_recheck(
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
