from __future__ import annotations

import csv
import json
import math
from pathlib import Path


SUMMARY_NAME = "zhang_force_chain_calibration_summary.csv"
ZHANG_ENDPOINT_TARGET_MPA = 600.0
ZHANG_ENDPOINT_WINDOW_MPA = (572.0, 638.0)


def aggregate_zhang_calibration(root: Path, outdir: Path) -> dict[str, object]:
    rows = collect_zhang_calibration_rows(root)
    if not rows:
        raise SystemExit(f"[FAIL] no {SUMMARY_NAME} files found under {root}")
    best_rows = best_by_artifact(rows)
    group_rows = summarize_groups(best_rows)
    recommendation = recommend_next_sweep(best_rows)
    outdir.mkdir(parents=True, exist_ok=True)
    write_csv(outdir / "zhang_calibration_candidates.csv", rows)
    write_csv(outdir / "zhang_calibration_best_by_run.csv", best_rows)
    write_csv(outdir / "zhang_calibration_group_summary.csv", group_rows)
    recommendation_json = outdir / "zhang_next_sweep_recommendation.json"
    recommendation_json.write_text(
        json.dumps(recommendation, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    recommendation_md = outdir / "zhang_next_sweep_recommendation.md"
    recommendation_md.write_text(render_recommendation(recommendation), encoding="utf-8")
    report_path = outdir / "zhang_calibration_ensemble_report.md"
    report_path.write_text(render_report(best_rows, group_rows), encoding="utf-8")
    return {
        "candidate_count": len(rows),
        "run_count": len(best_rows),
        "pass_run_count": sum(1 for row in best_rows if row.get("status") == "pass"),
        "best_by_run_csv": str(outdir / "zhang_calibration_best_by_run.csv"),
        "group_summary_csv": str(outdir / "zhang_calibration_group_summary.csv"),
        "next_sweep_json": str(recommendation_json),
        "next_sweep_markdown": str(recommendation_md),
        "report": str(report_path),
    }


def collect_zhang_calibration_rows(root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for summary_path in sorted(root.rglob(SUMMARY_NAME)):
        dem_dir = summary_path.parents[2]
        artifact = dem_dir.parent.name
        params = read_parameters(dem_dir / "model_parameters.csv")
        pressure_summary = first_row(dem_dir / "pressure_density_summary.csv")
        zhang_status = paper_status(dem_dir / "paper_reproduction" / "series_acceptance_summary.csv", "Zhang")
        for row in read_csv(summary_path):
            participation_delta = delta(row, "participation_first", "participation_last")
            d1_delta = delta(row, "d1_first", "d1_last")
            rows.append(
                {
                    "artifact": artifact,
                    "diamond_size_case": params.get("diamond_size_case", "?"),
                    "seed_index": optional_int(params.get("DEM_seed_index")),
                    "e_al_emax_gpa": optional_float(params.get("E_Al_smoothstep_Emax")),
                    "mu_scale": optional_float(params.get("mu_scale")),
                    "p95_mpa": optional_float(pressure_summary.get("p_target_mpa")),
                    "zhang_stage_status": zhang_status,
                    "threshold_factor": optional_float(row.get("threshold_factor")),
                    "min_chain_length": optional_int(row.get("min_chain_length")),
                    "status": row.get("status") or "missing",
                    "trend_score": optional_int(row.get("trend_score")),
                    "chain_coverage": optional_float(row.get("chain_coverage")),
                    "participation_trend": row.get("participation_trend"),
                    "participation_first": optional_float(row.get("participation_first")),
                    "participation_last": optional_float(row.get("participation_last")),
                    "participation_delta": participation_delta,
                    "d1_trend": row.get("d1_trend"),
                    "d1_first": optional_float(row.get("d1_first")),
                    "d1_last": optional_float(row.get("d1_last")),
                    "d1_delta": d1_delta,
                    "calibration_diagnosis": diagnose(row.get("status"), participation_delta, d1_delta),
                }
            )
    return rows


def best_by_artifact(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(str(row["artifact"]), []).append(row)
    return [sorted(group, key=candidate_sort_key)[0] for _, group in sorted(grouped.items())]


def summarize_groups(best_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for field in ("diamond_size_case", "mu_scale", "e_al_emax_gpa"):
        groups: dict[str, list[dict[str, object]]] = {}
        for row in best_rows:
            groups.setdefault(str(row.get(field)), []).append(row)
        for value, rows in sorted(groups.items()):
            participation = finite_values(rows, "participation_delta")
            d1 = finite_values(rows, "d1_delta")
            output.append(
                {
                    "group_by": field,
                    "group_value": value,
                    "run_count": len(rows),
                    "pass_run_count": sum(1 for row in rows if row.get("status") == "pass"),
                    "review_run_count": sum(1 for row in rows if row.get("status") == "review"),
                    "participation_delta_mean": mean(participation),
                    "d1_delta_mean": mean(d1),
                    "best_trend_score": max(
                        optional_int(row.get("trend_score")) or 0 for row in rows
                    ),
                }
            )
    return output


def recommend_next_sweep(best_rows: list[dict[str, object]]) -> dict[str, object]:
    if not best_rows:
        return {
            "status": "missing",
            "reason": "No Zhang calibration rows were available.",
            "workflow_dispatch_inputs": {},
            "estimated_run_count": 0,
        }

    selected = sorted(best_rows, key=recommendation_sort_key)[0]
    pressure = optional_float(selected.get("p95_mpa"))
    trend_pass = selected.get("status") == "pass"
    if trend_pass and pressure_in_endpoint_window(pressure):
        mu_values = [optional_float(selected.get("mu_scale")) or 1.0]
        e_values = [optional_float(selected.get("e_al_emax_gpa")) or 12.0]
        seed_values = [0, 1, 2]
        size_values = ["C", "D", "E"]
        inputs = {
            "runtime_profile": "demo",
            "mu_scale_json": json.dumps(format_value_list(mu_values)),
            "e_al_emax_sweep_json": json.dumps(format_value_list(e_values)),
            "dem_seed_json": json.dumps([str(value) for value in seed_values]),
            "diamond_size_case_json": json.dumps(size_values),
        }
        run_count = len(mu_values) * len(e_values) * len(seed_values) * len(size_values)
        return {
            "status": "ready",
            "next_sweep_mode": "seed_size_robustness",
            "selected_artifact": selected.get("artifact"),
            "selected_status": selected.get("status"),
            "diagnosis": selected.get("calibration_diagnosis"),
            "selected_threshold_factor": selected.get("threshold_factor"),
            "selected_min_chain_length": selected.get("min_chain_length"),
            "selected_mu_scale": selected.get("mu_scale"),
            "selected_e_al_emax_gpa": selected.get("e_al_emax_gpa"),
            "selected_p95_mpa": selected.get("p95_mpa"),
            "zhang_pressure_target_mpa": ZHANG_ENDPOINT_TARGET_MPA,
            "zhang_pressure_window_mpa": list(ZHANG_ENDPOINT_WINDOW_MPA),
            "reason": (
                f"p95={pressure:.3g} MPa is inside Zhang's 572-638 MPa endpoint "
                "window and the force-chain trend candidate passes, so hold the "
                "best mu/E pair fixed and validate robustness across seeds and "
                "diamond size cases"
            ),
            "workflow_dispatch_inputs": inputs,
            "estimated_run_count": run_count,
            "followup_after_light_sweep": (
                "If the seed/size matrix remains inside the pressure window with "
                "Zhang pass trends, promote the parameter pair to the next fidelity "
                "upgrade instead of broadening the light calibration sweep."
            ),
        }

    mu_values, mu_reason = recommend_mu_values(selected)
    e_values, pressure_reason = recommend_emax_values(selected)
    seed_values = recommend_seed_values(selected)
    size_values = recommend_size_values(selected)
    inputs = {
        "runtime_profile": "demo",
        "mu_scale_json": json.dumps(format_value_list(mu_values)),
        "e_al_emax_sweep_json": json.dumps(format_value_list(e_values)),
        "dem_seed_json": json.dumps([str(value) for value in seed_values]),
        "diamond_size_case_json": json.dumps(size_values),
    }
    run_count = len(mu_values) * len(e_values) * len(seed_values) * len(size_values)
    return {
        "status": "ready",
        "selected_artifact": selected.get("artifact"),
        "selected_status": selected.get("status"),
        "diagnosis": selected.get("calibration_diagnosis"),
        "selected_threshold_factor": selected.get("threshold_factor"),
        "selected_min_chain_length": selected.get("min_chain_length"),
        "selected_mu_scale": selected.get("mu_scale"),
        "selected_e_al_emax_gpa": selected.get("e_al_emax_gpa"),
        "selected_p95_mpa": selected.get("p95_mpa"),
        "zhang_pressure_target_mpa": ZHANG_ENDPOINT_TARGET_MPA,
        "zhang_pressure_window_mpa": list(ZHANG_ENDPOINT_WINDOW_MPA),
        "reason": "; ".join(reason for reason in [pressure_reason, mu_reason] if reason),
        "workflow_dispatch_inputs": inputs,
        "estimated_run_count": run_count,
        "followup_after_light_sweep": (
            "If any candidate reaches Zhang pass trends, rerun the best mu/E pair "
            "with dem_seed_json=[\"0\",\"1\",\"2\"] and diamond_size_case_json=[\"C\",\"D\",\"E\"]."
        ),
    }


def recommend_emax_values(row: dict[str, object]) -> tuple[list[float], str]:
    emax = optional_float(row.get("e_al_emax_gpa")) or 12.0
    pressure = optional_float(row.get("p95_mpa"))
    low, high = ZHANG_ENDPOINT_WINDOW_MPA
    if pressure is None or pressure <= 0.0:
        return unique_floats([emax * 1.5, emax * 2.0]), (
            "pressure endpoint is unavailable, so bracket Al modulus upward"
        )
    if pressure < low:
        scale = min(2.5, max(1.25, ZHANG_ENDPOINT_TARGET_MPA / pressure))
        return unique_floats([emax * 1.5, emax * scale]), (
            f"p95={pressure:.3g} MPa is below Zhang's 572-638 MPa endpoint window, "
            "so sweep higher Al endpoint modulus"
        )
    if pressure > high:
        return unique_floats([emax * 0.65, emax * 0.85]), (
            f"p95={pressure:.3g} MPa is above Zhang's 572-638 MPa endpoint window, "
            "so sweep lower Al endpoint modulus"
        )
    return unique_floats([emax * 0.9, emax * 1.1]), (
        "p95 is inside Zhang's pressure endpoint window, so keep a narrow Al modulus bracket"
    )


def recommend_mu_values(row: dict[str, object]) -> tuple[list[float], str]:
    mu = optional_float(row.get("mu_scale")) or 1.0
    diagnosis = str(row.get("calibration_diagnosis") or "")
    if diagnosis == "needs_participation_increase":
        return unique_floats([mu * 0.7, mu, mu * 1.3]), (
            "strong-force participation still decreases, so bracket friction scale "
            "around the current run"
        )
    if diagnosis == "needs_d1_decrease":
        return unique_floats([mu, mu * 1.25, mu * 1.5]), (
            "strong-force participation improves but D1 does not decrease, so test "
            "higher friction-driven rearrangement"
        )
    if diagnosis == "candidate_pass":
        return unique_floats([mu * 0.9, mu, mu * 1.1]), (
            "a Zhang trend candidate exists, so keep a narrow friction bracket"
        )
    return unique_floats([mu * 0.6, mu, mu * 1.4]), (
        "both force-chain trend gates need calibration, so use a wider friction bracket"
    )


def recommend_seed_values(row: dict[str, object]) -> list[int]:
    seed = optional_int(row.get("seed_index"))
    if seed is None:
        return [0]
    return [seed]


def recommend_size_values(row: dict[str, object]) -> list[str]:
    size = row.get("diamond_size_case")
    return [str(size)] if size not in (None, "", "?") else ["C"]


def recommendation_sort_key(
    row: dict[str, object],
) -> tuple[int, int, float, tuple[int, float, float, float, float, float]]:
    pressure = optional_float(row.get("p95_mpa"))
    pressure_rank = 0 if pressure_in_endpoint_window(pressure) else 1
    pressure_distance = (
        abs(pressure - ZHANG_ENDPOINT_TARGET_MPA)
        if pressure is not None
        else math.inf
    )
    status_rank = 0 if row.get("status") == "pass" else 1
    return (
        status_rank,
        pressure_rank,
        pressure_distance,
        candidate_sort_key(row),
    )


def pressure_in_endpoint_window(pressure: float | None) -> bool:
    if pressure is None:
        return False
    low, high = ZHANG_ENDPOINT_WINDOW_MPA
    return low <= pressure <= high


def render_recommendation(recommendation: dict[str, object]) -> str:
    lines = [
        "# Zhang Next Sweep Recommendation",
        "",
        f"- Status: `{recommendation.get('status')}`",
        f"- Selected artifact: `{recommendation.get('selected_artifact', 'missing')}`",
        f"- Diagnosis: `{recommendation.get('diagnosis', 'missing')}`",
        f"- Pressure target: `{format_number(recommendation.get('zhang_pressure_target_mpa'))} MPa`",
        f"- Estimated light runs: `{recommendation.get('estimated_run_count', 0)}`",
        "",
        "## Reason",
        "",
        str(recommendation.get("reason") or "No recommendation reason was generated."),
        "",
        "## Workflow Dispatch Inputs",
        "",
        "```json",
        json.dumps(recommendation.get("workflow_dispatch_inputs", {}), ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Follow-up",
        "",
        str(recommendation.get("followup_after_light_sweep") or "Review the next ensemble summary before broadening the sweep."),
        "",
    ]
    return "\n".join(lines)


def render_report(best_rows: list[dict[str, object]], group_rows: list[dict[str, object]]) -> str:
    pass_count = sum(1 for row in best_rows if row.get("status") == "pass")
    lines = [
        "# Zhang Calibration Ensemble Report",
        "",
        f"- Runs summarized: `{len(best_rows)}`",
        f"- Runs with pass candidate: `{pass_count}`",
        "",
        "## Best Candidate By DEM Run",
        "",
        "| Artifact | Size | Seed | Emax GPa | Mu Scale | Status | Threshold | Min Chain | Participation Delta | D1 Delta | Diagnosis |",
        "|---|---|---:|---:|---:|---|---:|---:|---:|---:|---|",
    ]
    for row in sorted(best_rows, key=candidate_sort_key):
        lines.append(
            "| {artifact} | {size} | {seed} | {emax} | {mu} | {status} | {threshold} | {chain} | {participation} | {d1} | {diagnosis} |".format(
                artifact=row.get("artifact"),
                size=row.get("diamond_size_case"),
                seed=format_number(row.get("seed_index")),
                emax=format_number(row.get("e_al_emax_gpa")),
                mu=format_number(row.get("mu_scale")),
                status=row.get("status"),
                threshold=format_number(row.get("threshold_factor")),
                chain=format_number(row.get("min_chain_length")),
                participation=format_number(row.get("participation_delta")),
                d1=format_number(row.get("d1_delta")),
                diagnosis=row.get("calibration_diagnosis"),
            )
        )
    lines.extend(
        [
            "",
            "## Parameter Group Summary",
            "",
            "| Group By | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in group_rows:
        lines.append(
            "| {group_by} | {value} | {runs} | {passes} | {participation} | {d1} |".format(
                group_by=row.get("group_by"),
                value=row.get("group_value"),
                runs=row.get("run_count"),
                passes=row.get("pass_run_count"),
                participation=format_number(row.get("participation_delta_mean")),
                d1=format_number(row.get("d1_delta_mean")),
            )
        )
    if pass_count == 0:
        lines.extend(
            [
                "",
                "No DEM run has a Zhang `pass` candidate yet. Treat this as evidence to vary contact law, friction, loading path, particle count, or shape model rather than only force-chain post-processing thresholds.",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def candidate_sort_key(row: dict[str, object]) -> tuple[int, float, float, float, float, float]:
    status_rank = 0 if row.get("status") == "pass" else 1
    trend_score = optional_float(row.get("trend_score")) or 0.0
    coverage = optional_float(row.get("chain_coverage")) or 0.0
    participation_delta = optional_float(row.get("participation_delta"))
    d1_delta = optional_float(row.get("d1_delta"))
    threshold = optional_float(row.get("threshold_factor"))
    return (
        status_rank,
        -trend_score,
        -coverage,
        -(participation_delta if participation_delta is not None else -math.inf),
        d1_delta if d1_delta is not None else math.inf,
        threshold if threshold is not None else math.inf,
    )


def diagnose(status: object, participation_delta: float | None, d1_delta: float | None) -> str:
    if status == "pass":
        return "candidate_pass"
    participation_ok = participation_delta is not None and participation_delta > 0.0
    d1_ok = d1_delta is not None and d1_delta < 0.0
    if d1_ok and not participation_ok:
        return "needs_participation_increase"
    if participation_ok and not d1_ok:
        return "needs_d1_decrease"
    return "needs_physics_calibration"


def unique_floats(values: list[float]) -> list[float]:
    output: list[float] = []
    seen: set[str] = set()
    for value in values:
        if not math.isfinite(value) or value <= 0:
            continue
        rounded = round(value, 3)
        key = f"{rounded:.3f}"
        if key in seen:
            continue
        seen.add(key)
        output.append(rounded)
    return output


def format_value_list(values: list[float]) -> list[str]:
    return [format_sweep_value(value) for value in values]


def format_sweep_value(value: float) -> str:
    if abs(value - round(value)) <= 1.0e-9:
        return str(int(round(value)))
    return f"{value:.3f}".rstrip("0").rstrip(".")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_parameters(path: Path) -> dict[str, str]:
    return {row["parameter"]: row["value"] for row in read_csv(path) if "parameter" in row and "value" in row}


def first_row(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    return rows[0] if rows else {}


def paper_status(path: Path, paper: str) -> str:
    for row in read_csv(path):
        if row.get("paper") == paper:
            return row.get("status") or "missing"
    return "missing"


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def delta(row: dict[str, str], first_key: str, last_key: str) -> float | None:
    first = optional_float(row.get(first_key))
    last = optional_float(row.get(last_key))
    if first is None or last is None:
        return None
    return last - first


def finite_values(rows: list[dict[str, object]], field: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = optional_float(row.get(field))
        if value is not None and math.isfinite(value):
            values.append(value)
    return values


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def optional_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def optional_int(value: object) -> int | None:
    number = optional_float(value)
    return int(number) if number is not None else None


def format_number(value: object) -> str:
    number = optional_float(value)
    if number is None:
        return "missing"
    return f"{number:.6g}"
