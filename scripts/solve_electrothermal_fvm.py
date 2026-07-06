from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve


def read_property_grid(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("property grid is empty")

    xs = np.array(sorted({float(row["x_um"]) for row in rows}), dtype=float)
    ys = np.array(sorted({float(row["y_um"]) for row in rows}), dtype=float)
    if len(rows) != len(xs) * len(ys):
        raise ValueError("property grid must be a complete structured grid")
    index = {(float(row["x_um"]), float(row["y_um"])): row for row in rows}
    sigma = np.empty((len(ys), len(xs)), dtype=float)
    conductivity = np.empty_like(sigma)
    for iy, y in enumerate(ys):
        for ix, x in enumerate(xs):
            row = index[(x, y)]
            sigma[iy, ix] = float(row["sigma_s_m"])
            conductivity[iy, ix] = float(row["k_w_mk"])
    if np.any(sigma <= 0) or np.any(conductivity <= 0):
        raise ValueError("electrical and thermal conductivity must be positive")
    return xs * 1.0e-6, ys * 1.0e-6, sigma, conductivity


def harmonic(a: float, b: float) -> float:
    return 2.0 * a * b / (a + b)


def solve_dirichlet_neumann(
    coeff: np.ndarray,
    xs: np.ndarray,
    ys: np.ndarray,
    *,
    bottom_value: float,
    top_value: float,
    source: np.ndarray | None = None,
) -> np.ndarray:
    ny, nx = coeff.shape
    dx = float(xs[1] - xs[0])
    dy = float(ys[1] - ys[0])
    matrix = lil_matrix((nx * ny, nx * ny), dtype=float)
    rhs = np.zeros(nx * ny, dtype=float)

    def node(ix: int, iy: int) -> int:
        return iy * nx + ix

    for iy in range(ny):
        for ix in range(nx):
            row = node(ix, iy)
            if iy == 0:
                matrix[row, row] = 1.0
                rhs[row] = bottom_value
                continue
            if iy == ny - 1:
                matrix[row, row] = 1.0
                rhs[row] = top_value
                continue
            north = harmonic(coeff[iy, ix], coeff[iy + 1, ix]) * dx / dy
            south = harmonic(coeff[iy, ix], coeff[iy - 1, ix]) * dx / dy
            diagonal = north + south
            matrix[row, node(ix, iy + 1)] = -north
            matrix[row, node(ix, iy - 1)] = -south
            if ix < nx - 1:
                east = harmonic(coeff[iy, ix], coeff[iy, ix + 1]) * dy / dx
                diagonal += east
                matrix[row, node(ix + 1, iy)] = -east
            if ix > 0:
                west = harmonic(coeff[iy, ix], coeff[iy, ix - 1]) * dy / dx
                diagonal += west
                matrix[row, node(ix - 1, iy)] = -west
            matrix[row, row] = diagonal
            if source is not None:
                rhs[row] = float(source[iy, ix]) * dx * dy

    values = spsolve(matrix.tocsr(), rhs)
    if not np.all(np.isfinite(values)):
        raise RuntimeError("finite-volume solve produced non-finite values")
    return values.reshape((ny, nx))


def electrical_diagnostics(
    voltage: np.ndarray,
    sigma: np.ndarray,
    xs: np.ndarray,
    ys: np.ndarray,
    applied_voltage: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float, float, float]:
    dx = float(xs[1] - xs[0])
    dy = float(ys[1] - ys[0])
    grad_y, grad_x = np.gradient(voltage, dy, dx)
    jx = -sigma * grad_x
    jy = -sigma * grad_y
    q_raw = sigma * (grad_x * grad_x + grad_y * grad_y)

    top_sigma = 2.0 * sigma[-1, :] * sigma[-2, :] / (sigma[-1, :] + sigma[-2, :])
    # Use the same edge conductances as the assembled finite-volume operator.
    top_current = float(np.sum(-top_sigma * dx * (voltage[-1, :] - voltage[-2, :]) / dy))

    edge_power = 0.0
    for iy in range(sigma.shape[0]):
        for ix in range(sigma.shape[1] - 1):
            conductance = harmonic(sigma[iy, ix], sigma[iy, ix + 1]) * dy / dx
            edge_power += conductance * (voltage[iy, ix + 1] - voltage[iy, ix]) ** 2
    for iy in range(sigma.shape[0] - 1):
        for ix in range(sigma.shape[1]):
            conductance = harmonic(sigma[iy, ix], sigma[iy + 1, ix]) * dx / dy
            edge_power += conductance * (voltage[iy + 1, ix] - voltage[iy, ix]) ** 2

    boundary_power = abs(applied_voltage * top_current)
    scale = edge_power / float(np.trapezoid(np.trapezoid(q_raw, xs, axis=1), ys))
    q = q_raw * scale
    relative_balance_error = abs(edge_power - boundary_power) / max(edge_power, boundary_power, 1.0e-30)
    return jx, jy, q, top_current, edge_power, relative_balance_error


def solve_fvm(
    grid_csv: Path,
    output_dir: Path,
    *,
    applied_voltage: float = 0.1,
    ambient_temperature_k: float = 293.15,
) -> dict[str, float | int | str]:
    xs, ys, sigma, conductivity = read_property_grid(grid_csv)
    voltage = solve_dirichlet_neumann(
        sigma,
        xs,
        ys,
        bottom_value=0.0,
        top_value=applied_voltage,
    )
    jx, jy, joule, top_current, electric_power, balance_error = electrical_diagnostics(
        voltage, sigma, xs, ys, applied_voltage
    )
    temperature = solve_dirichlet_neumann(
        conductivity,
        xs,
        ys,
        bottom_value=ambient_temperature_k,
        top_value=ambient_temperature_k,
        source=joule,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    field_path = output_dir / "fvm_fields.csv"
    with field_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["x_um", "y_um", "voltage_v", "jx_a_m2", "jy_a_m2", "jmag_a_m2", "joule_w_m3", "temperature_k"]
        )
        for iy, y in enumerate(ys):
            for ix, x in enumerate(xs):
                writer.writerow(
                    [
                        x * 1.0e6,
                        y * 1.0e6,
                        voltage[iy, ix],
                        jx[iy, ix],
                        jy[iy, ix],
                        float(np.hypot(jx[iy, ix], jy[iy, ix])),
                        joule[iy, ix],
                        temperature[iy, ix],
                    ]
                )

    summary: dict[str, float | int | str] = {
        "solver": "structured_finite_volume_parallel_check",
        "nx": len(xs),
        "ny": len(ys),
        "applied_voltage_v": applied_voltage,
        "ambient_temperature_k": ambient_temperature_k,
        "top_current_a_per_m_depth": abs(top_current),
        "electric_power_w_per_m_depth": electric_power,
        "electric_relative_balance_error": balance_error,
        "voltage_min_v": float(np.min(voltage)),
        "voltage_max_v": float(np.max(voltage)),
        "temperature_min_k": float(np.min(temperature)),
        "temperature_max_k": float(np.max(temperature)),
        "temperature_rise_max_k": float(np.max(temperature) - ambient_temperature_k),
        "field_csv": field_path.name,
    }
    (output_dir / "fvm_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    plot_fields(xs, ys, voltage, np.hypot(jx, jy), joule, temperature, output_dir)
    return summary


def plot_fields(
    xs: np.ndarray,
    ys: np.ndarray,
    voltage: np.ndarray,
    current: np.ndarray,
    joule: np.ndarray,
    temperature: np.ndarray,
    output_dir: Path,
) -> None:
    extent = [xs[0] * 1.0e6, xs[-1] * 1.0e6, ys[0] * 1.0e6, ys[-1] * 1.0e6]
    fields = [
        (voltage, "Potential (V)", "viridis"),
        (current, "Current density magnitude (A/m2)", "magma"),
        (joule, "Joule heating (W/m3)", "inferno"),
        (temperature, "Temperature (K)", "plasma"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(10, 6.6), constrained_layout=True)
    for axis, (field, title, cmap) in zip(axes.flat, fields, strict=True):
        image = axis.imshow(field, origin="lower", extent=extent, aspect="auto", cmap=cmap)
        axis.set_title(title)
        axis.set_xlabel("x (um)")
        axis.set_ylabel("y (um)")
        fig.colorbar(image, ax=axis, shrink=0.85)
    fig.savefig(output_dir / "fvm_electrothermal_fields.png", dpi=180)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the open-source electrothermal FVM parallel check")
    parser.add_argument("grid_csv", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--voltage-v", type=float, default=0.1)
    parser.add_argument("--ambient-k", type=float, default=293.15)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = solve_fvm(
        args.grid_csv,
        args.output_dir,
        applied_voltage=args.voltage_v,
        ambient_temperature_k=args.ambient_k,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
