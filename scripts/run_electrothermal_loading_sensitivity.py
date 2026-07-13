from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

from electrothermal_contact_model import (
    build_contact_physics,
    gaussian_property_grid,
    load_parameter_set,
    read_contacts,
    read_particles,
    write_comsol_interpolation,
    write_csv,
)
from run_electrothermal_contact_sensitivity import hotspot_metrics
from solve_electrothermal_fvm import solve_fvm


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_loading_parameters(path: Path, base_parameter_path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("unsupported loading-mode parameter schema")
    expected_hash = str(data["base_parameter_set"]["sha256"])
    actual_hash = file_sha256(base_parameter_path)
    if actual_hash != expected_hash:
        raise ValueError(f"base parameter hash mismatch: expected {expected_hash}, got {actual_hash}")
    if data["loading_modes"] != ["fixed_voltage", "fixed_current"]:
        raise ValueError("loading modes must be fixed_voltage then fixed_current")
    return data


def fixed_current_voltage(
    target_current_a_per_m: float,
    base_current_a_per_m: float,
    base_voltage_v: float,
) -> float:
    if min(target_current_a_per_m, base_current_a_per_m, base_voltage_v) <= 0:
        raise ValueError("current and voltage values must be positive")
    return base_voltage_v * target_current_a_per_m / base_current_a_per_m


def _nondecreasing(values: list[float], *, tolerance: float = 1.0e-12) -> bool:
    return all(left <= right + tolerance for left, right in zip(values, values[1:]))


def _nonincreasing(values: list[float], *, tolerance: float = 1.0e-12) -> bool:
    return all(left + tolerance >= right for left, right in zip(values, values[1:]))


def evaluate_loading_gates(
    rows: list[dict[str, Any]],
    loading_parameters: dict[str, Any],
    target_current_a_per_m: float,
) -> dict[str, bool]:
    acceptance = loading_parameters["acceptance"]
    ordered: dict[str, list[dict[str, Any]]] = {}
    for mode in loading_parameters["loading_modes"]:
        ordered[mode] = sorted(
            (row for row in rows if row["loading_mode"] == mode),
            key=lambda row: float(row["al_al_resistance_multiplier"]),
        )
    voltage_power = [float(row["electric_power_w_per_m_depth"]) for row in ordered["fixed_voltage"]]
    voltage_rise = [float(row["temperature_rise_max_k"]) for row in ordered["fixed_voltage"]]
    current_power = [float(row["electric_power_w_per_m_depth"]) for row in ordered["fixed_current"]]
    current_rise = [float(row["temperature_rise_max_k"]) for row in ordered["fixed_current"]]
    current_errors = [
        abs(float(row["top_current_a_per_m_depth"]) - target_current_a_per_m)
        / target_current_a_per_m
        for row in ordered["fixed_current"]
    ]
    reference_multiplier = float(loading_parameters["reference_case"]["multiplier"])
    references = {
        row["loading_mode"]: row
        for row in rows
        if math.isclose(float(row["al_al_resistance_multiplier"]), reference_multiplier)
    }
    cross_mode_hotspots = []
    for multiplier in loading_parameters["contact_resistance_multipliers"]:
        pair = [
            row for row in rows if math.isclose(float(row["al_al_resistance_multiplier"]), float(multiplier))
        ]
        by_mode = {row["loading_mode"]: row for row in pair}
        for prefix in ("joule_hotspot", "temperature_hotspot"):
            dx = float(by_mode["fixed_voltage"][f"{prefix}_x_um"]) - float(
                by_mode["fixed_current"][f"{prefix}_x_um"]
            )
            dy = float(by_mode["fixed_voltage"][f"{prefix}_y_um"]) - float(
                by_mode["fixed_current"][f"{prefix}_y_um"]
            )
            cross_mode_hotspots.append(math.hypot(dx, dy))
    return {
        "fixed_voltage_power_trend_gate": _nonincreasing(voltage_power),
        "fixed_voltage_temperature_trend_gate": _nonincreasing(voltage_rise),
        "fixed_current_power_trend_gate": _nondecreasing(current_power),
        "fixed_current_temperature_trend_gate": _nondecreasing(current_rise),
        "fvm_power_balance_gate": all(
            float(row["electric_relative_balance_error"])
            <= float(acceptance["fvm_power_balance_relative_max"])
            for row in rows
        ),
        "fixed_current_target_gate": max(current_errors)
        <= float(acceptance["fixed_current_relative_error_max"]),
        "reference_case_identity_gate": math.isclose(
            float(references["fixed_voltage"]["electric_power_w_per_m_depth"]),
            float(references["fixed_current"]["electric_power_w_per_m_depth"]),
            rel_tol=1.0e-12,
        )
        and math.isclose(
            float(references["fixed_voltage"]["temperature_rise_max_k"]),
            float(references["fixed_current"]["temperature_rise_max_k"]),
            rel_tol=1.0e-12,
        ),
        "cross_mode_hotspot_gate": max(cross_mode_hotspots)
        <= float(acceptance["same_scenario_cross_mode_hotspot_distance_um_max"]),
    }


def _plot_loading_sensitivity(rows: list[dict[str, Any]], path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.8), constrained_layout=True)
    colors = {"fixed_voltage": "#006d77", "fixed_current": "#c44536"}
    labels = {"fixed_voltage": "Fixed voltage", "fixed_current": "Fixed current"}
    for mode in ("fixed_voltage", "fixed_current"):
        selected = sorted(
            (row for row in rows if row["loading_mode"] == mode),
            key=lambda row: float(row["al_al_resistance_multiplier"]),
        )
        x = [float(row["al_al_resistance_multiplier"]) for row in selected]
        axes[0].plot(
            x,
            [float(row["electric_power_w_per_m_depth"]) for row in selected],
            marker="o",
            color=colors[mode],
            label=labels[mode],
        )
        axes[1].plot(
            x,
            [float(row["temperature_rise_max_k"]) for row in selected],
            marker="o",
            color=colors[mode],
        )
        axes[2].plot(
            x,
            [float(row["applied_voltage_v"]) for row in selected],
            marker="o",
            color=colors[mode],
        )
    axes[0].set_ylabel("Joule power (W/m depth)")
    axes[1].set_ylabel("Maximum temperature rise (K)")
    axes[2].set_ylabel("Applied voltage (V)")
    for axis in axes:
        axis.set_xscale("log")
        axis.set_yscale("log")
        axis.set_xlabel("Al-Al resistance multiplier")
        axis.grid(True, alpha=0.25)
    axes[0].legend(frameon=False)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _case_id(mode: str, multiplier: float) -> str:
    return f"{mode}_multiplier_{multiplier:g}".replace(".", "p")


def portable_plan_path(path: Path, root: Path, external_prefix: str) -> str:
    try:
        relative = path.resolve().relative_to(root.resolve())
        return relative.as_posix()
    except ValueError:
        return f"{external_prefix}/{path.name}"


def run_loading_sensitivity(
    particle_csv: Path,
    contact_csv: Path,
    base_parameter_json: Path,
    loading_parameter_json: Path,
    prepared_dir: Path,
    evidence_dir: Path,
) -> dict[str, Any]:
    base = load_parameter_set(base_parameter_json)
    loading = load_loading_parameters(loading_parameter_json, base_parameter_json)
    particles, height_um = read_particles(particle_csv)
    contacts = read_contacts(contact_csv)
    base["domain_height_um"] = height_um
    reference_multiplier = float(loading["reference_case"]["multiplier"])
    reference_rows = build_contact_physics(
        particles, contacts, base, al_al_multiplier=reference_multiplier
    )
    multipliers = [float(value) for value in loading["contact_resistance_multipliers"]]
    scenario_grids: dict[float, Path] = {}
    for multiplier in multipliers:
        contacts_for_case = build_contact_physics(
            particles, contacts, base, al_al_multiplier=multiplier
        )
        grid = gaussian_property_grid(contacts_for_case, reference_rows, base)
        scenario_dir = prepared_dir / f"multiplier_{multiplier:g}".replace(".", "p")
        grid_path = scenario_dir / "stage5_contact_property_grid.csv"
        write_csv(grid_path, grid)
        write_comsol_interpolation(scenario_dir / "stage5_comsol_interpolation.txt", grid)
        scenario_grids[multiplier] = grid_path

    base_voltage = float(loading["reference_case"]["applied_voltage_v"])
    rows: list[dict[str, Any]] = []
    base_voltage_results: dict[float, dict[str, Any]] = {}
    for multiplier in multipliers:
        case_id = _case_id("fixed_voltage", multiplier)
        output = evidence_dir / "fvm" / "fixed_voltage" / f"multiplier_{multiplier:g}".replace(".", "p")
        summary = solve_fvm(scenario_grids[multiplier], output, applied_voltage=base_voltage)
        row = {
            "case_id": case_id,
            "loading_mode": "fixed_voltage",
            "al_al_resistance_multiplier": multiplier,
            **summary,
            **hotspot_metrics(output / "fvm_fields.csv"),
        }
        rows.append(row)
        base_voltage_results[multiplier] = row

    target_current = float(base_voltage_results[reference_multiplier]["top_current_a_per_m_depth"])
    for multiplier in multipliers:
        applied_voltage = fixed_current_voltage(
            target_current,
            float(base_voltage_results[multiplier]["top_current_a_per_m_depth"]),
            base_voltage,
        )
        case_id = _case_id("fixed_current", multiplier)
        output = evidence_dir / "fvm" / "fixed_current" / f"multiplier_{multiplier:g}".replace(".", "p")
        summary = solve_fvm(scenario_grids[multiplier], output, applied_voltage=applied_voltage)
        rows.append(
            {
                "case_id": case_id,
                "loading_mode": "fixed_current",
                "al_al_resistance_multiplier": multiplier,
                **summary,
                **hotspot_metrics(output / "fvm_fields.csv"),
            }
        )

    rows.sort(key=lambda row: (str(row["loading_mode"]), float(row["al_al_resistance_multiplier"])))
    gates = evaluate_loading_gates(rows, loading, target_current)
    decision = "loading_mode_fvm_pass" if all(gates.values()) else "review"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    write_csv(evidence_dir / "loading_mode_summary.csv", rows)
    _plot_loading_sensitivity(rows, evidence_dir / "loading_mode_sensitivity.png")

    stage_dir = base_parameter_json.parents[2]
    evidence_root = stage_dir / "evidence"
    run_cases = []
    for row in rows:
        multiplier = float(row["al_al_resistance_multiplier"])
        input_dir = scenario_grids[multiplier].parent
        evidence_subpath = (
            evidence_dir / "comsol" / str(row["loading_mode"])
            / f"multiplier_{multiplier:g}".replace(".", "p")
        )
        run_cases.append(
            {
                "case_id": row["case_id"],
                "loading_mode": row["loading_mode"],
                "al_al_resistance_multiplier": multiplier,
                "applied_voltage_v": float(row["applied_voltage_v"]),
                "input_subpath": portable_plan_path(
                    input_dir, stage_dir, "external_open_verifier_input"
                ),
                "evidence_subpath": portable_plan_path(
                    evidence_subpath, evidence_root, "external_open_verifier_evidence"
                ),
                "fvm_summary_path": portable_plan_path(
                    evidence_dir / "fvm" / str(row["loading_mode"])
                    / f"multiplier_{multiplier:g}".replace(".", "p") / "fvm_summary.json",
                    stage_dir,
                    "external_open_verifier_fvm",
                ),
            }
        )
    run_plan = {
        "fvm_decision_required": "loading_mode_fvm_pass",
        "fixed_mesh": loading["comsol_mesh"],
        "cases": run_cases,
    }
    (evidence_dir / "comsol_run_plan.json").write_text(
        json.dumps(run_plan, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    result = {
        "decision": decision,
        "model_fidelity": "conditional_homogenized_loading_mode_screen",
        "target_current_a_per_m_depth": target_current,
        "gates": gates,
        "rows": rows,
        "source_hashes": {
            "particles": file_sha256(particle_csv),
            "contacts": file_sha256(contact_csv),
            "base_parameters": file_sha256(base_parameter_json),
            "loading_parameters": file_sha256(loading_parameter_json),
        },
        "interpretation_boundary": (
            "Loading-mode trends are conditional on a regularized continuum field. "
            "The active two-dimensional particle network is not electrically percolating."
        ),
    }
    (evidence_dir / "loading_mode_summary.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run fixed-voltage and fixed-current FVM sensitivity")
    parser.add_argument("particle_csv", type=Path)
    parser.add_argument("contact_csv", type=Path)
    parser.add_argument("base_parameter_json", type=Path)
    parser.add_argument("loading_parameter_json", type=Path)
    parser.add_argument("prepared_dir", type=Path)
    parser.add_argument("evidence_dir", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_loading_sensitivity(
        args.particle_csv,
        args.contact_csv,
        args.base_parameter_json,
        args.loading_parameter_json,
        args.prepared_dir,
        args.evidence_dir,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
