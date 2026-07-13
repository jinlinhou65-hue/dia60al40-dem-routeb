from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt


def plot_network(
    path: Path,
    particles: dict[int, dict[str, Any]],
    physics_rows: list[dict[str, Any]],
    active_indices: list[int],
    path_edge_indices: list[int],
    bottom: set[int],
    top: set[int],
) -> None:
    fig = plt.figure(figsize=(8.2, 6.6))
    axis = fig.add_subplot(111, projection="3d")
    for material, color in (("Al", "#d1495b"), ("Diamond", "#2a6f97")):
        selected = [row for row in particles.values() if row["material"] == material]
        axis.scatter(
            [float(row["x_um"]) for row in selected],
            [float(row["z_um"]) for row in selected],
            [float(row["y_um"]) for row in selected],
            s=[max(12.0, float(row["radius_um"]) * 1.8) for row in selected],
            c=color,
            alpha=0.78,
            label=material,
            depthshade=True,
        )
    path_set = set(path_edge_indices)
    for index in active_indices:
        row = physics_rows[index]
        first, second = particles[int(row["i"])], particles[int(row["j"])]
        is_path = index in path_set
        axis.plot(
            [first["x_um"], second["x_um"]],
            [first["z_um"], second["z_um"]],
            [first["y_um"], second["y_um"]],
            color="#f4b942" if is_path else "#626d71",
            linewidth=3.0 if is_path else 0.7,
            alpha=1.0 if is_path else 0.35,
        )
    for nodes, marker, color, label in (
        (bottom, "v", "#111111", "Bottom electrode"),
        (top, "^", "#f4b942", "Top electrode"),
    ):
        selected = [particles[node] for node in sorted(nodes)]
        axis.scatter(
            [row["x_um"] for row in selected],
            [row["z_um"] for row in selected],
            [row["y_um"] for row in selected],
            marker=marker,
            c=color,
            s=45,
            label=label,
        )
    axis.set_xlabel("x (um)")
    axis.set_ylabel("z (um)")
    axis.set_zlabel("loading y (um)")
    axis.view_init(elev=22, azim=-58)
    axis.legend(loc="upper left", frameon=False)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=190)
    plt.close(fig)
