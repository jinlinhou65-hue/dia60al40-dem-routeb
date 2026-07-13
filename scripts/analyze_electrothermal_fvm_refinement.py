from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator, RegularGridInterpolator

from analyze_comsol_mesh_convergence import relative_difference
from analyze_electrothermal_mvp import read_comsol_fields
from solve_electrothermal_fvm import read_property_grid, solve_fvm


FACTORS = (1, 2, 3)


def resample_property_grid(source: Path, factor: int, output: Path) -> tuple[int, int]:
    if factor < 1:
        raise ValueError("refinement factor must be at least one")
    xs, ys, sigma, conductivity = read_property_grid(source)
    target_x = np.linspace(xs[0], xs[-1], (len(xs) - 1) * factor + 1)
    target_y = np.linspace(ys[0], ys[-1], (len(ys) - 1) * factor + 1)
    target_y_grid, target_x_grid = np.meshgrid(target_y, target_x, indexing="ij")
    points = np.column_stack((target_y_grid.ravel(), target_x_grid.ravel()))
    target_sigma = RegularGridInterpolator((ys, xs), sigma)(points).reshape(target_y_grid.shape)
    target_k = RegularGridInterpolator((ys, xs), conductivity)(points).reshape(target_y_grid.shape)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["x_um", "y_um", "sigma_s_m", "k_w_mk"])
        for iy, y in enumerate(target_y):
            for ix, x in enumerate(target_x):
                writer.writerow([x * 1.0e6, y * 1.0e6, target_sigma[iy, ix], target_k[iy, ix]])
    return len(target_x), len(target_y)


def read_fvm_fields(path: Path) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    xs = np.array(sorted({float(row["x_um"]) for row in rows}), dtype=float)
    ys = np.array(sorted({float(row["y_um"]) for row in rows}), dtype=float)
    index = {(float(row["x_um"]), float(row["y_um"])): row for row in rows}
    fields: dict[str, np.ndarray] = {}
    for name in ("joule_w_m3", "temperature_k"):
        values = np.empty((len(ys), len(xs)), dtype=float)
        for iy, y in enumerate(ys):
            for ix, x in enumerate(xs):
                values[iy, ix] = float(index[(x, y)][name])
        fields[name] = values
    return xs, ys, fields


def interpolate_comsol_to_grid(
    comsol: dict[str, np.ndarray],
    xs_um: np.ndarray,
    ys_um: np.ndarray,
    field_name: str,
) -> np.ndarray:
    source_points = np.column_stack((comsol["y_um"], comsol["x_um"]))
    target_y, target_x = np.meshgrid(ys_um, xs_um, indexing="ij")
    target_points = np.column_stack((target_y.ravel(), target_x.ravel()))
    linear = LinearNDInterpolator(source_points, comsol[field_name])(target_points)
    if np.any(np.isnan(linear)):
        nearest = NearestNDInterpolator(source_points, comsol[field_name])(target_points)
        linear = np.where(np.isnan(linear), nearest, linear)
    return np.asarray(linear, dtype=float).reshape(target_y.shape)


def weighted_top_centroid(
    xs_um: np.ndarray,
    ys_um: np.ndarray,
    field: np.ndarray,
    *,
    quantile: float = 0.99,
) -> dict[str, float | int]:
    if not 0.0 < quantile < 1.0:
        raise ValueError("quantile must lie strictly between zero and one")
    if field.shape != (len(ys_um), len(xs_um)) or not np.all(np.isfinite(field)):
        raise ValueError("field shape or values are invalid")
    threshold = float(np.quantile(field, quantile))
    mask = field >= threshold
    weights = np.maximum(field[mask], 0.0)
    if float(np.sum(weights)) <= 0.0:
        weights = np.ones(mask.sum(), dtype=float)
    y_grid, x_grid = np.meshgrid(ys_um, xs_um, indexing="ij")
    return {
        "x_um": float(np.average(x_grid[mask], weights=weights)),
        "y_um": float(np.average(y_grid[mask], weights=weights)),
        "threshold": threshold,
        "point_count": int(mask.sum()),
    }


def _centroid_distance(first: dict[str, float | int], second: dict[str, float | int]) -> float:
    return math.hypot(float(first["x_um"]) - float(second["x_um"]), float(first["y_um"]) - float(second["y_um"]))


def _write_report(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# Stage 04 Open-FVM Refinement Diagnostic",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "| Factor | Grid | Nodes | Power (W/m) | Max rise (K) | Balance error |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["levels"]:
        lines.append(
            f"| {row['factor']} | {row['nx']} x {row['ny']} | {row['node_count']} | "
            f"{row['electric_power_w_per_m_depth']:.8g} | {row['temperature_rise_max_k']:.8g} | "
            f"{row['electric_relative_balance_error']:.3g} |"
        )
    comparison = result["comparison"]
    lines.extend(
        [
            "",
            f"- Factor-2/3 power difference: `{comparison['factor2_factor3_power_difference']:.3%}`.",
            f"- Factor-2/3 temperature-rise difference: `{comparison['factor2_factor3_rise_difference']:.3%}`.",
            f"- Factor-3/COMSOL power difference: `{comparison['factor3_comsol_power_difference']:.3%}`.",
            f"- Factor-3/COMSOL rise difference: `{comparison['factor3_comsol_rise_difference']:.3%}`.",
            f"- Top-1% Joule centroid distance: `{comparison['joule_centroid_distance_um']:.3f} um`.",
            f"- Top-1% temperature-rise centroid distance: `{comparison['temperature_centroid_distance_um']:.3f} um`.",
            "",
            "The original six-case loading study remains review; this report tests whether the",
            "open-verifier discretization explains the sole cross-solver threshold miss.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _plot(
    path: Path,
    levels: list[dict[str, Any]],
    xs_um: np.ndarray,
    ys_um: np.ndarray,
    comsol_q: np.ndarray,
    fvm_q: np.ndarray,
    comsol_centroid: dict[str, float | int],
    fvm_centroid: dict[str, float | int],
) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8), constrained_layout=True)
    nodes = [int(row["node_count"]) for row in levels]
    axes[0].plot(nodes, [float(row["electric_power_w_per_m_depth"]) for row in levels], marker="o", label="Power")
    axes[0].set(xlabel="FVM nodes", ylabel="Joule power (W/m depth)", title="Open-solver refinement")
    for axis, field, title, centroid, color in (
        (axes[1], comsol_q, "COMSOL Joule field", comsol_centroid, "white"),
        (axes[2], fvm_q, "FVM Joule field", fvm_centroid, "white"),
    ):
        image = axis.imshow(
            field,
            origin="lower",
            extent=[xs_um[0], xs_um[-1], ys_um[0], ys_um[-1]],
            aspect="auto",
            cmap="inferno",
        )
        axis.scatter([centroid["x_um"]], [centroid["y_um"]], marker="x", color=color, s=45)
        axis.set(xlabel="x (um)", ylabel="y (um)", title=title)
        fig.colorbar(image, ax=axis, shrink=0.8)
    axes[0].grid(True, alpha=0.25)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def analyze(
    source_property_grid: Path,
    prepared_dir: Path,
    evidence_dir: Path,
    comsol_summary_path: Path,
    comsol_fields_path: Path,
) -> dict[str, Any]:
    levels: list[dict[str, Any]] = []
    for factor in FACTORS:
        prepared = prepared_dir / f"factor_{factor}" / "stage5_contact_property_grid.csv"
        nx, ny = resample_property_grid(source_property_grid, factor, prepared)
        output = evidence_dir / f"factor_{factor}"
        summary = solve_fvm(prepared, output, applied_voltage=0.1)
        levels.append({"factor": factor, "node_count": nx * ny, **summary})

    factor2, factor3 = levels[1], levels[2]
    comsol_summary = json.loads(comsol_summary_path.read_text(encoding="utf-8"))
    ambient = float(comsol_summary["ambient_temperature_k"])
    comsol_power = float(comsol_summary["integrated_joule_2d_w_per_m_depth"])
    comsol_rise = float(comsol_summary["max_temperature_k"]) - ambient
    comsol_current = float(comsol_summary["top_current_a_per_m_depth"])
    factor3_power = float(factor3["electric_power_w_per_m_depth"])
    factor3_rise = float(factor3["temperature_rise_max_k"])
    factor3_current = float(factor3["top_current_a_per_m_depth"])

    xs_um, ys_um, fine_fields = read_fvm_fields(evidence_dir / "factor_3" / "fvm_fields.csv")
    comsol = read_comsol_fields(comsol_fields_path)
    comsol_q = interpolate_comsol_to_grid(comsol, xs_um, ys_um, "joule_w_m3")
    comsol_temperature = interpolate_comsol_to_grid(comsol, xs_um, ys_um, "temperature_k") - ambient
    fvm_q = fine_fields["joule_w_m3"]
    fvm_temperature = fine_fields["temperature_k"] - ambient
    centroids = {
        "comsol_joule": weighted_top_centroid(xs_um, ys_um, comsol_q),
        "fvm_joule": weighted_top_centroid(xs_um, ys_um, fvm_q),
        "comsol_temperature": weighted_top_centroid(xs_um, ys_um, comsol_temperature),
        "fvm_temperature": weighted_top_centroid(xs_um, ys_um, fvm_temperature),
    }
    comparison = {
        "factor2_factor3_power_difference": relative_difference(
            float(factor2["electric_power_w_per_m_depth"]), factor3_power
        ),
        "factor2_factor3_rise_difference": relative_difference(
            float(factor2["temperature_rise_max_k"]), factor3_rise
        ),
        "factor3_comsol_power_difference": relative_difference(factor3_power, comsol_power),
        "factor3_comsol_rise_difference": relative_difference(factor3_rise, comsol_rise),
        "factor3_comsol_current_difference": relative_difference(factor3_current, comsol_current),
        "joule_centroid_distance_um": _centroid_distance(centroids["comsol_joule"], centroids["fvm_joule"]),
        "temperature_centroid_distance_um": _centroid_distance(
            centroids["comsol_temperature"], centroids["fvm_temperature"]
        ),
    }
    gates = {
        "all_balance_gate": all(float(row["electric_relative_balance_error"]) <= 1.0e-8 for row in levels),
        "factor2_factor3_power_convergence_gate": comparison["factor2_factor3_power_difference"] <= 0.01,
        "factor2_factor3_rise_convergence_gate": comparison["factor2_factor3_rise_difference"] <= 0.01,
        "factor3_comsol_power_gate": comparison["factor3_comsol_power_difference"] <= 0.05,
        "factor3_comsol_rise_gate": comparison["factor3_comsol_rise_difference"] <= 0.05,
        "factor3_comsol_current_gate": comparison["factor3_comsol_current_difference"] <= 0.05,
        "joule_centroid_gate": comparison["joule_centroid_distance_um"] <= 24.0,
        "temperature_centroid_gate": comparison["temperature_centroid_distance_um"] <= 24.0,
    }
    decision = "fvm_refinement_pass" if all(gates.values()) else "review"
    result = {
        "decision": decision,
        "original_loading_decision": "review",
        "levels": levels,
        "comparison": comparison,
        "centroids": centroids,
        "gates": gates,
        "interpretation_boundary": (
            "This diagnostic refines only the open verifier against the frozen COMSOL/property inputs. "
            "It does not change the original preregistered loading-mode review decision."
        ),
    }
    output = evidence_dir / "comparison"
    output.mkdir(parents=True, exist_ok=True)
    (output / "fvm_refinement_summary.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    _write_report(output / "report.md", result)
    _plot(
        output / "fvm_refinement_and_hotspot.png",
        levels,
        xs_um,
        ys_um,
        comsol_q,
        fvm_q,
        centroids["comsol_joule"],
        centroids["fvm_joule"],
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refine the open FVM for the failing multiplier-1 case")
    parser.add_argument("source_property_grid", type=Path)
    parser.add_argument("prepared_dir", type=Path)
    parser.add_argument("evidence_dir", type=Path)
    parser.add_argument("comsol_summary", type=Path)
    parser.add_argument("comsol_fields", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = analyze(
        args.source_property_grid,
        args.prepared_dir,
        args.evidence_dir,
        args.comsol_summary,
        args.comsol_fields,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
