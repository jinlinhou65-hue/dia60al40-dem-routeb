"""Dispatch a one-variable loading-rate recheck for Zhang size C."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path

from dispatch_zhang_pscale2_c_pressure_lift_recheck import (
    format_value,
    parse_seed_json,
    read_summary,
    required_float,
)
from dispatch_zhang_size_specific_sweeps import (
    BASE_DEM_INPUTS,
    DEM_WORKFLOW,
    dispatch_payloads,
)


DEFAULT_SUMMARY = (
    Path("docs")
    / "reproduction_goal"
    / "03_zhang_particle_scale"
    / "data"
    / "pscale2_c_settle_midpoint_summary.json"
)
DEFAULT_SEEDS = ["0", "1", "2", "3", "4"]
BASELINE_VELOCITY_CM_S = 50.0
DEFAULT_TARGET_VELOCITY_CM_S = 25.0
BASELINE_SETTLE_STEPS = {"initial": 20_000, "stage": 20_000, "final": 50_000}


def build_c_loading_rate_payload(
    summary: dict[str, object],
    *,
    ref: str,
    seeds: list[str],
    target_velocity_cm_s: float,
) -> tuple[list[dict[str, object]], int]:
    if not seeds or len(set(seeds)) != len(seeds):
        raise SystemExit("[FAIL] seeds must be a non-empty unique list")
    if summary.get("decision") != "c_settle_midpoint_not_better":
        raise SystemExit(
            "[FAIL] source summary does not justify leaving the dwell branch: "
            f"{summary.get('decision')!r}"
        )
    if summary.get("diamond_size_case") != "C":
        raise SystemExit("[FAIL] source summary must describe diamond size C")
    if int(required_float(summary, "particle_count_scale")) != 2:
        raise SystemExit("[FAIL] source summary must use particle_count_scale=2")
    if not math.isfinite(target_velocity_cm_s):
        raise SystemExit("[FAIL] target velocity must be finite")
    if not 5.0 <= target_velocity_cm_s < BASELINE_VELOCITY_CM_S:
        raise SystemExit("[FAIL] target velocity must be in [5, 50) cm/s")

    groups = summary.get("groups")
    if not isinstance(groups, dict) or not isinstance(groups.get("settle1"), dict):
        raise SystemExit("[FAIL] source summary has no settle1 baseline metrics")
    baseline = groups["settle1"]
    baseline_mean = nested_float(baseline, "p95_mean_mpa")
    baseline_cv = nested_float(baseline, "p95_cv")
    baseline_both = int(nested_float(baseline, "pass_and_window_count"))
    if not 572.0 <= baseline_mean <= 638.0:
        raise SystemExit("[FAIL] settle1 baseline mean must be in the Zhang pressure window")

    emax = required_float(summary, "e_al_emax_gpa")
    mu = required_float(summary, "mu_scale")
    inputs = {
        **BASE_DEM_INPUTS,
        "runtime_profile": "demo",
        "demo_settle_scale": "1",
        "demo_top_velocity_cm_s": format_value(target_velocity_cm_s),
        "allow_evidence_mismatch": "true",
        "e_al_emax_sweep_json": json.dumps([format_value(emax)]),
        "mu_scale_json": json.dumps([format_value(mu)]),
        "dem_seed_json": json.dumps(seeds),
        "diamond_size_case_json": json.dumps(["C"]),
        "particle_count_scale_json": json.dumps(["2"]),
    }
    payload = {
        "ref": ref,
        "inputs": inputs,
        "metadata": {
            "diamond_size_case": "C",
            "particle_count_scale": 2,
            "source_run_id": str(summary.get("baseline_run_id", "")),
            "source_decision": str(summary.get("decision", "")),
            "e_al_emax_gpa": round(emax, 6),
            "mu_scale": round(mu, 6),
            "baseline_velocity_cm_s": BASELINE_VELOCITY_CM_S,
            "target_velocity_cm_s": target_velocity_cm_s,
            "velocity_ratio": target_velocity_cm_s / BASELINE_VELOCITY_CM_S,
            "settle_scale": 1,
            "settle_steps": BASELINE_SETTLE_STEPS,
            "baseline_p95_mean_mpa": round(baseline_mean, 6),
            "baseline_p95_cv": round(baseline_cv, 9),
            "baseline_pass_and_window_count": baseline_both,
            "seed_candidates": seeds,
            "estimated_run_count": len(seeds),
            "purpose": "c_loading_rate_seed_recheck",
            "changed_variable": "demo_top_velocity_cm_s",
            "held_variables": [
                "diamond_size_case",
                "particle_count_scale",
                "e_al_emax_gpa",
                "mu_scale",
                "demo_settle_scale",
                "time_step_seconds",
                "dem_seed_set",
            ],
            "hypothesis": (
                "Halving punch velocity reduces dynamic contact-network rearrangement "
                "and seed-to-seed P95 variance while preserving endpoint pressure."
            ),
        },
    }
    return [payload], len(seeds)


def nested_float(data: dict[str, object], field: str) -> float:
    if field not in data:
        raise SystemExit(f"[FAIL] settle1 baseline is missing {field}")
    try:
        value = float(data[field])
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"[FAIL] settle1 {field} is not numeric") from exc
    if not math.isfinite(value):
        raise SystemExit(f"[FAIL] settle1 {field} is not finite")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY))
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--ref", default=os.environ.get("GITHUB_REF_NAME", ""))
    parser.add_argument("--seed-json", default=json.dumps(DEFAULT_SEEDS))
    parser.add_argument(
        "--target-velocity-cm-s",
        type=float,
        default=DEFAULT_TARGET_VELOCITY_CM_S,
    )
    parser.add_argument("--max-total-runs", type=int, default=5)
    parser.add_argument("--sleep-seconds", type=float, default=2.0)
    parser.add_argument("--output", default="")
    parser.add_argument("--dispatch", action="store_true")
    args = parser.parse_args()

    summary_path = Path(args.summary)
    ref = args.ref or "codex/paper-reproduction-demo"
    payloads, total_runs = build_c_loading_rate_payload(
        read_summary(summary_path),
        ref=ref,
        seeds=parse_seed_json(args.seed_json),
        target_velocity_cm_s=args.target_velocity_cm_s,
    )
    if total_runs > args.max_total_runs:
        raise SystemExit(
            f"[FAIL] plan expands to {total_runs} DEM runs, above max {args.max_total_runs}"
        )

    result: dict[str, object] = {
        "summary": str(summary_path),
        "mode": "zhang_pscale2_c_loading_rate_recheck",
        "ref": ref,
        "workflow": DEM_WORKFLOW,
        "dispatch": bool(args.dispatch),
        "payload_count": len(payloads),
        "total_estimated_run_count": total_runs,
        "payloads": payloads,
    }
    if args.dispatch:
        if not args.repo:
            raise SystemExit("[FAIL] --repo or GITHUB_REPOSITORY is required for dispatch")
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token:
            raise SystemExit("[FAIL] GH_TOKEN or GITHUB_TOKEN is required for dispatch")
        result["dispatch_results"] = dispatch_payloads(
            repo=args.repo,
            token=token,
            payloads=payloads,
            sleep_seconds=args.sleep_seconds,
        )

    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
