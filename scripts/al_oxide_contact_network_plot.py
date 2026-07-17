from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def plot_sensitivity(path: Path, scenarios: list[dict[str, Any]]) -> None:
    partial = [row for row in scenarios if row["model"] == "partial_rupture"]
    intact = [row for row in scenarios if row["model"] == "intact_oxide"]
    fractions = [float(row["metallic_bridge_fraction"]) for row in partial]
    x_values = np.arange(len(fractions))
    x_labels = ["0" if value == 0 else f"{value:.0e}" for value in fractions]
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    axes[0, 0].plot(x_values, [row["equivalent_resistance_ohm"] for row in partial], "o-")
    axes[0, 0].set(yscale="log", xlabel="Metallic bridge area fraction", ylabel="Equivalent resistance (ohm)")
    axes[0, 0].set_xticks(x_values, x_labels, rotation=35)
    axes[0, 0].grid(True, which="both", alpha=0.25)
    axes[0, 1].plot(x_values, [row["total_power_w_fixed_voltage"] for row in partial], "o-", label="0.1 V")
    axes[0, 1].plot(x_values, [row["total_power_w_fixed_current"] for row in partial], "s-", label="1 A")
    axes[0, 1].set(yscale="log", xlabel="Metallic bridge area fraction", ylabel="Total Joule power (W)")
    axes[0, 1].set_xticks(x_values, x_labels, rotation=35)
    axes[0, 1].legend()
    axes[0, 1].grid(True, which="both", alpha=0.25)
    thicknesses = sorted({float(row["particle_film_thickness_m"]) for row in intact})
    resistivities = sorted({float(row["film_resistivity_ohm_m"]) for row in intact})
    grid = np.array(
        [
            [
                next(
                    row["equivalent_resistance_ohm"]
                    for row in intact
                    if row["particle_film_thickness_m"] == thickness
                    and row["film_resistivity_ohm_m"] == resistivity
                )
                for resistivity in resistivities
            ]
            for thickness in thicknesses
        ]
    )
    image = axes[1, 0].imshow(np.log10(grid), aspect="auto", origin="lower", cmap="viridis")
    axes[1, 0].set_xticks(range(len(resistivities)), [f"{value:.0e}" for value in resistivities])
    axes[1, 0].set_yticks(range(len(thicknesses)), [f"{value*1e9:.0f}" for value in thicknesses])
    axes[1, 0].set(
        xlabel="Effective film resistivity (ohm m)",
        ylabel="Film thickness per particle (nm)",
        title="log10 intact-film equivalent R",
    )
    fig.colorbar(image, ax=axes[1, 0], label="log10(R/ohm)")
    axes[1, 1].plot(
        x_values,
        [row["shortest_path_resistance_ohm"] / row["equivalent_resistance_ohm"] for row in partial],
        "o-",
    )
    axes[1, 1].set(xlabel="Metallic bridge area fraction", ylabel="Shortest path R / network R")
    axes[1, 1].set_xticks(x_values, x_labels, rotation=35)
    axes[1, 1].grid(True, which="both", alpha=0.25)
    fig.suptitle("Archived 3D Al-Al network: preregistered oxide-contact sensitivity")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_hotspots(
    path: Path,
    particles: list[dict[str, str]],
    scenario_rows: list[dict[str, Any]],
    edge_rows: list[dict[str, Any]],
    bottom: set[int],
    top: set[int],
) -> None:
    selected = ["clean", "intact_d6e-09_rho1e+06", "partial_f1e-06"]
    coordinates = {
        int(float(row["particle_id"])): (float(row["x_um"]), float(row["y_um"]), float(row["z_um"]))
        for row in particles
    }
    summaries = {row["scenario_id"]: row for row in scenario_rows}
    fig = plt.figure(figsize=(15, 5), constrained_layout=True)
    cmap = plt.get_cmap("inferno")
    normalizer = plt.Normalize(-6.0, 0.0)
    for panel, scenario_id in enumerate(selected, start=1):
        axis = fig.add_subplot(1, 3, panel, projection="3d")
        rows = [row for row in edge_rows if row["scenario_id"] == scenario_id]
        maximum = max(float(row["joule_power_w_fixed_voltage"]) for row in rows)
        for row in rows:
            first, second = coordinates[int(row["i"])], coordinates[int(row["j"])]
            relative = max(float(row["joule_power_w_fixed_voltage"]) / maximum, 1e-6)
            color = cmap(normalizer(math.log10(relative))) if row["included_in_transport"] else "#c7c7c7"
            axis.plot(*zip(first, second), color=color, linewidth=0.5 + 2.5 * math.sqrt(relative), alpha=0.9)
        ids = sorted(coordinates)
        node_colors = [
            "#2563eb" if node in bottom else "#dc2626" if node in top else "#6b7280"
            for node in ids
        ]
        axis.scatter(
            [coordinates[node][0] for node in ids],
            [coordinates[node][1] for node in ids],
            [coordinates[node][2] for node in ids],
            c=node_colors,
            s=9,
            alpha=0.75,
        )
        summary = summaries[scenario_id]
        axis.set_title(f"{scenario_id}\nReq={summary['equivalent_resistance_ohm']:.3e} ohm")
        axis.set(xlabel="x (um)", ylabel="y (um)", zlabel="z (um)")
        axis.view_init(elev=22, azim=-55)
    scalar = plt.cm.ScalarMappable(norm=normalizer, cmap=cmap)
    fig.colorbar(
        scalar,
        ax=fig.axes,
        shrink=0.72,
        pad=0.02,
        label="log10(edge Joule power / scenario maximum)",
    )
    fig.suptitle("Fixed 0.1 V: spatial Joule paths on the frozen direct-contact graph")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)
