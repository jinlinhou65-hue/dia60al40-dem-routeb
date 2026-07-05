"""Dispatch a paired Zhang size-C sidewall-friction sensitivity run."""

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


DEFAULT_AUDIT = (
    Path("docs")
    / "reproduction_goal"
    / "03_zhang_particle_scale"
    / "data"
    / "zhang_contact_parameter_audit.json"
)
DEFAULT_SEEDS = ["0", "1", "2", "3", "4"]
PINNED_LIGGGHTS_COMMIT = "3d5c00f20519e6bb6eb6756f51f1ad36564e649d"


def build_c_wall_friction_payload(
    audit: dict[str, object],
    *,
    ref: str,
    seeds: list[str],
) -> tuple[list[dict[str, object]], int]:
    if not seeds or len(set(seeds)) != len(seeds):
        raise SystemExit("[FAIL] seeds must be a non-empty unique list")
    decision = require_mapping(audit, "decision")
    if decision.get("next_variable") != "sidewall_friction_only":
        raise SystemExit("[FAIL] audit does not authorize a sidewall-only experiment")
    if require_mapping(audit, "liggghts_audit").get("audited_commit") != PINNED_LIGGGHTS_COMMIT:
        raise SystemExit("[FAIL] audit and workflow LIGGGHTS commits differ")

    controls = require_mapping(decision, "fixed_controls")
    baseline_mu_wall = required_finite(decision, "baseline_effective_mu_wall")
    test_mu_wall = required_finite(decision, "test_effective_mu_wall")
    test_wall_scale = required_finite(decision, "test_wall_scale")
    if not math.isclose(test_mu_wall, baseline_mu_wall * test_wall_scale, rel_tol=2.0e-5):
        raise SystemExit("[FAIL] test wall scale does not reproduce the registered effective mu_w")
    if not 0.0 < test_wall_scale < 1.0:
        raise SystemExit("[FAIL] test wall scale must reduce the baseline sidewall friction")

    emax = required_finite(controls, "e_al_emax_gpa")
    mu = required_finite(controls, "mu_scale")
    velocity = required_finite(controls, "top_velocity_cm_s")
    wall_scales = ["1", format_precise(test_wall_scale)]
    inputs = {
        **BASE_DEM_INPUTS,
        "runtime_profile": "demo",
        "demo_settle_scale": format_value(required_finite(controls, "settle_scale")),
        "demo_top_velocity_cm_s": format_value(velocity),
        "allow_evidence_mismatch": "true",
        "e_al_emax_sweep_json": json.dumps([format_value(emax)]),
        "mu_scale_json": json.dumps([format_value(mu)]),
        "mu_wall_scale_json": json.dumps(wall_scales),
        "dem_seed_json": json.dumps(seeds),
        "diamond_size_case_json": json.dumps([str(controls["diamond_size_case"])]),
        "particle_count_scale_json": json.dumps(
            [format_value(required_finite(controls, "particle_count_scale"))]
        ),
    }
    total_runs = len(wall_scales) * len(seeds)
    payload = {
        "ref": ref,
        "inputs": inputs,
        "metadata": {
            "purpose": "c_paired_sidewall_friction_recheck",
            "changed_variable": "mu_wall_scale",
            "baseline_mu_wall_scale": 1.0,
            "test_mu_wall_scale": test_wall_scale,
            "baseline_effective_mu_wall": baseline_mu_wall,
            "test_effective_mu_wall": test_mu_wall,
            "liggghts_commit": PINNED_LIGGGHTS_COMMIT,
            "seed_candidates": seeds,
            "estimated_run_count": total_runs,
            "held_variables": [
                "diamond_size_case",
                "particle_count_scale",
                "e_al_emax_gpa",
                "mu_scale",
                "particle_particle_friction",
                "particle_tool_friction",
                "coefficient_restitution",
                "demo_settle_scale",
                "demo_top_velocity_cm_s",
                "time_step_seconds",
                "dem_seed_set",
            ],
            "hypothesis": (
                "The paper-supported low sidewall friction point mu_w=0.001 reduces "
                "seed-to-seed pressure and force-network inhomogeneity without moving "
                "the mean endpoint pressure outside 572-638 MPa."
            ),
        },
    }
    return [payload], total_runs


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
    return f"{value:.9f}".rstrip("0").rstrip(".")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", default=str(DEFAULT_AUDIT))
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--ref", default=os.environ.get("GITHUB_REF_NAME", ""))
    parser.add_argument("--seed-json", default=json.dumps(DEFAULT_SEEDS))
    parser.add_argument("--max-total-runs", type=int, default=10)
    parser.add_argument("--sleep-seconds", type=float, default=2.0)
    parser.add_argument("--output", default="")
    parser.add_argument("--dispatch", action="store_true")
    args = parser.parse_args()

    audit_path = Path(args.audit)
    ref = args.ref or "codex/paper-reproduction-demo"
    payloads, total_runs = build_c_wall_friction_payload(
        read_summary(audit_path),
        ref=ref,
        seeds=parse_seed_json(args.seed_json),
    )
    if total_runs > args.max_total_runs:
        raise SystemExit(
            f"[FAIL] plan expands to {total_runs} DEM runs, above max {args.max_total_runs}"
        )

    result: dict[str, object] = {
        "source_audit": str(audit_path),
        "mode": "zhang_pscale2_c_wall_friction_recheck",
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
