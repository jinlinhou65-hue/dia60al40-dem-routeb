"""Dispatch a five-seed Zhang C interparticle-friction sensitivity run."""

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
)
from dispatch_zhang_size_specific_sweeps import (
    BASE_DEM_INPUTS,
    DEM_WORKFLOW,
    dispatch_payloads,
)


STAGE = Path("docs") / "reproduction_goal" / "03_zhang_particle_scale"
DEFAULT_PLAN = STAGE / "data" / "pscale2_c_particle_friction_plan.json"
DEFAULT_PREVIOUS = STAGE / "data" / "pscale2_c_wall_friction_summary.json"
DEFAULT_SEEDS = ["0", "1", "2", "3", "4"]
PINNED_LIGGGHTS_COMMIT = "3d5c00f20519e6bb6eb6756f51f1ad36564e649d"


def build_c_particle_friction_payload(
    plan: dict[str, object],
    previous: dict[str, object],
    *,
    ref: str,
    seeds: list[str],
) -> tuple[list[dict[str, object]], int]:
    if plan.get("mode") != "zhang_pscale2_c_particle_friction_recheck":
        raise SystemExit("[FAIL] plan does not authorize the particle-friction recheck")
    if previous.get("decision") != plan.get("previous_decision"):
        raise SystemExit("[FAIL] prior sidewall-friction decision does not match the plan")
    if not seeds or len(set(seeds)) != len(seeds):
        raise SystemExit("[FAIL] seeds must be a non-empty unique list")

    controls = require_mapping(plan, "fixed_controls")
    baseline = require_mapping(plan, "baseline")
    test = require_mapping(plan, "test")
    if controls.get("liggghts_commit") != PINNED_LIGGGHTS_COMMIT:
        raise SystemExit("[FAIL] particle-friction plan does not use the pinned solver")
    if str(previous.get("run_id")) != str(baseline.get("run_id")):
        raise SystemExit("[FAIL] plan baseline does not match the verified prior run")
    if seeds != [str(seed) for seed in controls.get("seeds", [])]:
        raise SystemExit("[FAIL] dispatch seeds differ from the preregistered paired seeds")

    mu_scale = required_finite(controls, "mu_scale")
    target_mu = required_finite(test, "paper_sweep_point")
    input_mu = required_finite(test, "input_mu_before_global_scale")
    if not math.isclose(input_mu * mu_scale, target_mu, rel_tol=0.0, abs_tol=5.0e-10):
        raise SystemExit("[FAIL] particle input does not reproduce the registered effective mu_p")
    for field in (
        "effective_mu_al_al",
        "effective_mu_al_diamond",
        "effective_mu_diamond_diamond",
    ):
        if not math.isclose(required_finite(test, field), target_mu, abs_tol=1.0e-12):
            raise SystemExit(f"[FAIL] {field} differs from the paper sweep point")

    particle_input = format_precise(input_mu)
    inputs = {
        **BASE_DEM_INPUTS,
        "mu_al_al": particle_input,
        "mu_al_diamond": particle_input,
        "mu_diamond_diamond": particle_input,
        "runtime_profile": "demo",
        "demo_settle_scale": format_value(required_finite(controls, "demo_settle_scale")),
        "demo_top_velocity_cm_s": format_value(required_finite(controls, "top_velocity_cm_s")),
        "allow_evidence_mismatch": "true",
        "e_al_emax_sweep_json": json.dumps(
            [format_value(required_finite(controls, "e_al_emax_gpa"))]
        ),
        "mu_scale_json": json.dumps([format_value(mu_scale)]),
        "mu_wall_scale_json": json.dumps(
            [format_value(required_finite(controls, "mu_wall_scale"))]
        ),
        "dem_seed_json": json.dumps(seeds),
        "diamond_size_case_json": json.dumps([str(controls["diamond_size_case"])]),
        "particle_count_scale_json": json.dumps(
            [format_value(required_finite(controls, "particle_count_scale"))]
        ),
    }
    payload = {
        "ref": ref,
        "inputs": inputs,
        "metadata": {
            "purpose": "c_particle_friction_recheck_reusing_verified_baseline",
            "changed_variable": "interparticle_friction_coefficients",
            "baseline_run_id": str(baseline["run_id"]),
            "test_effective_mu_particle": target_mu,
            "liggghts_commit": PINNED_LIGGGHTS_COMMIT,
            "seed_candidates": seeds,
            "estimated_run_count": len(seeds),
            "held_variables": [
                "diamond_size_case",
                "particle_count_scale",
                "e_al_emax_gpa",
                "mu_scale",
                "particle_tool_friction",
                "particle_wall_friction",
                "coefficient_restitution",
                "demo_settle_scale",
                "demo_top_velocity_cm_s",
                "time_step_seconds",
                "dem_seed_set",
            ],
            "hypothesis": plan.get("hypothesis"),
        },
    }
    return [payload], len(seeds)


def require_mapping(data: dict[str, object], field: str) -> dict[str, object]:
    value = data.get(field)
    if not isinstance(value, dict):
        raise SystemExit(f"[FAIL] {field} must be an object")
    return value


def required_finite(data: dict[str, object], field: str) -> float:
    try:
        value = float(data[field])
    except (KeyError, TypeError, ValueError) as exc:
        raise SystemExit(f"[FAIL] {field} must be numeric") from exc
    if not math.isfinite(value):
        raise SystemExit(f"[FAIL] {field} must be finite")
    return value


def format_precise(value: float) -> str:
    return f"{value:.12g}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", default=str(DEFAULT_PLAN))
    parser.add_argument("--previous-summary", default=str(DEFAULT_PREVIOUS))
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--ref", default=os.environ.get("GITHUB_REF_NAME", ""))
    parser.add_argument("--seed-json", default=json.dumps(DEFAULT_SEEDS))
    parser.add_argument("--max-total-runs", type=int, default=5)
    parser.add_argument("--sleep-seconds", type=float, default=2.0)
    parser.add_argument("--output", default="")
    parser.add_argument("--dispatch", action="store_true")
    args = parser.parse_args()

    ref = args.ref or "codex/paper-reproduction-demo"
    payloads, total_runs = build_c_particle_friction_payload(
        read_summary(Path(args.plan)),
        read_summary(Path(args.previous_summary)),
        ref=ref,
        seeds=parse_seed_json(args.seed_json),
    )
    if total_runs > args.max_total_runs:
        raise SystemExit(
            f"[FAIL] plan expands to {total_runs} DEM runs, above max {args.max_total_runs}"
        )

    result: dict[str, object] = {
        "source_plan": args.plan,
        "source_previous_summary": args.previous_summary,
        "mode": "zhang_pscale2_c_particle_friction_recheck",
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
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
