"""Dispatch a Zhang pscale=2 seed robustness recheck for the C candidate."""

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
    / "pscale2_followup_size_summary.csv"
)
DEFAULT_SIZE = "C"
DEFAULT_SEEDS = ["0", "1", "2", "3", "4"]


def build_c_seed_recheck_payload(
    rows: list[dict[str, str]],
    *,
    ref: str,
    size_case: str,
    seeds: list[str],
) -> tuple[list[dict[str, object]], int]:
    if not seeds:
        raise SystemExit("[FAIL] at least one seed is required")
    row = find_size_row(rows, size_case)
    if str(row.get("decision")) != "candidate_ready_for_seed_recheck":
        raise SystemExit(
            f"[FAIL] size {size_case} is not marked candidate_ready_for_seed_recheck: {row}"
        )
    if str(row.get("best_status")) != "pass":
        raise SystemExit(f"[FAIL] size {size_case} best trend status is not pass: {row}")
    if str(row.get("best_pressure_in_window")).lower() != "true":
        raise SystemExit(f"[FAIL] size {size_case} best pressure is not in window: {row}")

    emax = required_float(row, "best_e_al_emax_gpa")
    mu = required_float(row, "best_mu_scale")
    p95 = required_float(row, "best_p95_mpa")
    if emax <= 0 or mu <= 0 or p95 <= 0:
        raise SystemExit(f"[FAIL] size {size_case} has non-positive candidate values: {row}")

    inputs = {
        **BASE_DEM_INPUTS,
        "runtime_profile": "demo",
        "allow_evidence_mismatch": "true",
        "e_al_emax_sweep_json": json.dumps([format_value(emax)]),
        "mu_scale_json": json.dumps([format_value(mu)]),
        "dem_seed_json": json.dumps([str(seed) for seed in seeds]),
        "diamond_size_case_json": json.dumps([size_case]),
        "particle_count_scale_json": json.dumps(["2"]),
    }
    payload = {
        "ref": ref,
        "inputs": inputs,
        "metadata": {
            "diamond_size_case": size_case,
            "particle_count_scale": 2,
            "source_decision": row.get("decision", ""),
            "source_best_e_al_emax_gpa": round(emax, 6),
            "source_best_mu_scale": round(mu, 6),
            "source_best_p95_mpa": round(p95, 6),
            "seed_candidates": [str(seed) for seed in seeds],
            "estimated_run_count": len(seeds),
            "purpose": "c_seed_robustness_recheck",
            "rationale": (
                "C has a pscale=2 candidate that satisfies both the Zhang pressure window "
                "and force-chain trend gates. Re-run only the random mixing seed to test "
                "whether the candidate survives stochastic particle placement."
            ),
        },
    }
    return [payload], len(seeds)


def find_size_row(rows: list[dict[str, str]], size_case: str) -> dict[str, str]:
    matches = [row for row in rows if str(row.get("diamond_size_case")) == size_case]
    if len(matches) != 1:
        raise SystemExit(f"[FAIL] expected exactly one summary row for {size_case}, got {len(matches)}")
    return matches[0]


def read_summary(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"[FAIL] summary CSV does not exist: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit(f"[FAIL] summary CSV is empty: {path}")
    return rows


def required_float(row: dict[str, str], field: str) -> float:
    value = row.get(field)
    try:
        number = float(str(value))
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"[FAIL] row has invalid {field}: {value!r}") from exc
    if not math.isfinite(number):
        raise SystemExit(f"[FAIL] row has non-finite {field}: {value!r}")
    return number


def parse_seed_json(value: str) -> list[str]:
    parsed = json.loads(value)
    if not isinstance(parsed, list) or not parsed:
        raise SystemExit("[FAIL] seed-json must be a non-empty JSON list")
    seeds = [str(item) for item in parsed]
    if len(set(seeds)) != len(seeds):
        raise SystemExit("[FAIL] seed-json must not contain duplicate seeds")
    return seeds


def format_value(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY))
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--ref", default=os.environ.get("GITHUB_REF_NAME", ""))
    parser.add_argument("--size-case", default=DEFAULT_SIZE)
    parser.add_argument("--seed-json", default=json.dumps(DEFAULT_SEEDS))
    parser.add_argument("--max-total-runs", type=int, default=5)
    parser.add_argument("--sleep-seconds", type=float, default=2.0)
    parser.add_argument("--output", default="")
    parser.add_argument("--dispatch", action="store_true")
    args = parser.parse_args()

    summary_path = Path(args.summary)
    rows = read_summary(summary_path)
    ref = args.ref or "codex/paper-reproduction-demo"
    payloads, total_runs = build_c_seed_recheck_payload(
        rows,
        ref=ref,
        size_case=args.size_case,
        seeds=parse_seed_json(args.seed_json),
    )
    if total_runs > args.max_total_runs:
        raise SystemExit(f"[FAIL] plan expands to {total_runs} DEM runs, above max {args.max_total_runs}")

    result: dict[str, object] = {
        "summary": str(summary_path),
        "mode": "zhang_pscale2_c_seed_recheck",
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
