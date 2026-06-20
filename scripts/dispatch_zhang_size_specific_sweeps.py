"""Dispatch Zhang size-specific DEM sweeps from a recommendation JSON file."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_RECOMMENDATION = (
    Path("docs")
    / "zhang_sweep_evidence"
    / "run_27867380830"
    / "zhang_next_sweep_recommendation.json"
)
DEM_WORKFLOW = "dia60al40-dem.yml"
BASE_DEM_INPUTS = {
    "e_al_e0_gpa": "5",
    "e_al_emax_gpa": "12",
    "e_diamond_gpa": "300",
    "e_tool_gpa": "600",
    "e_wall_gpa": "200",
    "mu_al_al": "0.30",
    "mu_al_diamond": "0.30",
    "mu_al_tool": "0.08",
    "mu_al_wall": "0.08",
    "mu_diamond_diamond": "0.10",
    "mu_diamond_tool": "0.08",
    "mu_diamond_wall": "0.08",
}


def build_dispatch_payloads(
    recommendation: dict[str, object],
    *,
    ref: str,
) -> tuple[list[dict[str, object]], int]:
    if recommendation.get("next_sweep_mode") != "size_specific_calibration":
        raise SystemExit("[FAIL] recommendation is not in size_specific_calibration mode")
    plan = recommendation.get("workflow_dispatch_plan")
    if not isinstance(plan, list) or not plan:
        raise SystemExit("[FAIL] recommendation has no workflow_dispatch_plan")

    payloads: list[dict[str, object]] = []
    total_runs = 0
    seen_sizes: set[str] = set()
    for item in plan:
        if not isinstance(item, dict):
            raise SystemExit("[FAIL] workflow_dispatch_plan entries must be objects")
        size = str(item.get("diamond_size_case") or "")
        if not size:
            raise SystemExit("[FAIL] size-specific plan entry has no diamond_size_case")
        if size in seen_sizes:
            raise SystemExit(f"[FAIL] duplicate size-specific plan entry for {size}")
        seen_sizes.add(size)
        inputs = item.get("workflow_dispatch_inputs")
        if not isinstance(inputs, dict):
            raise SystemExit(f"[FAIL] plan entry {size} has no workflow_dispatch_inputs")
        run_count = validate_inputs(size, inputs)
        expected = int(item.get("estimated_run_count") or 0)
        if expected != run_count:
            raise SystemExit(
                f"[FAIL] plan entry {size} estimated_run_count={expected} "
                f"but inputs expand to {run_count}"
            )
        total_runs += run_count
        payloads.append(
            {
                "ref": ref,
                "inputs": {
                    **BASE_DEM_INPUTS,
                    **{str(key): str(value) for key, value in inputs.items()},
                },
                "metadata": {
                    "diamond_size_case": size,
                    "estimated_run_count": run_count,
                    "pressure_action": item.get("pressure_action"),
                    "trend_action": item.get("trend_action"),
                },
            }
        )
    return payloads, total_runs


def validate_inputs(size: str, inputs: dict[str, object]) -> int:
    required = [
        "runtime_profile",
        "allow_evidence_mismatch",
        "mu_scale_json",
        "e_al_emax_sweep_json",
        "dem_seed_json",
        "diamond_size_case_json",
    ]
    missing = [key for key in required if key not in inputs]
    if missing:
        raise SystemExit(f"[FAIL] plan entry {size} missing inputs: {', '.join(missing)}")
    if inputs["runtime_profile"] != "demo":
        raise SystemExit(f"[FAIL] plan entry {size} must use runtime_profile=demo")
    if inputs["allow_evidence_mismatch"] != "true":
        raise SystemExit(f"[FAIL] plan entry {size} must allow evidence mismatches")

    mu_values = json_list(inputs["mu_scale_json"], "mu_scale_json", size)
    e_values = json_list(inputs["e_al_emax_sweep_json"], "e_al_emax_sweep_json", size)
    seed_values = json_list(inputs["dem_seed_json"], "dem_seed_json", size)
    size_values = json_list(inputs["diamond_size_case_json"], "diamond_size_case_json", size)
    if size_values != [size]:
        raise SystemExit(
            f"[FAIL] plan entry {size} must dispatch only its own size case, got {size_values}"
        )
    return len(mu_values) * len(e_values) * len(seed_values) * len(size_values)


def json_list(value: object, field: str, size: str) -> list[object]:
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"[FAIL] plan entry {size} has invalid {field}: {exc}") from exc
    if not isinstance(parsed, list) or not parsed:
        raise SystemExit(f"[FAIL] plan entry {size} {field} must be a non-empty JSON list")
    return parsed


def dispatch_payloads(
    *,
    repo: str,
    token: str,
    payloads: list[dict[str, object]],
    sleep_seconds: float,
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{DEM_WORKFLOW}/dispatches"
    for index, payload in enumerate(payloads, start=1):
        body = json.dumps(
            {"ref": payload["ref"], "inputs": payload["inputs"]},
            sort_keys=True,
        ).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": "zhang-size-specific-sweep",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urllib.request.urlopen(request) as response:
                status = response.status
                response_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            response_body = exc.read().decode("utf-8", errors="replace")
            raise SystemExit(
                f"[FAIL] dispatch {index} returned HTTP {exc.code}: {response_body}"
            ) from exc
        if status != 204:
            raise SystemExit(
                f"[FAIL] dispatch {index} returned HTTP {status}: {response_body}"
            )
        results.append(
            {
                "index": index,
                "workflow": DEM_WORKFLOW,
                "metadata": payload["metadata"],
                "http_status": status,
            }
        )
        if sleep_seconds > 0 and index < len(payloads):
            time.sleep(sleep_seconds)
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--recommendation", default=str(DEFAULT_RECOMMENDATION))
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--ref", default=os.environ.get("GITHUB_REF_NAME", ""))
    parser.add_argument("--max-total-runs", type=int, default=36)
    parser.add_argument("--sleep-seconds", type=float, default=2.0)
    parser.add_argument("--dispatch", action="store_true")
    args = parser.parse_args()

    recommendation_path = Path(args.recommendation)
    recommendation = json.loads(recommendation_path.read_text(encoding="utf-8"))
    ref = args.ref or "codex/paper-reproduction-demo"
    payloads, total_runs = build_dispatch_payloads(recommendation, ref=ref)
    if total_runs > args.max_total_runs:
        raise SystemExit(
            f"[FAIL] plan expands to {total_runs} DEM runs, above max {args.max_total_runs}"
        )

    summary: dict[str, object] = {
        "recommendation": str(recommendation_path),
        "mode": recommendation.get("next_sweep_mode"),
        "status": recommendation.get("status"),
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
        summary["dispatch_results"] = dispatch_payloads(
            repo=args.repo,
            token=token,
            payloads=payloads,
            sleep_seconds=args.sleep_seconds,
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
