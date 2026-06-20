"""Dispatch a narrow Zhang pscale=2 pressure recalibration sweep."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path

from dispatch_zhang_size_specific_sweeps import (
    BASE_DEM_INPUTS,
    DEM_WORKFLOW,
    dispatch_payloads,
)


DEFAULT_COMPARISON = (
    Path("docs")
    / "reproduction_goal"
    / "03_zhang_particle_scale"
    / "data"
    / "1x_vs_2x_comparison.csv"
)
DEFAULT_TARGET_MPA = 600.0
DEFAULT_E_MULTIPLIERS = [0.95, 1.0, 1.05]


def build_pscale2_recalibration_payloads(
    rows: list[dict[str, str]],
    *,
    ref: str,
    target_pressure_mpa: float,
    e_multipliers: list[float],
) -> tuple[list[dict[str, object]], int]:
    if target_pressure_mpa <= 0:
        raise SystemExit("[FAIL] target pressure must be positive")
    if not e_multipliers:
        raise SystemExit("[FAIL] at least one E multiplier is required")

    payloads: list[dict[str, object]] = []
    for row in sorted(rows, key=lambda item: str(item.get("diamond_size_case"))):
        size = required_text(row, "diamond_size_case")
        current_p95 = required_float(row, "refined_best_p95_mpa")
        current_emax = required_float(row, "refined_e_al_emax_gpa")
        mu = required_float(row, "refined_mu_scale")
        run_id = required_text(row, "refined_source_run_id")
        artifact = required_text(row, "refined_artifact")
        if current_p95 <= 0:
            raise SystemExit(f"[FAIL] size {size} has non-positive refined P95: {current_p95}")

        target_emax = current_emax * target_pressure_mpa / current_p95
        e_values = unique_formatted(
            target_emax * multiplier for multiplier in e_multipliers
        )
        inputs = {
            **BASE_DEM_INPUTS,
            "runtime_profile": "demo",
            "allow_evidence_mismatch": "true",
            "e_al_emax_sweep_json": json.dumps(e_values),
            "mu_scale_json": json.dumps([format_value(mu)]),
            "dem_seed_json": json.dumps(["2"]),
            "diamond_size_case_json": json.dumps([size]),
            "particle_count_scale_json": json.dumps(["2"]),
        }
        payloads.append(
            {
                "ref": ref,
                "inputs": inputs,
                "metadata": {
                    "diamond_size_case": size,
                    "particle_count_scale": 2,
                    "source_run_id": run_id,
                    "source_artifact": artifact,
                    "source_p95_mpa": round(current_p95, 6),
                    "source_e_al_emax_gpa": round(current_emax, 6),
                    "source_mu_scale": round(mu, 6),
                    "target_pressure_mpa": target_pressure_mpa,
                    "target_e_al_emax_gpa": round(target_emax, 6),
                    "e_al_emax_candidates": e_values,
                    "estimated_run_count": len(e_values),
                    "purpose": "pressure_first_pscale2_recalibration",
                },
            }
        )
    return payloads, sum(int(item["metadata"]["estimated_run_count"]) for item in payloads)


def read_comparison(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"[FAIL] comparison CSV does not exist: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit(f"[FAIL] comparison CSV is empty: {path}")
    return rows


def required_text(row: dict[str, str], field: str) -> str:
    value = str(row.get(field) or "").strip()
    if not value:
        raise SystemExit(f"[FAIL] row missing {field}: {row}")
    return value


def required_float(row: dict[str, str], field: str) -> float:
    value = row.get(field)
    try:
        return float(str(value))
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"[FAIL] row has invalid {field}: {value!r}") from exc


def unique_formatted(values) -> list[str]:
    output: list[str] = []
    for value in values:
        formatted = format_value(float(value))
        if formatted not in output:
            output.append(formatted)
    return output


def format_value(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def parse_multipliers(value: str) -> list[float]:
    parsed = json.loads(value)
    if not isinstance(parsed, list) or not parsed:
        raise SystemExit("[FAIL] e-multipliers-json must be a non-empty JSON list")
    multipliers = [float(item) for item in parsed]
    if any(item <= 0 for item in multipliers):
        raise SystemExit("[FAIL] E multipliers must be positive")
    return multipliers


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comparison", default=str(DEFAULT_COMPARISON))
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--ref", default=os.environ.get("GITHUB_REF_NAME", ""))
    parser.add_argument("--target-pressure-mpa", type=float, default=DEFAULT_TARGET_MPA)
    parser.add_argument("--e-multipliers-json", default=json.dumps(DEFAULT_E_MULTIPLIERS))
    parser.add_argument("--max-total-runs", type=int, default=9)
    parser.add_argument("--sleep-seconds", type=float, default=2.0)
    parser.add_argument("--dispatch", action="store_true")
    args = parser.parse_args()

    comparison_path = Path(args.comparison)
    rows = read_comparison(comparison_path)
    ref = args.ref or "codex/paper-reproduction-demo"
    payloads, total_runs = build_pscale2_recalibration_payloads(
        rows,
        ref=ref,
        target_pressure_mpa=args.target_pressure_mpa,
        e_multipliers=parse_multipliers(args.e_multipliers_json),
    )
    if total_runs > args.max_total_runs:
        raise SystemExit(f"[FAIL] plan expands to {total_runs} DEM runs, above max {args.max_total_runs}")

    result: dict[str, object] = {
        "comparison": str(comparison_path),
        "mode": "zhang_pscale2_pressure_recalibration",
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
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
