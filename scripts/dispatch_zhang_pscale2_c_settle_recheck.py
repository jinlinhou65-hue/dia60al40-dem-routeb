"""Dispatch a one-variable settle-duration recheck for Zhang size C."""

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
    / "pscale2_c_pressure_lift_summary.json"
)
DEFAULT_SEEDS = ["0", "1", "2", "3", "4"]
BASELINE_SETTLE_STEPS = {
    "initial": 20_000,
    "stage": 20_000,
    "final": 50_000,
}
DEFAULT_SETTLE_SCALE = 4.0


def build_c_settle_recheck_payload(
    summary: dict[str, object],
    *,
    ref: str,
    seeds: list[str],
    settle_scale: float,
) -> tuple[list[dict[str, object]], int]:
    if not seeds:
        raise SystemExit("[FAIL] at least one seed is required")
    if len(set(seeds)) != len(seeds):
        raise SystemExit("[FAIL] seeds must be unique")
    if summary.get("decision") != "c_pressure_lift_improves_but_not_seed_robust":
        raise SystemExit(
            "[FAIL] source summary does not justify a settle recheck: "
            f"{summary.get('decision')!r}"
        )
    if summary.get("diamond_size_case") != "C":
        raise SystemExit("[FAIL] source summary must describe diamond size C")
    if int(required_float(summary, "particle_count_scale")) != 2:
        raise SystemExit("[FAIL] source summary must use particle_count_scale=2")
    if not math.isfinite(settle_scale) or not 1.0 < settle_scale <= 10.0:
        raise SystemExit("[FAIL] settle scale must be finite and in (1, 10]")

    seed_count = int(required_float(summary, "seed_count"))
    pass_window_count = int(required_float(summary, "pressure_lift_pass_and_window_count"))
    if pass_window_count >= seed_count:
        raise SystemExit("[FAIL] source candidate is already seed robust")
    pressure_mean = required_float(summary, "pressure_lift_p95_mean_mpa")
    if not 572.0 <= pressure_mean <= 638.0:
        raise SystemExit("[FAIL] source mean P95 must be inside the Zhang pressure window")

    emax = required_float(summary, "pressure_lift_e_al_emax_gpa")
    mu = required_float(summary, "mu_scale")
    target_steps = {
        name: max(1, round(value * settle_scale))
        for name, value in BASELINE_SETTLE_STEPS.items()
    }
    inputs = {
        **BASE_DEM_INPUTS,
        "runtime_profile": "demo",
        "demo_settle_scale": format_value(settle_scale),
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
            "source_run_id": str(summary.get("run_id", "")),
            "source_decision": str(summary.get("decision", "")),
            "e_al_emax_gpa": round(emax, 6),
            "mu_scale": round(mu, 6),
            "baseline_p95_mean_mpa": round(pressure_mean, 6),
            "baseline_pass_and_window_count": pass_window_count,
            "settle_scale": settle_scale,
            "baseline_settle_steps": BASELINE_SETTLE_STEPS,
            "target_settle_steps": target_steps,
            "seed_candidates": seeds,
            "estimated_run_count": len(seeds),
            "purpose": "c_settle_relaxation_seed_recheck",
            "changed_variable": "demo_settle_scale",
            "held_variables": [
                "diamond_size_case",
                "particle_count_scale",
                "e_al_emax_gpa",
                "mu_scale",
                "top_velocity_cm_s",
                "time_step_seconds",
                "dem_seed_set",
            ],
            "hypothesis": (
                "Longer dwell after each displacement stage allows contact relaxation "
                "and may reduce seed-to-seed pressure and force-chain variance."
            ),
        },
    }
    return [payload], len(seeds)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY))
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--ref", default=os.environ.get("GITHUB_REF_NAME", ""))
    parser.add_argument("--seed-json", default=json.dumps(DEFAULT_SEEDS))
    parser.add_argument("--settle-scale", type=float, default=DEFAULT_SETTLE_SCALE)
    parser.add_argument("--max-total-runs", type=int, default=5)
    parser.add_argument("--sleep-seconds", type=float, default=2.0)
    parser.add_argument("--output", default="")
    parser.add_argument("--dispatch", action="store_true")
    args = parser.parse_args()

    summary_path = Path(args.summary)
    ref = args.ref or "codex/paper-reproduction-demo"
    payloads, total_runs = build_c_settle_recheck_payload(
        read_summary(summary_path),
        ref=ref,
        seeds=parse_seed_json(args.seed_json),
        settle_scale=args.settle_scale,
    )
    if total_runs > args.max_total_runs:
        raise SystemExit(f"[FAIL] plan expands to {total_runs} DEM runs, above max {args.max_total_runs}")

    result: dict[str, object] = {
        "summary": str(summary_path),
        "mode": "zhang_pscale2_c_settle_recheck",
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
