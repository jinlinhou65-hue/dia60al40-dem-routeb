"""Compare Zhang size-C pressure-lift results against the prior seed recheck."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from analyze_zhang_pscale2_c_seed_recheck_results import (
    ZHANG_WINDOW,
    format_number,
    normalize_row,
    optional_float,
    read_csv,
    required_float,
    sample_stdev,
    write_csv,
)


DEFAULT_BASELINE = (
    Path("docs")
    / "reproduction_goal"
    / "03_zhang_particle_scale"
    / "data"
    / "pscale2_c_seed_recheck_candidates.csv"
)


def analyze_pressure_lift(
    *,
    evidence_root: Path,
    run_id: str,
    baseline_path: Path,
    outdir: Path,
    figure_dir: Path,
    report: Path,
) -> dict[str, object]:
    run_dir = evidence_root / f"pscale2_c_pressure_lift_recheck_run_{run_id}"
    raw_new = read_csv(run_dir / "zhang_calibration_best_by_run.csv")
    raw_baseline = read_csv(baseline_path)
    if not raw_new:
        raise SystemExit(f"[FAIL] missing pressure-lift rows: {run_dir}")
    if not raw_baseline:
        raise SystemExit(f"[FAIL] missing baseline seed rows: {baseline_path}")

    new_rows = [normalize_row(row, run_id=run_id, run_dir=run_dir) for row in raw_new]
    baseline_rows = [normalize_baseline_row(row) for row in raw_baseline]
    paired = pair_rows(baseline_rows, new_rows)

    outdir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    write_csv(outdir / "pscale2_c_pressure_lift_candidates.csv", new_rows)
    write_csv(outdir / "pscale2_c_pressure_lift_paired.csv", paired)

    summary = summarize(paired, new_rows=new_rows, run_id=run_id)
    acceptance = [acceptance_row(summary)]
    write_csv(outdir / "pscale2_c_pressure_lift_acceptance.csv", acceptance)
    (outdir / "pscale2_c_pressure_lift_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_plot(paired, figure_dir=figure_dir)
    write_report(report, summary=summary, paired=paired, acceptance=acceptance)
    return summary


def normalize_baseline_row(row: dict[str, str]) -> dict[str, object]:
    seed = required_float(row, "seed_index")
    p95 = required_float(row, "p95_mpa")
    return {
        "source_run_id": row.get("source_run_id", ""),
        "seed_index": int(seed),
        "e_al_emax_gpa": required_float(row, "e_al_emax_gpa"),
        "mu_scale": required_float(row, "mu_scale"),
        "p95_mpa": p95,
        "pressure_in_window": str(row.get("pressure_in_window", "")).lower() == "true",
        "status": row.get("status", ""),
        "participation_delta": optional_float(row.get("participation_delta")),
        "d1_delta": optional_float(row.get("d1_delta")),
    }


def pair_rows(
    baseline_rows: list[dict[str, object]],
    new_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    baseline_by_seed = unique_by_seed(baseline_rows, "baseline")
    new_by_seed = unique_by_seed(new_rows, "pressure-lift")
    if set(baseline_by_seed) != set(new_by_seed):
        raise SystemExit(
            "[FAIL] baseline and pressure-lift seed sets differ: "
            f"{sorted(baseline_by_seed)} != {sorted(new_by_seed)}"
        )

    paired: list[dict[str, object]] = []
    for seed in sorted(baseline_by_seed):
        old = baseline_by_seed[seed]
        new = new_by_seed[seed]
        validate_held_variables(old, new, seed=seed)
        old_p95 = float(old["p95_mpa"])
        new_p95 = float(new["p95_mpa"])
        delta = new_p95 - old_p95
        paired.append(
            {
                "seed_index": seed,
                "baseline_run_id": old["source_run_id"],
                "pressure_lift_run_id": new["source_run_id"],
                "baseline_e_al_emax_gpa": old["e_al_emax_gpa"],
                "pressure_lift_e_al_emax_gpa": new["e_al_emax_gpa"],
                "mu_scale": new["mu_scale"],
                "baseline_p95_mpa": old_p95,
                "pressure_lift_p95_mpa": new_p95,
                "p95_delta_mpa": delta,
                "p95_delta_percent": 100.0 * delta / old_p95,
                "baseline_pressure_in_window": old["pressure_in_window"],
                "pressure_lift_pressure_in_window": new["pressure_in_window"],
                "baseline_status": old["status"],
                "pressure_lift_status": new["status"],
                "baseline_pass_and_window": (
                    old["status"] == "pass" and bool(old["pressure_in_window"])
                ),
                "pressure_lift_pass_and_window": (
                    new["status"] == "pass" and bool(new["pressure_in_window"])
                ),
                "pressure_lift_participation_delta": new["participation_delta"],
                "pressure_lift_d1_delta": new["d1_delta"],
            }
        )
    return paired


def unique_by_seed(
    rows: list[dict[str, object]],
    label: str,
) -> dict[int, dict[str, object]]:
    result: dict[int, dict[str, object]] = {}
    for row in rows:
        seed = int(row["seed_index"])
        if seed in result:
            raise SystemExit(f"[FAIL] duplicate {label} row for seed {seed}")
        result[seed] = row
    return result


def validate_held_variables(
    old: dict[str, object],
    new: dict[str, object],
    *,
    seed: int,
) -> None:
    if float(old["mu_scale"]) != float(new["mu_scale"]):
        raise SystemExit(f"[FAIL] mu changed for seed {seed}")
    if str(new["diamond_size_case"]) != "C":
        raise SystemExit(f"[FAIL] pressure-lift row is not size C for seed {seed}")
    if int(float(new["particle_count_scale"])) != 2:
        raise SystemExit(f"[FAIL] particle_count_scale changed for seed {seed}")
    if float(new["e_al_emax_gpa"]) <= float(old["e_al_emax_gpa"]):
        raise SystemExit(f"[FAIL] Emax did not increase for seed {seed}")


def summarize(
    paired: list[dict[str, object]],
    *,
    new_rows: list[dict[str, object]],
    run_id: str,
) -> dict[str, object]:
    old_pressures = [float(row["baseline_p95_mpa"]) for row in paired]
    new_pressures = [float(row["pressure_lift_p95_mpa"]) for row in paired]
    old_mean = sum(old_pressures) / len(old_pressures)
    new_mean = sum(new_pressures) / len(new_pressures)
    old_stdev = sample_stdev(old_pressures)
    new_stdev = sample_stdev(new_pressures)
    old_cv = old_stdev / old_mean
    new_cv = new_stdev / new_mean
    old_emax = float(paired[0]["baseline_e_al_emax_gpa"])
    new_emax = float(paired[0]["pressure_lift_e_al_emax_gpa"])
    emax_gain_percent = 100.0 * (new_emax - old_emax) / old_emax
    pressure_gain_percent = 100.0 * (new_mean - old_mean) / old_mean
    pass_count = sum(1 for row in new_rows if row["status"] == "pass")
    window_count = sum(1 for row in new_rows if row["pressure_in_window"])
    both_count = sum(
        1 for row in new_rows if row["status"] == "pass" and row["pressure_in_window"]
    )
    old_both_count = sum(1 for row in paired if row["baseline_pass_and_window"])
    decision = pressure_lift_decision(
        seed_count=len(paired),
        new_mean=new_mean,
        new_cv=new_cv,
        old_cv=old_cv,
        old_both_count=old_both_count,
        both_count=both_count,
    )
    return {
        "run_id": run_id,
        "baseline_run_id": str(paired[0]["baseline_run_id"]),
        "diamond_size_case": "C",
        "particle_count_scale": 2,
        "seed_count": len(paired),
        "mu_scale": float(paired[0]["mu_scale"]),
        "baseline_e_al_emax_gpa": old_emax,
        "pressure_lift_e_al_emax_gpa": new_emax,
        "e_al_emax_gain_percent": emax_gain_percent,
        "pressure_window_mpa": list(ZHANG_WINDOW),
        "target_pressure_mpa": 600.0,
        "baseline_p95_mean_mpa": old_mean,
        "pressure_lift_p95_mean_mpa": new_mean,
        "p95_mean_delta_mpa": new_mean - old_mean,
        "p95_mean_gain_percent": pressure_gain_percent,
        "target_error_mpa": new_mean - 600.0,
        "baseline_p95_stdev_mpa": old_stdev,
        "pressure_lift_p95_stdev_mpa": new_stdev,
        "baseline_p95_cv": old_cv,
        "pressure_lift_p95_cv": new_cv,
        "p95_cv_reduction_percent": 100.0 * (old_cv - new_cv) / old_cv,
        "mean_pressure_response_ratio": pressure_gain_percent / emax_gain_percent,
        "baseline_pass_and_window_count": old_both_count,
        "pressure_lift_pass_count": pass_count,
        "pressure_lift_window_count": window_count,
        "pressure_lift_pass_and_window_count": both_count,
        "pressure_lift_p95_min_mpa": min(new_pressures),
        "pressure_lift_p95_max_mpa": max(new_pressures),
        "decision": decision,
        "recommended_next_step": recommendation(decision, both_count, len(paired)),
    }


def pressure_lift_decision(
    *,
    seed_count: int,
    new_mean: float,
    new_cv: float,
    old_cv: float,
    old_both_count: int,
    both_count: int,
) -> str:
    if both_count == seed_count:
        return "c_pressure_lift_seed_robust"
    if ZHANG_WINDOW[0] <= new_mean <= ZHANG_WINDOW[1] and both_count > old_both_count and new_cv < old_cv:
        return "c_pressure_lift_improves_but_not_seed_robust"
    return "c_pressure_lift_not_sufficient"


def recommendation(decision: str, both_count: int, total: int) -> str:
    if decision == "c_pressure_lift_seed_robust":
        return "Freeze C at pscale=2 and continue D/E calibration before a 4x pilot."
    return (
        f"The Emax lift improved C but only {both_count}/{total} seeds pass both gates. "
        "Keep Emax=72.581 GPa as the pressure reference, but do not raise Emax again as "
        "the sole control. Next change one loading-path or contact-relaxation variable to "
        "reduce seed variance, then rerun the same five seeds with mu held at 0.654."
    )


def acceptance_row(summary: dict[str, object]) -> dict[str, object]:
    seed_count = int(summary["seed_count"])
    return {
        "diamond_size_case": "C",
        "artifact_imported": True,
        "workflow_completed": True,
        "mean_pressure_gate": (
            "pass"
            if ZHANG_WINDOW[0] <= float(summary["pressure_lift_p95_mean_mpa"]) <= ZHANG_WINDOW[1]
            else "review"
        ),
        "all_seed_pressure_gate": (
            "pass" if int(summary["pressure_lift_window_count"]) == seed_count else "review"
        ),
        "all_seed_trend_gate": (
            "pass" if int(summary["pressure_lift_pass_count"]) == seed_count else "review"
        ),
        "seed_robust_gate": (
            "pass"
            if int(summary["pressure_lift_pass_and_window_count"]) == seed_count
            else "review"
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
        "# Zhang pscale=2 C Pressure-Lift Recheck Results",
        "",
        "## Conclusion",
        "",
        str(summary["recommended_next_step"]),
        "",
        "## Hypothesis Test",
        "",
        "| Metric | Baseline | Pressure lift | Change |",
        "|---|---:|---:|---:|",
        "| Emax GPa | {old_e:.3f} | {new_e:.3f} | {e_gain:+.2f}% |".format(
            old_e=float(summary["baseline_e_al_emax_gpa"]),
            new_e=float(summary["pressure_lift_e_al_emax_gpa"]),
            e_gain=float(summary["e_al_emax_gain_percent"]),
        ),
        "| Mean P95 MPa | {old:.3f} | {new:.3f} | {gain:+.2f}% |".format(
            old=float(summary["baseline_p95_mean_mpa"]),
            new=float(summary["pressure_lift_p95_mean_mpa"]),
            gain=float(summary["p95_mean_gain_percent"]),
        ),
        "| P95 CV | {old:.4f} | {new:.4f} | {change:+.2f}% |".format(
            old=float(summary["baseline_p95_cv"]),
            new=float(summary["pressure_lift_p95_cv"]),
            change=-float(summary["p95_cv_reduction_percent"]),
        ),
        "| Pass + window seeds | {old:.0f}/5 | {new:.0f}/5 | +{delta:.0f} seed |".format(
            old=float(summary["baseline_pass_and_window_count"]),
            new=float(summary["pressure_lift_pass_and_window_count"]),
            delta=(
                float(summary["pressure_lift_pass_and_window_count"])
                - float(summary["baseline_pass_and_window_count"])
            ),
        ),
        "",
        "The Emax increase was {e_gain:.2f}%, while mean P95 increased only {p_gain:.2f}% "
        "(response ratio {ratio:.3f}). The proportional 600 MPa hypothesis therefore "
        "over-predicted the ensemble mean by {miss:.3f} MPa.".format(
            e_gain=float(summary["e_al_emax_gain_percent"]),
            p_gain=float(summary["p95_mean_gain_percent"]),
            ratio=float(summary["mean_pressure_response_ratio"]),
            miss=abs(float(summary["target_error_mpa"])),
        ),
        "",
        "## Paired Seeds",
        "",
        "| Seed | Baseline P95 | Lift P95 | Delta MPa | Delta % | Pressure Gate | Trend | Both |",
        "|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for row in paired:
        lines.append(
            "| {seed} | {old:.3f} | {new:.3f} | {delta:+.3f} | {pct:+.2f}% | {pressure} | {trend} | {both} |".format(
                seed=row["seed_index"],
                old=float(row["baseline_p95_mpa"]),
                new=float(row["pressure_lift_p95_mpa"]),
                delta=float(row["p95_delta_mpa"]),
                pct=float(row["p95_delta_percent"]),
                pressure="pass" if row["pressure_lift_pressure_in_window"] else "review",
                trend=row["pressure_lift_status"],
                both="pass" if row["pressure_lift_pass_and_window"] else "review",
            )
        )
    row = acceptance[0]
    lines.extend(
        [
            "",
            "## Acceptance",
            "",
            "| Artifact | Workflow | Mean pressure | All-seed pressure | All-seed trend | Seed robust | Decision |",
            "|---|---|---|---|---|---|---|",
            "| pass | pass | {mean} | {pressure} | {trend} | {robust} | {decision} |".format(
                mean=row["mean_pressure_gate"],
                pressure=row["all_seed_pressure_gate"],
                trend=row["all_seed_trend_gate"],
                robust=row["seed_robust_gate"],
                decision=row["decision"],
            ),
            "",
            "## Files",
            "",
            "- `data/pscale2_c_pressure_lift_candidates.csv`",
            "- `data/pscale2_c_pressure_lift_paired.csv`",
            "- `data/pscale2_c_pressure_lift_acceptance.csv`",
            "- `data/pscale2_c_pressure_lift_summary.json`",
            "- `figures/pscale2_c_pressure_lift_paired.png`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def write_plot(paired: list[dict[str, object]], *, figure_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        (figure_dir / "pscale2_c_pressure_lift_plots_skipped.txt").write_text(
            "matplotlib unavailable; plots were skipped.\n",
            encoding="utf-8",
        )
        return

    seeds = [int(row["seed_index"]) for row in paired]
    old = [float(row["baseline_p95_mpa"]) for row in paired]
    new = [float(row["pressure_lift_p95_mpa"]) for row in paired]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.axhspan(ZHANG_WINDOW[0], ZHANG_WINDOW[1], color="#2f7d32", alpha=0.12)
    ax.plot(seeds, old, marker="o", color="#4c78a8", label="Emax 63.462 GPa")
    ax.plot(seeds, new, marker="s", color="#d1495b", label="Emax 72.581 GPa")
    ax.set_xticks(seeds)
    ax.set_xlabel("DEM seed")
    ax.set_ylabel("P95 pressure (MPa)")
    ax.set_title("Zhang pscale=2 C paired pressure-lift response")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(figure_dir / "pscale2_c_pressure_lift_paired.png", dpi=160)
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
        default=(
            "docs/reproduction_goal/03_zhang_particle_scale/"
            "pscale2_c_pressure_lift_report.md"
        ),
    )
    args = parser.parse_args()

    summary = analyze_pressure_lift(
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
