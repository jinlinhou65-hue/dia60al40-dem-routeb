"""Dispatch the targeted Zhang pscale=2 follow-up calibration sweep."""

from __future__ import annotations

import argparse
import csv
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
    / "pscale2_recalibration_size_summary.csv"
)
DEFAULT_TARGET_MPA = 600.0


def build_pscale2_followup_payloads(
    rows: list[dict[str, str]],
    *,
    ref: str,
    target_pressure_mpa: float,
) -> tuple[list[dict[str, object]], int]:
    if target_pressure_mpa <= 0:
        raise SystemExit("[FAIL] target pressure must be positive")

    payloads: list[dict[str, object]] = []
    for row in sorted(rows, key=lambda item: str(item.get("diamond_size_case"))):
        size = required_text(row, "diamond_size_case")
        best_emax = required_float(row, "best_e_al_emax_gpa")
        best_mu = required_float(row, "best_mu_scale")
        best_p95 = required_float(row, "best_p95_mpa")
        decision = required_text(row, "decision")
        status = required_text(row, "best_status")
        if best_emax <= 0 or best_mu <= 0 or best_p95 <= 0:
            raise SystemExit(f"[FAIL] size {size} has non-positive calibration values: {row}")

        branch = branch_for_size(
            size=size,
            best_emax=best_emax,
            best_mu=best_mu,
            best_p95=best_p95,
            target_pressure_mpa=target_pressure_mpa,
        )
        e_values = branch["e_al_emax_candidates"]
        mu_values = branch["mu_scale_candidates"]
        inputs = {
            **BASE_DEM_INPUTS,
            "runtime_profile": "demo",
            "allow_evidence_mismatch": "true",
            "e_al_emax_sweep_json": json.dumps(e_values),
            "mu_scale_json": json.dumps(mu_values),
            "dem_seed_json": json.dumps(["2"]),
            "diamond_size_case_json": json.dumps([size]),
            "particle_count_scale_json": json.dumps(["2"]),
        }
        run_count = len(e_values) * len(mu_values)
        payloads.append(
            {
                "ref": ref,
                "inputs": inputs,
                "metadata": {
                    "diamond_size_case": size,
                    "particle_count_scale": 2,
                    "source_decision": decision,
                    "source_status": status,
                    "source_best_e_al_emax_gpa": round(best_emax, 6),
                    "source_best_mu_scale": round(best_mu, 6),
                    "source_best_p95_mpa": round(best_p95, 6),
                    "target_pressure_mpa": target_pressure_mpa,
                    "purpose": branch["purpose"],
                    "rationale": branch["rationale"],
                    "e_al_emax_candidates": e_values,
                    "mu_scale_candidates": mu_values,
                    "estimated_run_count": run_count,
                },
            }
        )
    return payloads, sum(int(item["metadata"]["estimated_run_count"]) for item in payloads)


def branch_for_size(
    *,
    size: str,
    best_emax: float,
    best_mu: float,
    best_p95: float,
    target_pressure_mpa: float,
) -> dict[str, object]:
    if size == "C":
        return {
            "purpose": "c_pressure_edge_narrow_emax",
            "rationale": (
                "C already passes the Zhang trend gate and is only slightly below the "
                "572 MPa pressure lower bound; narrow around the observed local best because "
                "the prior wider Emax extension was non-monotonic."
            ),
            "e_al_emax_candidates": unique_formatted(
                best_emax + delta for delta in [-1.5, -0.5, 0.5, 1.5]
            ),
            "mu_scale_candidates": [format_value(best_mu)],
        }
    if size == "D":
        return {
            "purpose": "d_hold_pressure_tune_friction_participation",
            "rationale": (
                "D has a pressure-window candidate but negative force-chain participation "
                "delta; hold Emax and sweep higher friction multipliers to test the "
                "participation gate without losing the pressure anchor."
            ),
            "e_al_emax_candidates": [format_value(best_emax)],
            "mu_scale_candidates": unique_formatted(best_mu * multiplier for multiplier in [1.0, 1.10, 1.25]),
        }
    if size == "E":
        target_emax = best_emax * target_pressure_mpa / best_p95
        return {
            "purpose": "e_pressure_extension_emax",
            "rationale": (
                "E remains far below the pressure window; extend endpoint modulus around "
                "the proportional pressure target before tuning participation."
            ),
            "e_al_emax_candidates": unique_formatted(
                target_emax * multiplier for multiplier in [0.95, 1.0, 1.10]
            ),
            "mu_scale_candidates": [format_value(best_mu)],
        }
    raise SystemExit(f"[FAIL] unsupported Zhang size case for follow-up: {size}")


def read_summary(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"[FAIL] summary CSV does not exist: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit(f"[FAIL] summary CSV is empty: {path}")
    return rows


def required_text(row: dict[str, str], field: str) -> str:
    value = str(row.get(field) or "").strip()
    if not value:
        raise SystemExit(f"[FAIL] row missing {field}: {row}")
    return value


def required_float(row: dict[str, str], field: str) -> float:
    value = row.get(field)
    try:
        number = float(str(value))
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"[FAIL] row has invalid {field}: {value!r}") from exc
    if not math.isfinite(number):
        raise SystemExit(f"[FAIL] row has non-finite {field}: {value!r}")
    return number


def unique_formatted(values) -> list[str]:
    output: list[str] = []
    for value in values:
        formatted = format_value(float(value))
        if formatted not in output:
            output.append(formatted)
    return output


def format_value(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY))
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--ref", default=os.environ.get("GITHUB_REF_NAME", ""))
    parser.add_argument("--target-pressure-mpa", type=float, default=DEFAULT_TARGET_MPA)
    parser.add_argument("--max-total-runs", type=int, default=12)
    parser.add_argument("--sleep-seconds", type=float, default=2.0)
    parser.add_argument("--output", default="")
    parser.add_argument("--dispatch", action="store_true")
    args = parser.parse_args()

    summary_path = Path(args.summary)
    rows = read_summary(summary_path)
    ref = args.ref or "codex/paper-reproduction-demo"
    payloads, total_runs = build_pscale2_followup_payloads(
        rows,
        ref=ref,
        target_pressure_mpa=args.target_pressure_mpa,
    )
    if total_runs > args.max_total_runs:
        raise SystemExit(f"[FAIL] plan expands to {total_runs} DEM runs, above max {args.max_total_runs}")

    result: dict[str, object] = {
        "summary": str(summary_path),
        "mode": "zhang_pscale2_size_specific_followup",
        "ref": ref,
        "workflow": DEM_WORKFLOW,
        "dispatch": bool(args.dispatch),
        "target_pressure_mpa": args.target_pressure_mpa,
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
