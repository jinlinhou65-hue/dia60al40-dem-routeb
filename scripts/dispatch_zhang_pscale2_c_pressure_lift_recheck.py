"""Dispatch a one-variable pressure-lift seed recheck for Zhang size C."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path

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
    / "pscale2_c_seed_recheck_summary.json"
)
DEFAULT_SEEDS = ["0", "1", "2", "3", "4"]
DEFAULT_TARGET_PRESSURE_MPA = 600.0
DEFAULT_MAX_LIFT_RATIO = 1.30


def build_c_pressure_lift_payload(
    summary: dict[str, object],
    *,
    ref: str,
    seeds: list[str],
    target_pressure_mpa: float,
    max_lift_ratio: float,
) -> tuple[list[dict[str, object]], int]:
    if not seeds:
        raise SystemExit("[FAIL] at least one seed is required")
    if len(set(seeds)) != len(seeds):
        raise SystemExit("[FAIL] seeds must be unique")
    if summary.get("decision") != "c_candidate_not_seed_robust":
        raise SystemExit(
            "[FAIL] source summary is not marked c_candidate_not_seed_robust: "
            f"{summary.get('decision')!r}"
        )
    if summary.get("diamond_size_case") != "C":
        raise SystemExit("[FAIL] source summary must describe diamond size C")
    if int(required_float(summary, "particle_count_scale")) != 2:
        raise SystemExit("[FAIL] source summary must use particle_count_scale=2")

    pressure_window = summary.get("pressure_window_mpa")
    if not isinstance(pressure_window, list) or len(pressure_window) != 2:
        raise SystemExit("[FAIL] source summary has no two-value pressure window")
    pressure_low = finite_float(pressure_window[0], "pressure_window_mpa[0]")
    pressure_high = finite_float(pressure_window[1], "pressure_window_mpa[1]")
    if not pressure_low < target_pressure_mpa < pressure_high:
        raise SystemExit("[FAIL] target pressure must be inside the source pressure window")

    source_emax = required_float(summary, "e_al_emax_gpa")
    source_mu = required_float(summary, "mu_scale")
    source_mean_p95 = required_float(summary, "p95_mean_mpa")
    if source_emax <= 0 or source_mu <= 0 or source_mean_p95 <= 0:
        raise SystemExit("[FAIL] source Emax, mu, and mean P95 must be positive")
    if source_mean_p95 >= pressure_low:
        raise SystemExit("[FAIL] source mean P95 is not below the Zhang pressure window")
    if not 1.0 < max_lift_ratio <= 1.5:
        raise SystemExit("[FAIL] max lift ratio must be in (1.0, 1.5]")

    requested_ratio = target_pressure_mpa / source_mean_p95
    applied_ratio = min(requested_ratio, max_lift_ratio)
    target_emax = round(source_emax * applied_ratio, 3)
    if target_emax <= source_emax:
        raise SystemExit("[FAIL] derived Emax does not increase the source Emax")

    inputs = {
        **BASE_DEM_INPUTS,
        "runtime_profile": "demo",
        "allow_evidence_mismatch": "true",
        "e_al_emax_sweep_json": json.dumps([format_value(target_emax)]),
        "mu_scale_json": json.dumps([format_value(source_mu)]),
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
            "source_e_al_emax_gpa": round(source_emax, 6),
            "source_mu_scale": round(source_mu, 6),
            "source_p95_mean_mpa": round(source_mean_p95, 6),
            "target_pressure_mpa": round(target_pressure_mpa, 6),
            "requested_lift_ratio": round(requested_ratio, 9),
            "applied_lift_ratio": round(applied_ratio, 9),
            "target_e_al_emax_gpa": target_emax,
            "seed_candidates": seeds,
            "estimated_run_count": len(seeds),
            "purpose": "c_pressure_lift_seed_recheck",
            "changed_variable": "e_al_emax_gpa",
            "held_variables": [
                "diamond_size_case",
                "particle_count_scale",
                "mu_scale",
                "dem_seed_set",
                "runtime_profile",
            ],
            "scaling_hypothesis": (
                "Use a first-order P95-to-Emax proportional lift to target 600 MPa; "
                "the DEM run tests this hypothesis rather than assuming it is valid."
            ),
        },
    }
    return [payload], len(seeds)


def read_summary(path: Path) -> dict[str, object]:
    if not path.exists():
        raise SystemExit(f"[FAIL] summary JSON does not exist: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"[FAIL] summary JSON must contain an object: {path}")
    return data


def parse_seed_json(value: str) -> list[str]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"[FAIL] seed-json is invalid JSON: {exc}") from exc
    if not isinstance(parsed, list) or not parsed:
        raise SystemExit("[FAIL] seed-json must be a non-empty JSON list")
    seeds = [str(item) for item in parsed]
    if any(not seed.strip() for seed in seeds):
        raise SystemExit("[FAIL] seed-json values must not be empty")
    return seeds


def required_float(data: dict[str, object], field: str) -> float:
    if field not in data:
        raise SystemExit(f"[FAIL] source summary is missing {field}")
    return finite_float(data[field], field)


def finite_float(value: object, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"[FAIL] {field} is not numeric: {value!r}") from exc
    if not math.isfinite(number):
        raise SystemExit(f"[FAIL] {field} is not finite: {value!r}")
    return number


def format_value(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY))
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--ref", default=os.environ.get("GITHUB_REF_NAME", ""))
    parser.add_argument("--seed-json", default=json.dumps(DEFAULT_SEEDS))
    parser.add_argument("--target-pressure-mpa", type=float, default=DEFAULT_TARGET_PRESSURE_MPA)
    parser.add_argument("--max-lift-ratio", type=float, default=DEFAULT_MAX_LIFT_RATIO)
    parser.add_argument("--max-total-runs", type=int, default=5)
    parser.add_argument("--sleep-seconds", type=float, default=2.0)
    parser.add_argument("--output", default="")
    parser.add_argument("--dispatch", action="store_true")
    args = parser.parse_args()

    summary_path = Path(args.summary)
    ref = args.ref or "codex/paper-reproduction-demo"
    payloads, total_runs = build_c_pressure_lift_payload(
        read_summary(summary_path),
        ref=ref,
        seeds=parse_seed_json(args.seed_json),
        target_pressure_mpa=args.target_pressure_mpa,
        max_lift_ratio=args.max_lift_ratio,
    )
    if total_runs > args.max_total_runs:
        raise SystemExit(f"[FAIL] plan expands to {total_runs} DEM runs, above max {args.max_total_runs}")

    result: dict[str, object] = {
        "summary": str(summary_path),
        "mode": "zhang_pscale2_c_pressure_lift_recheck",
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
