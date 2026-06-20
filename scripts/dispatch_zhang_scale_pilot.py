"""Dispatch a small Zhang particle-count scale pilot from imported evidence."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

from dispatch_zhang_size_specific_sweeps import (
    BASE_DEM_INPUTS,
    DEM_WORKFLOW,
    dispatch_payloads,
)


DEFAULT_SUMMARY = (
    Path("docs")
    / "zhang_sweep_evidence"
    / "size_specific_27874059503_27874061902_27874064063"
    / "summary.json"
)


def build_scale_pilot_payloads(
    summary: dict[str, object],
    *,
    ref: str,
    particle_count_scale: int,
) -> tuple[list[dict[str, object]], int]:
    if particle_count_scale < 2:
        raise SystemExit("[FAIL] scale pilot must use particle_count_scale >= 2")
    rows = summary.get("size_summary")
    if not isinstance(rows, list) or not rows:
        raise SystemExit("[FAIL] summary has no size_summary rows")

    payloads: list[dict[str, object]] = []
    for row in sorted(rows, key=lambda item: str(item.get("diamond_size_case"))):
        if not isinstance(row, dict):
            raise SystemExit("[FAIL] size_summary row must be an object")
        size = str(row.get("diamond_size_case") or "")
        if not size:
            raise SystemExit("[FAIL] size_summary row has no diamond_size_case")
        if row.get("best_status") != "pass":
            raise SystemExit(f"[FAIL] size {size} best row is not pass")
        if int(row.get("passing_window_count") or 0) < 1:
            raise SystemExit(f"[FAIL] size {size} has no pass+pressure-window candidate")

        artifact = str(row.get("best_artifact") or "")
        seed = seed_from_artifact(artifact)
        emax = format_value(row.get("best_e_al_emax_gpa"))
        mu = format_value(row.get("best_mu_scale"))
        inputs = {
            **BASE_DEM_INPUTS,
            "runtime_profile": "demo",
            "allow_evidence_mismatch": "true",
            "e_al_emax_sweep_json": json.dumps([emax]),
            "mu_scale_json": json.dumps([mu]),
            "dem_seed_json": json.dumps([str(seed)]),
            "diamond_size_case_json": json.dumps([size]),
            "particle_count_scale_json": json.dumps([str(particle_count_scale)]),
        }
        payloads.append(
            {
                "ref": ref,
                "inputs": inputs,
                "metadata": {
                    "diamond_size_case": size,
                    "particle_count_scale": particle_count_scale,
                    "source_artifact": artifact,
                    "source_run_id": row.get("best_source_run_id"),
                    "source_p95_mpa": row.get("best_p95_mpa"),
                    "estimated_run_count": 1,
                },
            }
        )
    return payloads, len(payloads)


def seed_from_artifact(artifact: str) -> int:
    match = re.search(r"(?:^|-)seed(\d+)(?:$|-)", artifact)
    if not match:
        raise SystemExit(f"[FAIL] could not infer seed index from artifact: {artifact}")
    return int(match.group(1))


def format_value(value: object) -> str:
    number = float(value)  # Raises a useful exception for malformed imported evidence.
    return f"{number:.6g}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY))
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--ref", default=os.environ.get("GITHUB_REF_NAME", ""))
    parser.add_argument("--particle-count-scale", type=int, default=2)
    parser.add_argument("--max-total-runs", type=int, default=3)
    parser.add_argument("--sleep-seconds", type=float, default=2.0)
    parser.add_argument("--dispatch", action="store_true")
    args = parser.parse_args()

    summary_path = Path(args.summary)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    ref = args.ref or "codex/paper-reproduction-demo"
    payloads, total_runs = build_scale_pilot_payloads(
        summary,
        ref=ref,
        particle_count_scale=args.particle_count_scale,
    )
    if total_runs > args.max_total_runs:
        raise SystemExit(f"[FAIL] plan expands to {total_runs} DEM runs, above max {args.max_total_runs}")

    result: dict[str, object] = {
        "summary": str(summary_path),
        "mode": "zhang_particle_count_scale_pilot",
        "ref": ref,
        "workflow": DEM_WORKFLOW,
        "dispatch": bool(args.dispatch),
        "payload_count": len(payloads),
        "total_estimated_run_count": total_runs,
        "particle_count_scale": args.particle_count_scale,
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
