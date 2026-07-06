from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import RegularGridInterpolator


def read_comsol_fields(path: Path) -> dict[str, np.ndarray]:
    header: list[str] | None = None
    rows: list[list[float]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("% x,"):
                header = next(csv.reader([line[2:]]))
                continue
            if line.startswith("%"):
                continue
            rows.append([float(value) for value in next(csv.reader([line]))])
    if header is None or not rows:
        raise ValueError("COMSOL field export has no header or data")
    data = np.asarray(rows, dtype=float)
    if data.shape[1] != len(header):
        raise ValueError("COMSOL field export column count does not match header")
    if not np.all(np.isfinite(data)):
        raise ValueError("COMSOL field export contains non-finite values")
    return {
        "x_um": data[:, 0],
        "y_um": data[:, 1],
        "voltage_v": data[:, 2],
        "temperature_k": data[:, 3],
        "current_density_a_m2": data[:, 4],
        "joule_w_m3": data[:, 5],
    }


def read_fvm_fields(path: Path) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    xs = np.array(sorted({float(row["x_um"]) for row in rows}))
    ys = np.array(sorted({float(row["y_um"]) for row in rows}))
    index = {(float(row["x_um"]), float(row["y_um"])): row for row in rows}
    fields: dict[str, np.ndarray] = {}
    for name in ("voltage_v", "temperature_k"):
        array = np.empty((len(ys), len(xs)), dtype=float)
        for iy, y in enumerate(ys):
            for ix, x in enumerate(xs):
                array[iy, ix] = float(index[(x, y)][name])
        fields[name] = array
    return xs, ys, fields


def relative_difference(a: float, b: float) -> float:
    return abs(a - b) / max((abs(a) + abs(b)) / 2.0, 1.0e-30)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def analyze(
    comsol_summary_path: Path,
    comsol_fields_path: Path,
    comsol_log_path: Path,
    fvm_summary_path: Path,
    fvm_fields_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    comsol_summary = json.loads(comsol_summary_path.read_text(encoding="utf-8"))
    fvm_summary = json.loads(fvm_summary_path.read_text(encoding="utf-8"))
    comsol = read_comsol_fields(comsol_fields_path)
    fvm_x, fvm_y, fvm = read_fvm_fields(fvm_fields_path)
    log_text = comsol_log_path.read_text(encoding="utf-8", errors="replace")

    points = np.column_stack((comsol["y_um"], comsol["x_um"]))
    fvm_voltage = RegularGridInterpolator((fvm_y, fvm_x), fvm["voltage_v"])(points)
    fvm_temperature = RegularGridInterpolator((fvm_y, fvm_x), fvm["temperature_k"])(points)
    applied_voltage = float(fvm_summary["applied_voltage_v"])
    ambient = float(fvm_summary["ambient_temperature_k"])
    comsol_rise = float(comsol_summary["max_temperature_k"]) - ambient
    fvm_rise = float(fvm_summary["temperature_rise_max_k"])
    potential_nrmse = float(
        np.sqrt(np.mean((comsol["voltage_v"] - fvm_voltage) ** 2)) / applied_voltage
    )
    temperature_rise_nrmse = float(
        np.sqrt(np.mean((comsol["temperature_k"] - fvm_temperature) ** 2))
        / max(comsol_rise, fvm_rise)
    )
    power_relative_difference = relative_difference(
        float(comsol_summary["integrated_joule_2d_w_per_m_depth"]),
        float(fvm_summary["electric_power_w_per_m_depth"]),
    )
    max_rise_relative_difference = relative_difference(comsol_rise, fvm_rise)

    gates = {
        "comsol_solve_gate": comsol_summary.get("solve_status") == "success",
        "log_error_gate": "运行 Java 类时出错" not in log_text and "*****错误" not in log_text,
        "finite_field_gate": all(np.all(np.isfinite(values)) for values in comsol.values()),
        "voltage_boundary_gate": math.isclose(float(np.min(comsol["voltage_v"])), 0.0, abs_tol=1.0e-9)
        and math.isclose(float(np.max(comsol["voltage_v"])), applied_voltage, abs_tol=1.0e-9),
        "positive_temperature_rise_gate": comsol_rise > 0.0,
        "joule_power_agreement_gate": power_relative_difference <= 0.05,
        "temperature_rise_agreement_gate": max_rise_relative_difference <= 0.05,
        "potential_field_agreement_gate": potential_nrmse <= 0.05,
        "temperature_field_agreement_gate": temperature_rise_nrmse <= 0.10,
    }
    decision = "smoke_pass" if all(gates.values()) else "review"
    summary: dict[str, object] = {
        "decision": decision,
        "model_fidelity": "mesoscale_smoke_model_not_particle_resolved",
        "comsol": {
            **comsol_summary,
            "field_node_count": len(comsol["x_um"]),
            "voltage_min_v": float(np.min(comsol["voltage_v"])),
            "voltage_max_v": float(np.max(comsol["voltage_v"])),
            "temperature_min_k": float(np.min(comsol["temperature_k"])),
            "temperature_max_export_k": float(np.max(comsol["temperature_k"])),
            "current_density_max_a_m2": float(np.max(comsol["current_density_a_m2"])),
            "joule_max_w_m3": float(np.max(comsol["joule_w_m3"])),
        },
        "fvm": fvm_summary,
        "comparison": {
            "joule_power_relative_difference": power_relative_difference,
            "max_temperature_rise_relative_difference": max_rise_relative_difference,
            "potential_nrmse_by_applied_voltage": potential_nrmse,
            "temperature_nrmse_by_max_rise": temperature_rise_nrmse,
        },
        "gates": gates,
        "evidence_sha256": {
            "comsol_summary": file_sha256(comsol_summary_path),
            "comsol_fields": file_sha256(comsol_fields_path),
            "comsol_log": file_sha256(comsol_log_path),
            "fvm_summary": file_sha256(fvm_summary_path),
            "fvm_fields": file_sha256(fvm_fields_path),
        },
        "interpretation_boundary": (
            "This proves a reproducible DEM-contact-to-electrothermal smoke route. "
            "It does not validate experimental conductivity, contact resistance, or particle-resolved fields."
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "comparison_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    write_acceptance(output_dir / "acceptance.csv", gates, decision)
    write_report(output_dir / "report.md", summary)
    write_figure(
        output_dir / "comsol_fvm_comparison.png",
        comsol,
        fvm_voltage,
        fvm_temperature,
        comsol_summary,
        fvm_summary,
    )
    return summary


def write_acceptance(path: Path, gates: dict[str, bool], decision: str) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([*gates.keys(), "decision"])
        writer.writerow([*("pass" if value else "fail" for value in gates.values()), decision])


def write_report(path: Path, summary: dict[str, object]) -> None:
    comsol = summary["comsol"]
    fvm = summary["fvm"]
    comparison = summary["comparison"]
    lines = [
        "# Stage 04 Electrothermal MVP Smoke Report",
        "",
        f"Decision: `{summary['decision']}`",
        "",
        "| Metric | COMSOL 6.4 | Open FVM | Relative difference |",
        "|---|---:|---:|---:|",
        (
            f"| Joule power (W/m depth) | {comsol['integrated_joule_2d_w_per_m_depth']:.6f} | "
            f"{fvm['electric_power_w_per_m_depth']:.6f} | "
            f"{comparison['joule_power_relative_difference']:.3%} |"
        ),
        (
            f"| Maximum temperature rise (K) | "
            f"{comsol['max_temperature_k'] - fvm['ambient_temperature_k']:.6f} | "
            f"{fvm['temperature_rise_max_k']:.6f} | "
            f"{comparison['max_temperature_rise_relative_difference']:.3%} |"
        ),
        "",
        f"- Potential field normalized RMSE: `{comparison['potential_nrmse_by_applied_voltage']:.6f}`.",
        f"- Temperature field normalized RMSE: `{comparison['temperature_nrmse_by_max_rise']:.6f}`.",
        f"- COMSOL exported field nodes: `{comsol['field_node_count']}`.",
        "- All gates require finite fields, correct voltage limits, a clean COMSOL log, and cross-solver agreement.",
        "",
        "## Boundary",
        "",
        str(summary["interpretation_boundary"]),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_figure(
    path: Path,
    comsol: dict[str, np.ndarray],
    fvm_voltage: np.ndarray,
    fvm_temperature: np.ndarray,
    comsol_summary: dict[str, object],
    fvm_summary: dict[str, object],
) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), constrained_layout=True)
    axes[0].scatter(fvm_voltage, comsol["voltage_v"], s=6, alpha=0.35)
    axes[0].plot([0, 0.1], [0, 0.1], color="black", linewidth=1)
    axes[0].set(xlabel="FVM potential (V)", ylabel="COMSOL potential (V)", title="Potential field")
    ambient = float(fvm_summary["ambient_temperature_k"])
    axes[1].scatter(fvm_temperature - ambient, comsol["temperature_k"] - ambient, s=6, alpha=0.35)
    rise_max = max(float(np.max(fvm_temperature - ambient)), float(np.max(comsol["temperature_k"] - ambient)))
    axes[1].plot([0, rise_max], [0, rise_max], color="black", linewidth=1)
    axes[1].set(xlabel="FVM temperature rise (K)", ylabel="COMSOL temperature rise (K)", title="Temperature field")
    powers = [
        float(comsol_summary["integrated_joule_2d_w_per_m_depth"]),
        float(fvm_summary["electric_power_w_per_m_depth"]),
    ]
    axes[2].bar(["COMSOL", "Open FVM"], powers, color=["#35618f", "#d17a3a"])
    axes[2].set(ylabel="Joule power (W/m depth)", title="Energy comparison")
    fig.savefig(path, dpi=180)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare COMSOL and open-FVM electrothermal MVP results")
    parser.add_argument("comsol_summary", type=Path)
    parser.add_argument("comsol_fields", type=Path)
    parser.add_argument("comsol_log", type=Path)
    parser.add_argument("fvm_summary", type=Path)
    parser.add_argument("fvm_fields", type=Path)
    parser.add_argument("output_dir", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = analyze(
        args.comsol_summary,
        args.comsol_fields,
        args.comsol_log,
        args.fvm_summary,
        args.fvm_fields,
        args.output_dir,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
