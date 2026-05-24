from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

from dem_stage_metadata import STAGE_BY_ID, UM_PER_CM, particle_shape, read_liggghts_dump


def import_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, RegularPolygon

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.linewidth": 1.0,
            "axes.labelsize": 11,
            "axes.titlesize": 12,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 9,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )
    return plt, Circle, RegularPolygon


def read_curve(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def f(row: dict[str, str], key: str) -> float:
    return float(row[key])


def f_default(row: dict[str, str], key: str, default: float) -> float:
    value = row.get(key, "")
    return default if value == "" else float(value)


def save_pressure_plots(rows: list[dict[str, str]], outdir: Path) -> None:
    plt, _, _ = import_matplotlib()
    rho = [f(row, "actual_rho_total") for row in rows]
    pressure = [f(row, "pressure_mpa") for row in rows]
    displacement = [f(row, "top_displacement_um") for row in rows]
    al_modulus = [f_default(row, "al_modulus_gpa", float("nan")) for row in rows]
    contacts = [f(row, "avg_contact_count") for row in rows]
    overlap = [f(row, "max_overlap_um") for row in rows]
    overlap_ratio = [f_default(row, "max_overlap_ratio", float("nan")) for row in rows]
    bottom_pressure = [f_default(row, "bottom_pressure_mpa", 0.0) for row in rows]
    left_pressure = [f_default(row, "left_pressure_mpa", 0.0) for row in rows]
    right_pressure = [f_default(row, "right_pressure_mpa", 0.0) for row in rows]

    fig, ax = plt.subplots(figsize=(7.2, 4.8), dpi=180)
    ax.plot(rho, pressure, marker="o", linewidth=2.0, color="#1f4e79")
    ax.set_xlabel("Total relative density")
    ax.set_ylabel("Punch pressure (MPa)")
    ax.set_title("Pressure-density curve")
    ax.grid(True, alpha=0.3)
    ax.tick_params(direction="in", top=True, right=True)
    fig.tight_layout()
    fig.savefig(outdir / "pressure_density_curve.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 4.8), dpi=180)
    ax.plot(displacement, pressure, marker="o", linewidth=2.0, color="#8a3ffc")
    ax.set_xlabel("Top punch displacement (um)")
    ax.set_ylabel("Punch pressure (MPa)")
    ax.set_title("Pressure-displacement curve")
    ax.grid(True, alpha=0.3)
    ax.tick_params(direction="in", top=True, right=True)
    fig.tight_layout()
    fig.savefig(outdir / "pressure_displacement_curve.png")
    plt.close(fig)

    fig, ax1 = plt.subplots(figsize=(7.2, 4.8), dpi=180)
    ax1.plot(rho, al_modulus, marker="s", linewidth=2.0, color="#c43b3b")
    ax1.set_xlabel("Total relative density")
    ax1.set_ylabel("Al DEM modulus (GPa)", color="#c43b3b")
    ax1.tick_params(axis="y", labelcolor="#c43b3b")
    ax2 = ax1.twinx()
    ax2.plot(rho, pressure, marker="o", linewidth=2.0, color="#1f4e79")
    ax2.set_ylabel("Punch pressure (MPa)", color="#1f4e79")
    ax2.tick_params(axis="y", labelcolor="#1f4e79")
    ax1.set_title("Staged Al hardening and pressure")
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(direction="in", top=True)
    ax2.tick_params(direction="in", right=True)
    fig.tight_layout()
    fig.savefig(outdir / "al_modulus_pressure_curve.png")
    plt.close(fig)

    fig, ax1 = plt.subplots(figsize=(7.2, 4.8), dpi=180)
    ax1.plot(rho, contacts, marker="o", linewidth=2.0, color="#276749")
    ax1.set_xlabel("Total relative density")
    ax1.set_ylabel("Average contact count", color="#276749")
    ax1.tick_params(axis="y", labelcolor="#276749")
    ax2 = ax1.twinx()
    ax2.plot(rho, overlap, marker="s", linewidth=2.0, color="#b7791f")
    ax2.set_ylabel("Max overlap (um)", color="#b7791f")
    ax2.tick_params(axis="y", labelcolor="#b7791f")
    ax1.set_title("Contact-network diagnostics")
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(direction="in", top=True)
    ax2.tick_params(direction="in", right=True)
    fig.tight_layout()
    fig.savefig(outdir / "contact_overlap_diagnostics.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 4.8), dpi=180)
    ax.plot(rho, overlap_ratio, marker="o", linewidth=2.0, color="#b7791f")
    ax.set_xlabel("Total relative density")
    ax.set_ylabel("Max overlap / minimum radius")
    ax.set_title("Normalized overlap diagnostic")
    ax.grid(True, alpha=0.3)
    ax.tick_params(direction="in", top=True, right=True)
    fig.tight_layout()
    fig.savefig(outdir / "normalized_overlap_curve.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 4.8), dpi=180)
    ax.plot(rho, pressure, marker="o", linewidth=2.0, label="Top", color="#1f4e79")
    ax.plot(rho, bottom_pressure, marker="s", linewidth=2.0, label="Bottom", color="#805ad5")
    ax.plot(rho, left_pressure, marker="^", linewidth=2.0, label="Left wall", color="#276749")
    ax.plot(rho, right_pressure, marker="v", linewidth=2.0, label="Right wall", color="#c43b3b")
    ax.set_xlabel("Total relative density")
    ax.set_ylabel("Boundary pressure (MPa)")
    ax.set_title("Boundary reaction pressures")
    ax.grid(True, alpha=0.3)
    ax.legend(frameon=False)
    ax.tick_params(direction="in", top=True, right=True)
    fig.tight_layout()
    fig.savefig(outdir / "boundary_pressure_curve.png")
    plt.close(fig)


def latest_stage_dump(root: Path, stage_id: str) -> Path:
    matches = sorted(root.glob(f"{stage_id}_*.dump"))
    if not matches:
        raise SystemExit(f"[FAIL] no dump found for {stage_id}")
    return matches[-1]


def plot_stage(root: Path, stage_id: str, outdir: Path) -> None:
    plt, Circle, RegularPolygon = import_matplotlib()
    dump = latest_stage_dump(root, stage_id)
    rows = read_liggghts_dump(dump)
    _, target_rho, height_um, _, _ = STAGE_BY_ID[stage_id]

    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=180)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-25, 425)
    ax.set_ylim(-25, 230)
    ax.add_patch(plt.Rectangle((0, 0), 400, height_um, fill=False, linewidth=1.2, edgecolor="#444444"))

    for row in rows:
        x = float(row["x"]) * UM_PER_CM
        y = float(row["y"]) * UM_PER_CM
        r = float(row["radius"]) * UM_PER_CM
        shape = particle_shape(row)
        if shape == "Al":
            patch = Circle((x, y), r, facecolor="#d7e9ff", edgecolor="#235789", linewidth=0.6)
        else:
            patch = RegularPolygon(
                (x, y),
                numVertices=8,
                radius=r,
                orientation=math.radians(22.5),
                facecolor="#333333",
                edgecolor="#111111",
                linewidth=0.6,
            )
        ax.add_patch(patch)

    ax.set_xlabel("x (um)")
    ax.set_ylabel("y (um)")
    ax.set_title(f"{stage_id}: target rho={target_rho:.3f}, height={height_um:.1f} um")
    ax.tick_params(direction="in", top=True, right=True)
    fig.tight_layout()
    fig.savefig(outdir / f"particles_{stage_id}.png")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="liggghts/DEM")
    parser.add_argument("--curve", default="liggghts/DEM/pressure_density_curve.csv")
    parser.add_argument("--outdir", default="liggghts/DEM/plots")
    args = parser.parse_args()

    root = Path(args.root)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    rows = read_curve(Path(args.curve))
    save_pressure_plots(rows, outdir)
    for stage_id in STAGE_BY_ID:
        plot_stage(root, stage_id, outdir)
    print(f"[OK] wrote DEM plots to {outdir}")


if __name__ == "__main__":
    main()
