from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from analyze_comsol_mesh_convergence import parse_comsol_log


SOURCE_FILES = (
    "README.md",
    "report.md",
    "model_spec.md",
    "data/source/dem_fem_handoff_stage5_rho095.csv",
    "data/source/stage5_rho095_direct_contacts.csv",
    "data/source/electrothermal_parameter_set.json",
    "data/source/loading_mode_parameter_set.json",
    "loading_mode_preregistration.md",
    "fvm_refinement_preregistration.md",
)

IMPLEMENTATION_FILES = (
    ".github/workflows/electrothermal-mvp-verification.yml",
    "comsol/Dia60Al40_ElectrothermalMVP.java",
    "scripts/electrothermal_contact_model.py",
    "scripts/solve_electrothermal_fvm.py",
    "scripts/run_electrothermal_loading_sensitivity.py",
    "scripts/analyze_electrothermal_loading_comsol.py",
    "scripts/analyze_electrothermal_fvm_refinement.py",
    "scripts/run_comsol_electrothermal_mvp.ps1",
    "scripts/run_comsol_electrothermal_loading_sensitivity.ps1",
    "scripts/build_electrothermal_loading_manifest.py",
    "tests/test_comsol_electrothermal_mvp.py",
    "tests/test_electrothermal_loading_sensitivity.py",
    "tests/test_electrothermal_loading_comsol.py",
    "tests/test_electrothermal_fvm_refinement.py",
    "tests/test_electrothermal_loading_manifest.py",
)

EXPECTED_REVIEW_CASES = (
    "fixed_current_multiplier_1",
    "fixed_voltage_multiplier_1",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _record(path: Path, repo_root: Path, role: str) -> dict[str, Any]:
    resolved = path.resolve()
    relative = resolved.relative_to(repo_root.resolve())
    return {
        "path": relative.as_posix(),
        "role": role,
        "bytes": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def _git(repo_root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=repo_root, text=True, encoding="utf-8"
    ).strip()


def decision_snapshot(stage_dir: Path) -> dict[str, Any]:
    evidence = stage_dir / "evidence" / "loading_mode_sensitivity"
    fvm = _read_json(evidence / "loading_mode_summary.json")
    comparison = _read_json(evidence / "comparison" / "loading_mode_comparison.json")
    refinement = _read_json(
        evidence
        / "fvm_refinement"
        / "multiplier_1"
        / "comparison"
        / "fvm_refinement_summary.json"
    )
    failed_case_ids = sorted(
        str(row["case_id"]) for row in comparison["rows"] if not bool(row["case_gate"])
    )
    return {
        "open_six_case_decision": fvm["decision"],
        "archived_comsol_comparison_decision": comparison["decision"],
        "archived_comsol_failed_case_ids": failed_case_ids,
        "archived_comsol_global_gates": comparison["gates"],
        "refinement_decision": refinement["decision"],
        "refinement_original_loading_decision": refinement["original_loading_decision"],
        "refinement_gates": refinement["gates"],
    }


def validate_decision_snapshot(snapshot: dict[str, Any]) -> None:
    if snapshot["open_six_case_decision"] != "loading_mode_fvm_pass":
        raise ValueError("open six-case loading decision must pass")
    if snapshot["archived_comsol_comparison_decision"] != "review":
        raise ValueError("archived six-case COMSOL comparison must preserve review")
    if tuple(snapshot["archived_comsol_failed_case_ids"]) != EXPECTED_REVIEW_CASES:
        raise ValueError("only the two multiplier-1 loading cases may fail the original gate")
    global_gates = snapshot["archived_comsol_global_gates"]
    if global_gates.get("all_case_gates") is not False:
        raise ValueError("original all-case gate must remain false")
    if not all(value for key, value in global_gates.items() if key != "all_case_gates"):
        raise ValueError("all non-case loading-mode gates must pass")
    if snapshot["refinement_decision"] != "fvm_refinement_pass":
        raise ValueError("preregistered FVM refinement must pass")
    if snapshot["refinement_original_loading_decision"] != "review":
        raise ValueError("refinement must preserve the original review decision")
    if not all(snapshot["refinement_gates"].values()):
        raise ValueError("every preregistered refinement gate must pass")


def _collect_records(
    repo_root: Path,
    stage_dir: Path,
    output_path: Path,
) -> list[dict[str, Any]]:
    selected: dict[Path, str] = {}
    for relative in SOURCE_FILES:
        path = stage_dir / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        selected[path.resolve()] = "source_or_preregistration"
    for relative in IMPLEMENTATION_FILES:
        path = repo_root / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        selected[path.resolve()] = "implementation"
    for root, role in (
        (stage_dir / "data" / "prepared" / "loading_mode_sensitivity", "prepared_input"),
        (stage_dir / "evidence" / "loading_mode_sensitivity", "solver_or_analysis_evidence"),
    ):
        if not root.is_dir():
            raise FileNotFoundError(root)
        for path in root.rglob("*"):
            if path.is_file() and path.resolve() != output_path.resolve():
                selected[path.resolve()] = role
    return [_record(path, repo_root, selected[path]) for path in sorted(selected)]


def _structural_counts(stage_dir: Path) -> dict[str, int]:
    evidence = stage_dir / "evidence" / "loading_mode_sensitivity"
    prepared = stage_dir / "data" / "prepared" / "loading_mode_sensitivity"
    counts = {
        "accepted_comsol_summaries": len(list(evidence.glob("comsol/*/multiplier_*/comsol_summary.json"))),
        "accepted_comsol_logs": len(list(evidence.glob("comsol/*/multiplier_*/comsol_batch.log"))),
        "accepted_comsol_models": len(
            list(evidence.glob("comsol/*/multiplier_*/Dia60Al40_ElectrothermalMVP.mph"))
        ),
        "open_six_case_summaries": len(list(evidence.glob("fvm/*/multiplier_*/fvm_summary.json"))),
        "refined_open_summaries": len(
            list(evidence.glob("fvm_refinement/multiplier_1/factor_*/fvm_summary.json"))
        ),
        "scenario_property_grids": len(list(prepared.glob("multiplier_*/stage5_contact_property_grid.csv"))),
        "scenario_comsol_interpolations": len(
            list(prepared.glob("multiplier_*/stage5_comsol_interpolation.txt"))
        ),
        "refined_property_grids": len(
            list(prepared.glob("fvm_refinement/multiplier_1/factor_*/stage5_contact_property_grid.csv"))
        ),
        "preserved_failure_logs": len(list(evidence.glob("failures/*/comsol_batch.log"))),
    }
    expected = {
        "accepted_comsol_summaries": 6,
        "accepted_comsol_logs": 6,
        "accepted_comsol_models": 6,
        "open_six_case_summaries": 6,
        "refined_open_summaries": 3,
        "scenario_property_grids": 3,
        "scenario_comsol_interpolations": 3,
        "refined_property_grids": 3,
        "preserved_failure_logs": 1,
    }
    if counts != expected:
        raise ValueError(f"loading evidence structure mismatch: expected {expected}, got {counts}")
    for summary_path in evidence.glob("comsol/*/multiplier_*/comsol_summary.json"):
        summary = _read_json(summary_path)
        log_path = summary_path.with_name("comsol_batch.log")
        log = parse_comsol_log(log_path.read_text(encoding="utf-8", errors="replace"))
        if summary.get("solver") != "COMSOL 6.4" or summary.get("solve_status") != "success":
            raise ValueError(f"invalid COMSOL summary: {summary_path}")
        if int(log["element_count"]) != 3316 or bool(log["log_error"]):
            raise ValueError(f"invalid fixed-mesh COMSOL log: {log_path}")
    return counts


def build_manifest(
    repo_root: Path,
    stage_dir: Path,
    output_path: Path,
    *,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    stage_dir = stage_dir.resolve()
    stage_dir.relative_to(repo_root)
    snapshot = decision_snapshot(stage_dir)
    validate_decision_snapshot(snapshot)
    counts = _structural_counts(stage_dir)
    records = _collect_records(repo_root, stage_dir, output_path)
    status = _git(repo_root, "status", "--porcelain", "--untracked-files=no")
    manifest = {
        "schema_version": 1,
        "generated_at_utc": generated_at_utc or datetime.now(timezone.utc).isoformat(),
        "stage": stage_dir.relative_to(repo_root).as_posix(),
        "source_commit_at_generation": _git(repo_root, "rev-parse", "HEAD"),
        "source_branch_at_generation": _git(repo_root, "branch", "--show-current"),
        "working_tree_clean_at_generation": not bool(status),
        "hashes_are_authoritative_for_uncommitted_sources": True,
        "solver_provenance": {
            "licensed_solver": "COMSOL 6.4",
            "open_solver": "structured_finite_volume_parallel_check",
            "comsol_mesh_elements": 3316,
            "comsol_cases": 6,
        },
        "decision_snapshot": snapshot,
        "structural_counts": counts,
        "record_count": len(records),
        "records": records,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return manifest


def verify_records(manifest: dict[str, Any], repo_root: Path) -> list[str]:
    errors: list[str] = []
    resolved_root = repo_root.resolve()
    for record in manifest["records"]:
        path = (resolved_root / str(record["path"])).resolve()
        try:
            path.relative_to(resolved_root)
        except ValueError:
            errors.append(f"path escapes repository: {record['path']}")
            continue
        if not path.is_file():
            errors.append(f"missing: {record['path']}")
            continue
        if path.stat().st_size != int(record["bytes"]):
            errors.append(f"size mismatch: {record['path']}")
        if sha256_file(path) != str(record["sha256"]):
            errors.append(f"sha256 mismatch: {record['path']}")
    return errors


def verify_manifest(manifest_path: Path, repo_root: Path) -> dict[str, Any]:
    manifest = _read_json(manifest_path)
    errors = verify_records(manifest, repo_root)
    stage_dir = repo_root / str(manifest["stage"])
    current_snapshot = decision_snapshot(stage_dir)
    try:
        validate_decision_snapshot(current_snapshot)
    except ValueError as exc:
        errors.append(str(exc))
    if current_snapshot != manifest["decision_snapshot"]:
        errors.append("decision snapshot differs from manifest")
    return {
        "decision": "manifest_pass" if not errors else "manifest_fail",
        "record_count": len(manifest["records"]),
        "errors": errors,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build or verify Stage 04 loading evidence manifest")
    parser.add_argument("stage_dir", nargs="?", type=Path)
    parser.add_argument("output", nargs="?", type=Path)
    parser.add_argument("--verify", type=Path)
    parser.add_argument("--verification-output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    if args.verify:
        result = verify_manifest(args.verify, repo_root)
        if args.verification_output:
            args.verification_output.parent.mkdir(parents=True, exist_ok=True)
            args.verification_output.write_text(
                json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
            )
        print(json.dumps(result, indent=2, ensure_ascii=True))
        if result["decision"] != "manifest_pass":
            raise SystemExit(1)
        return
    if args.stage_dir is None or args.output is None:
        raise SystemExit("stage_dir and output are required when not using --verify")
    result = build_manifest(repo_root, args.stage_dir, args.output)
    print(json.dumps({"decision": "manifest_built", "record_count": result["record_count"]}))


if __name__ == "__main__":
    main()
