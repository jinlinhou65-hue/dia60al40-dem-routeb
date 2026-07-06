"""Dispatch the preregistered five-seed Zhang size-E pressure-lift run."""

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
DEFAULT_PLAN = STAGE / "data" / "pscale2_e_pressure_lift_plan.json"
DEFAULT_SEEDS = ["0", "1", "2", "3", "4"]
PINNED_LIGGGHTS_COMMIT = "3d5c00f20519e6bb6eb6756f51f1ad36564e649d"


def build_e_pressure_lift_payload(
    plan: dict[str, object],
    *,
    ref: str,
    seeds: list[str],
) -> tuple[list[dict[str, object]], int]:
    if plan.get("mode") != "zhang_pscale2_e_pressure_lift_recheck":
        raise SystemExit("[FAIL] plan does not authorize the E pressure-lift recheck")
    if not seeds or len(set(seeds)) != len(seeds):
        raise SystemExit("[FAIL] seeds must be a non-empty unique list")

    source = require_mapping(plan, "source_candidate")
    scaling = require_mapping(plan, "scaling")
    controls = require_mapping(plan, "fixed_controls")
    if controls.get("liggghts_commit") != PINNED_LIGGGHTS_COMMIT:
        raise SystemExit("[FAIL] E plan does not use the pinned solver")
    if controls.get("diamond_size_case") != "E":
        raise SystemExit("[FAIL] E plan changed the size case")
    if seeds != [str(seed) for seed in controls.get("seeds", [])]:
        raise SystemExit("[FAIL] dispatch seeds differ from the preregistered seeds")

    source_emax = required_finite(source, "e_al_emax_gpa")
    source_p95 = required_finite(source, "p95_mpa")
    target_pressure = required_finite(scaling, "target_pressure_mpa")
    target_emax = required_finite(scaling, "target_emax_gpa")
    derived = source_emax * target_pressure / source_p95
    if not math.isclose(target_emax, round(derived, 3), abs_tol=5.0e-4):
        raise SystemExit("[FAIL] registered Emax does not match the scaling formula")
    if not source_emax < target_emax <= source_emax * 1.15:
        raise SystemExit("[FAIL] Emax lift must be positive and capped at 15 percent")

    mu = required_finite(controls, "mu_scale")
    inputs = {
        **BASE_DEM_INPUTS,
        "runtime_profile": "demo",
        "demo_settle_scale": format_value(
            required_finite(controls, "demo_settle_scale")
        ),
        "demo_top_velocity_cm_s": format_value(
            required_finite(controls, "top_velocity_cm_s")
        ),
        "allow_evidence_mismatch": "true",
        "e_al_emax_sweep_json": json.dumps([format_value(target_emax)]),
        "mu_scale_json": json.dumps([format_value(mu)]),
        "mu_wall_scale_json": json.dumps(
            [format_value(required_finite(controls, "mu_wall_scale"))]
        ),
        "dem_seed_json": json.dumps(seeds),
        "diamond_size_case_json": json.dumps(["E"]),
        "particle_count_scale_json": json.dumps(
            [format_value(required_finite(controls, "particle_count_scale"))]
        ),
    }
    payload = {
        "ref": ref,
        "inputs": inputs,
        "metadata": {
            "purpose": "e_pressure_lift_five_seed_recheck",
            "changed_variable": "e_al_emax_gpa",
            "source_run_id": str(source.get("run_id", "")),
            "source_seed_index": int(required_finite(source, "seed_index")),
            "source_e_al_emax_gpa": source_emax,
            "source_p95_mpa": source_p95,
            "target_pressure_mpa": target_pressure,
            "target_e_al_emax_gpa": target_emax,
            "mu_scale": mu,
            "liggghts_commit": PINNED_LIGGGHTS_COMMIT,
            "seed_candidates": seeds,
            "estimated_run_count": len(seeds),
            "held_variables": [
                "diamond_size_case",
                "particle_count_scale",
                "mu_scale",
                "mu_wall_scale",
                "contact_pair_friction",
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", default=str(DEFAULT_PLAN))
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--ref", default=os.environ.get("GITHUB_REF_NAME", ""))
    parser.add_argument("--seed-json", default=json.dumps(DEFAULT_SEEDS))
    parser.add_argument("--max-total-runs", type=int, default=5)
    parser.add_argument("--sleep-seconds", type=float, default=2.0)
    parser.add_argument("--output", default="")
    parser.add_argument("--dispatch", action="store_true")
    args = parser.parse_args()

    ref = args.ref or "codex/paper-reproduction-demo"
    payloads, total_runs = build_e_pressure_lift_payload(
        read_summary(Path(args.plan)),
        ref=ref,
        seeds=parse_seed_json(args.seed_json),
    )
    if total_runs > args.max_total_runs:
        raise SystemExit(
            f"[FAIL] plan expands to {total_runs} DEM runs, above max {args.max_total_runs}"
        )

    result: dict[str, object] = {
        "source_plan": args.plan,
        "mode": "zhang_pscale2_e_pressure_lift_recheck",
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
