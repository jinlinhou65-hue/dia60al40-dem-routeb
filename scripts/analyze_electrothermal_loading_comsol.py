from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

from analyze_comsol_mesh_convergence import parse_comsol_log, relative_difference
from analyze_electrothermal_mvp import read_comsol_fields
from electrothermal_contact_model import write_csv


def field_hotspots(path: Path) -> dict[str, float]:
    fields = read_comsol_fields(path)
    joule_index = int(fields["joule_w_m3"].argmax())
    temperature_index = int(fields["temperature_k"].argmax())
    return {
        "comsol_joule_hotspot_x_um": float(fields["x_um"][joule_index]),
        "comsol_joule_hotspot_y_um": float(fields["y_um"][joule_index]),
        "comsol_joule_hotspot_w_m3": float(fields["joule_w_m3"][joule_index]),
        "comsol_temperature_hotspot_x_um": float(fields["x_um"][temperature_index]),
        "comsol_temperature_hotspot_y_um": float(fields["y_um"][temperature_index]),
    }


def _trend(values: list[float], *, increasing: bool) -> bool:
    pairs = zip(values, values[1:])
    if increasing:
        return all(left <= right + 1.0e-12 for left, right in pairs)
    return all(left + 1.0e-12 >= right for left, right in pairs)


def evaluate_global_gates(
    rows: list[dict[str, Any]],
    expected_element_count: int,
    hotspot_distance_max_um: float,
) -> dict[str, bool]:
    by_mode = {
        mode: sorted(
            (row for row in rows if row["loading_mode"] == mode),
            key=lambda row: float(row["al_al_resistance_multiplier"]),
        )
        for mode in ("fixed_voltage", "fixed_current")
    }
    hotspot_distances = []
    for multiplier in sorted({float(row["al_al_resistance_multiplier"]) for row in rows}):
        pair = {
            row["loading_mode"]: row
            for row in rows
            if math.isclose(float(row["al_al_resistance_multiplier"]), multiplier)
        }
        for prefix in ("comsol_joule_hotspot", "comsol_temperature_hotspot"):
            dx = float(pair["fixed_voltage"][f"{prefix}_x_um"]) - float(
                pair["fixed_current"][f"{prefix}_x_um"]
            )
            dy = float(pair["fixed_voltage"][f"{prefix}_y_um"]) - float(
                pair["fixed_current"][f"{prefix}_y_um"]
            )
            hotspot_distances.append(math.hypot(dx, dy))
    return {
        "all_case_gates": all(bool(row["case_gate"]) for row in rows),
        "fixed_mesh_element_gate": all(
            int(row["element_count"]) == expected_element_count for row in rows
        ),
        "fixed_voltage_power_trend_gate": _trend(
            [float(row["comsol_power_w_per_m_depth"]) for row in by_mode["fixed_voltage"]],
            increasing=False,
        ),
        "fixed_voltage_temperature_trend_gate": _trend(
            [float(row["comsol_temperature_rise_k"]) for row in by_mode["fixed_voltage"]],
            increasing=False,
        ),
        "fixed_current_power_trend_gate": _trend(
            [float(row["comsol_power_w_per_m_depth"]) for row in by_mode["fixed_current"]],
            increasing=True,
        ),
        "fixed_current_temperature_trend_gate": _trend(
            [float(row["comsol_temperature_rise_k"]) for row in by_mode["fixed_current"]],
            increasing=True,
        ),
        "cross_mode_hotspot_gate": max(hotspot_distances) <= hotspot_distance_max_um,
    }


def _plot(rows: list[dict[str, Any]], path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.9), constrained_layout=True)
    colors = {"fixed_voltage": "#006d77", "fixed_current": "#c44536"}
    for mode in ("fixed_voltage", "fixed_current"):
        selected = sorted(
            (row for row in rows if row["loading_mode"] == mode),
            key=lambda row: float(row["al_al_resistance_multiplier"]),
        )
        x = [float(row["al_al_resistance_multiplier"]) for row in selected]
        for solver, linestyle in (("comsol", "-"), ("fvm", "--")):
            axes[0].plot(
                x,
                [float(row[f"{solver}_power_w_per_m_depth"]) for row in selected],
                marker="o",
                linestyle=linestyle,
                color=colors[mode],
                label=f"{mode.replace('_', ' ')} {solver.upper()}",
            )
            axes[1].plot(
                x,
                [float(row[f"{solver}_temperature_rise_k"]) for row in selected],
                marker="o",
                linestyle=linestyle,
                color=colors[mode],
            )
    axes[0].set_ylabel("Joule power (W/m depth)")
    axes[1].set_ylabel("Maximum temperature rise (K)")
    for axis in axes:
        axis.set_xscale("log")
        axis.set_yscale("log")
        axis.set_xlabel("Al-Al resistance multiplier")
        axis.grid(True, alpha=0.25)
    axes[0].legend(frameon=False, fontsize=8)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _write_report(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# Stage 04 Loading-Mode COMSOL/FVM Report",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "| Mode | R multiplier | Voltage (V) | COMSOL/FVM power (W/m) | COMSOL/FVM rise (K) | Power diff | Rise diff |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["rows"]:
        lines.append(
            f"| {row['loading_mode']} | {row['al_al_resistance_multiplier']:.0f} | "
            f"{row['applied_voltage_v']:.9g} | {row['comsol_power_w_per_m_depth']:.6g} / "
            f"{row['fvm_power_w_per_m_depth']:.6g} | {row['comsol_temperature_rise_k']:.6g} / "
            f"{row['fvm_temperature_rise_k']:.6g} | {row['power_relative_difference']:.3%} | "
            f"{row['temperature_rise_relative_difference']:.3%} |"
        )
    lines.extend(
        [
            "",
            "All COMSOL cases use the already accepted 3316-element medium mesh. The loading modes",
            "are a project mechanism extension because the audited Liu PDF does not specify an",
            "electrical boundary condition.",
            "",
            "## Boundary",
            "",
            str(result["interpretation_boundary"]),
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def analyze(
    evidence_dir: Path,
    loading_parameter_json: Path,
    comsol_evidence_dir: Path | None = None,
) -> dict[str, Any]:
    loading = json.loads(loading_parameter_json.read_text(encoding="utf-8"))
    fvm_result = json.loads((evidence_dir / "loading_mode_summary.json").read_text(encoding="utf-8"))
    plan = json.loads((evidence_dir / "comsol_run_plan.json").read_text(encoding="utf-8"))
    comsol_root = evidence_dir if comsol_evidence_dir is None else comsol_evidence_dir
    fvm_by_case = {row["case_id"]: row for row in fvm_result["rows"]}
    acceptance = loading["acceptance"]
    ambient = float(loading["ambient_temperature_k"])
    rows: list[dict[str, Any]] = []
    for case in plan["cases"]:
        fvm = fvm_by_case[case["case_id"]]
        multiplier_label = f"multiplier_{float(case['al_al_resistance_multiplier']):g}".replace(".", "p")
        comsol_dir = comsol_root / "comsol" / case["loading_mode"] / multiplier_label
        comsol = json.loads((comsol_dir / "comsol_summary.json").read_text(encoding="utf-8"))
        log_metrics = parse_comsol_log(
            (comsol_dir / "comsol_batch.log").read_text(encoding="utf-8", errors="replace")
        )
        hotspots = field_hotspots(comsol_dir / "comsol_fields.csv")
        comsol_power = float(comsol["integrated_joule_2d_w_per_m_depth"])
        fvm_power = float(fvm["electric_power_w_per_m_depth"])
        comsol_rise = float(comsol["max_temperature_k"]) - ambient
        fvm_rise = float(fvm["temperature_rise_max_k"])
        comsol_current = float(comsol["top_current_a_per_m_depth"])
        fvm_current = float(fvm["top_current_a_per_m_depth"])
        power_difference = relative_difference(comsol_power, fvm_power)
        rise_difference = relative_difference(comsol_rise, fvm_rise)
        current_difference = relative_difference(comsol_current, fvm_current)
        case_gate = (
            comsol.get("solve_status") == "success"
            and not bool(log_metrics["log_error"])
            and math.isclose(float(comsol["applied_voltage_v"]), float(case["applied_voltage_v"]), rel_tol=1e-10)
            and power_difference <= float(acceptance["comsol_fvm_power_relative_difference_max"])
            and rise_difference <= float(acceptance["comsol_fvm_temperature_rise_relative_difference_max"])
            and current_difference <= float(acceptance["comsol_fvm_current_relative_difference_max"])
        )
        rows.append(
            {
                "case_id": case["case_id"],
                "loading_mode": case["loading_mode"],
                "al_al_resistance_multiplier": float(case["al_al_resistance_multiplier"]),
                "applied_voltage_v": float(case["applied_voltage_v"]),
                "element_count": int(log_metrics["element_count"]),
                "minimum_element_quality": float(log_metrics["minimum_element_quality"]),
                "dof_count": int(log_metrics["dof_count"]),
                "comsol_power_w_per_m_depth": comsol_power,
                "fvm_power_w_per_m_depth": fvm_power,
                "power_relative_difference": power_difference,
                "comsol_temperature_rise_k": comsol_rise,
                "fvm_temperature_rise_k": fvm_rise,
                "temperature_rise_relative_difference": rise_difference,
                "comsol_current_a_per_m_depth": comsol_current,
                "fvm_current_a_per_m_depth": fvm_current,
                "current_relative_difference": current_difference,
                **hotspots,
                "fvm_joule_hotspot_x_um": float(fvm["joule_hotspot_x_um"]),
                "fvm_joule_hotspot_y_um": float(fvm["joule_hotspot_y_um"]),
                "fvm_temperature_hotspot_x_um": float(fvm["temperature_hotspot_x_um"]),
                "fvm_temperature_hotspot_y_um": float(fvm["temperature_hotspot_y_um"]),
                "case_gate": case_gate,
            }
        )
    rows.sort(key=lambda row: (str(row["loading_mode"]), float(row["al_al_resistance_multiplier"])))
    gates = evaluate_global_gates(
        rows,
        int(loading["comsol_mesh"]["expected_element_count"]),
        float(acceptance["same_scenario_cross_mode_hotspot_distance_um_max"]),
    )
    failed_case_ids = [str(row["case_id"]) for row in rows if not bool(row["case_gate"])]
    decision = "loading_mode_comsol_pass" if all(gates.values()) else "review"
    result = {
        "decision": decision,
        "failed_case_ids": failed_case_ids,
        "original_preregistered_decision_preserved": True,
        "gates": gates,
        "rows": rows,
        "interpretation_boundary": (
            "This verifies conditional loading-mode behavior and cross-solver consistency. "
            "It does not establish a percolating particle-resolved network or experimental temperature."
        ),
    }
    output = evidence_dir / "comparison"
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "loading_mode_comparison.csv", rows)
    (output / "loading_mode_comparison.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    _write_report(output / "report.md", result)
    _plot(rows, output / "comsol_fvm_loading_comparison.png")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze six fixed-mesh COMSOL loading cases")
    parser.add_argument("evidence_dir", type=Path)
    parser.add_argument("loading_parameter_json", type=Path)
    parser.add_argument(
        "--comsol-evidence-dir",
        type=Path,
        help="Read archived COMSOL cases here while writing comparison beside the FVM evidence",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = analyze(args.evidence_dir, args.loading_parameter_json, args.comsol_evidence_dir)
    print(json.dumps(result, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
