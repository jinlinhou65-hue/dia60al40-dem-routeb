from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

from electrothermal_contact_model import (
    analyze_topology,
    build_contact_physics,
    gaussian_property_grid,
    load_parameter_set,
    read_contacts,
    read_particles,
    write_csv,
)
from solve_electrothermal_fvm import solve_fvm


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hotspot_metrics(field_csv: Path) -> dict[str, float]:
    with field_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    joule_row = max(rows, key=lambda row: float(row["joule_w_m3"]))
    temperature_row = max(rows, key=lambda row: float(row["temperature_k"]))
    return {
        "joule_hotspot_x_um": float(joule_row["x_um"]),
        "joule_hotspot_y_um": float(joule_row["y_um"]),
        "joule_hotspot_w_m3": float(joule_row["joule_w_m3"]),
        "temperature_hotspot_x_um": float(temperature_row["x_um"]),
        "temperature_hotspot_y_um": float(temperature_row["y_um"]),
    }


def plot_sensitivity(rows: list[dict[str, Any]], output_dir: Path) -> None:
    multipliers = [float(row["al_al_resistance_multiplier"]) for row in rows]
    powers = [float(row["electric_power_w_per_m_depth"]) for row in rows]
    rises = [float(row["temperature_rise_max_k"]) for row in rows]
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.8), constrained_layout=True)
    axes[0].plot(multipliers, powers, marker="o", color="#006d77")
    axes[0].set_ylabel("Joule power (W/m depth)")
    axes[1].plot(multipliers, rises, marker="o", color="#c44536")
    axes[1].set_ylabel("Maximum temperature rise (K)")
    for axis in axes:
        axis.set_xscale("log")
        axis.set_xlabel("Al-Al resistance multiplier")
        axis.grid(True, alpha=0.25)
    fig.savefig(output_dir / "contact_resistance_sensitivity.png", dpi=180)
    plt.close(fig)


def plot_contact_network(
    particles: dict[int, dict[str, Any]],
    rows: list[dict[str, Any]],
    topology: dict[str, Any],
    height_um: float,
    output_dir: Path,
) -> None:
    cutoff = float(topology["electrical_active_conductance_cutoff_s"])
    pair_colors = {"Al-Al": "#006d77", "Al-Diamond": "#d17b0f", "Diamond-Diamond": "#6c757d"}
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.6), constrained_layout=True)
    for axis, active_only, title in (
        (axes[0], False, "All direct contacts"),
        (axes[1], True, "Electrically active contacts"),
    ):
        for row in rows:
            if active_only and float(row["electrical_conductance_s"]) < cutoff:
                continue
            first, second = particles[int(row["i"])], particles[int(row["j"])]
            axis.plot(
                [first["x_um"], second["x_um"]],
                [first["y_um"], second["y_um"]],
                color=pair_colors[str(row["contact_type"])],
                linewidth=1.0 if active_only else 0.65,
                alpha=0.85 if active_only else 0.5,
            )
        for material, marker, color in (("Al", "o", "#83c5be"), ("Diamond", "s", "#495057")):
            selected = [particle for particle in particles.values() if particle["material"] == material]
            axis.scatter(
                [particle["x_um"] for particle in selected],
                [particle["y_um"] for particle in selected],
                s=18,
                marker=marker,
                color=color,
                edgecolor="white",
                linewidth=0.3,
                label=material,
                zorder=3,
            )
        axis.axhline(0.0, color="#1d3557", linewidth=2.0)
        axis.axhline(height_um, color="#c1121f", linewidth=2.0)
        axis.set_xlim(0.0, 400.0)
        axis.set_ylim(-4.0, height_um + 4.0)
        axis.set_aspect("equal", adjustable="box")
        axis.set_xlabel("x (um)")
        axis.set_ylabel("y (um)")
        axis.set_title(title)
    axes[0].legend(frameon=False, loc="upper right")
    status = "percolating" if topology["electrical_percolates_bottom_to_top"] else "not percolating"
    fig.suptitle(f"Stage 5 contact topology: active network is {status}")
    fig.savefig(output_dir / "contact_network_topology.png", dpi=180)
    plt.close(fig)


def run_sensitivity(
    particle_csv: Path,
    contact_csv: Path,
    parameter_json: Path,
    output_dir: Path,
) -> dict[str, Any]:
    parameters = load_parameter_set(parameter_json)
    particles, height_um = read_particles(particle_csv)
    contacts = read_contacts(contact_csv)
    parameters["domain_height_um"] = height_um
    contact_model = parameters["contact_model"]
    reference_multiplier = float(contact_model["al_al_resistance_multiplier_reference"])
    reference_rows = build_contact_physics(
        particles, contacts, parameters, al_al_multiplier=reference_multiplier
    )
    topology = analyze_topology(particles, height_um, reference_rows, parameters)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "reference_contact_physics.csv", reference_rows)
    (output_dir / "topology_summary.json").write_text(
        json.dumps(topology, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    plot_contact_network(particles, reference_rows, topology, height_um, output_dir)

    scenario_summaries: list[dict[str, Any]] = []
    voltage = float(parameters["continuum_mapping"]["voltage_v"])
    for multiplier in contact_model["al_al_resistance_multiplier_sweep"]:
        scenario_rows = build_contact_physics(
            particles, contacts, parameters, al_al_multiplier=float(multiplier)
        )
        grid = gaussian_property_grid(scenario_rows, reference_rows, parameters)
        label = f"multiplier_{float(multiplier):g}".replace(".", "p")
        scenario_dir = output_dir / label
        grid_path = scenario_dir / "stage5_contact_property_grid.csv"
        write_csv(grid_path, grid)
        write_csv(scenario_dir / "contact_physics.csv", scenario_rows)
        fvm_summary = solve_fvm(grid_path, scenario_dir / "fvm", applied_voltage=voltage)
        metrics = hotspot_metrics(scenario_dir / "fvm" / "fvm_fields.csv")
        scenario_summaries.append(
            {
                "scenario": label,
                "al_al_resistance_multiplier": float(multiplier),
                "electrical_network_percolates": topology["electrical_percolates_bottom_to_top"],
                **fvm_summary,
                **metrics,
            }
        )

    scenario_summaries.sort(key=lambda row: float(row["al_al_resistance_multiplier"]))
    powers = [float(row["electric_power_w_per_m_depth"]) for row in scenario_summaries]
    rises = [float(row["temperature_rise_max_k"]) for row in scenario_summaries]
    power_monotonic = all(left >= right for left, right in zip(powers, powers[1:]))
    rise_monotonic = all(left >= right for left, right in zip(rises, rises[1:]))
    balance_pass = all(
        float(row["electric_relative_balance_error"]) <= 1.0e-8 for row in scenario_summaries
    )
    decision = "conditional_sensitivity_pass" if power_monotonic and rise_monotonic and balance_pass else "fail"
    write_csv(output_dir / "sensitivity_summary.csv", scenario_summaries)
    plot_sensitivity(scenario_summaries, output_dir)
    result = {
        "decision": decision,
        "interpretation": "conditional_continuum_screen_not_experimental_prediction",
        "electrical_network_percolates": topology["electrical_percolates_bottom_to_top"],
        "power_nonincreasing_with_resistance": power_monotonic,
        "temperature_rise_nonincreasing_with_resistance": rise_monotonic,
        "power_balance_pass": balance_pass,
        "scenario_count": len(scenario_summaries),
        "frozen_grid": {
            "nx": parameters["continuum_mapping"]["nx"],
            "ny": parameters["continuum_mapping"]["ny"],
        },
        "fixed_comsol_mesh_reference_elements": 3316,
        "source_hashes": {
            "particles_sha256": file_sha256(particle_csv),
            "contacts_sha256": file_sha256(contact_csv),
            "parameters_sha256": file_sha256(parameter_json),
        },
        "scenarios": scenario_summaries,
    }
    (output_dir / "sensitivity_summary.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run material-aware contact sensitivity screening")
    parser.add_argument("particle_csv", type=Path)
    parser.add_argument("contact_csv", type=Path)
    parser.add_argument("parameter_json", type=Path)
    parser.add_argument("output_dir", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_sensitivity(
        args.particle_csv, args.contact_csv, args.parameter_json, args.output_dir
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
