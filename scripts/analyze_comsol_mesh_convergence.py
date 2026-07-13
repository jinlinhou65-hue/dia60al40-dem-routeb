from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path

import matplotlib.pyplot as plt


LEVELS = ("coarse", "medium", "fine")


def relative_difference(a: float, b: float) -> float:
    return abs(a - b) / max((abs(a) + abs(b)) / 2.0, 1.0e-30)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _extract_int(text: str, patterns: tuple[str, ...], label: str) -> int:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.MULTILINE | re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))
    raise ValueError(f"COMSOL log does not contain {label}")


def _extract_float(text: str, patterns: tuple[str, ...], label: str) -> float:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.MULTILINE | re.IGNORECASE)
        if match:
            return float(match.group(1))
    raise ValueError(f"COMSOL log does not contain {label}")


def parse_comsol_log(text: str) -> dict[str, float | int | bool]:
    element_count = _extract_int(
        text,
        (r"^\s*单元数[：:]\s*([\d,]+)\s*$", r"^\s*Number of elements[：:]\s*([\d,]+)\s*$"),
        "element count",
    )
    minimum_quality = _extract_float(
        text,
        (
            r"^\s*最小单元质量[：:]\s*([0-9.eE+-]+)\s*$",
            r"^\s*Minimum element quality[：:]\s*([0-9.eE+-]+)\s*$",
        ),
        "minimum element quality",
    )
    dof_count = _extract_int(
        text,
        (
            r"求解的自由度数[：:]\s*([\d,]+)",
            r"Number of degrees of freedom solved for[：:]\s*([\d,]+)",
        ),
        "degree-of-freedom count",
    )
    has_error = any(
        marker in text
        for marker in ("运行 Java 类时出错", "Error running Java class", "*****错误", "Exception")
    )
    return {
        "element_count": element_count,
        "minimum_element_quality": minimum_quality,
        "dof_count": dof_count,
        "log_error": has_error,
    }


def read_level(root: Path, level: str) -> dict[str, object]:
    directory = root / level
    summary_path = directory / "comsol_summary.json"
    log_path = directory / "comsol_batch.log"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    log_metrics = parse_comsol_log(log_path.read_text(encoding="utf-8", errors="replace"))
    ambient = float(summary.get("ambient_temperature_k", 293.15))
    return {
        "level": level,
        "mesh_hmax_um": float(summary["mesh_hmax_um"]),
        "mesh_hmin_um": float(summary["mesh_hmin_um"]),
        "element_count": int(log_metrics["element_count"]),
        "minimum_element_quality": float(log_metrics["minimum_element_quality"]),
        "dof_count": int(log_metrics["dof_count"]),
        "integrated_joule_2d_w_per_m_depth": float(summary["integrated_joule_2d_w_per_m_depth"]),
        "max_temperature_k": float(summary["max_temperature_k"]),
        "max_temperature_rise_k": float(summary["max_temperature_k"]) - ambient,
        "solve_status": summary.get("solve_status"),
        "log_error": bool(log_metrics["log_error"]),
        "summary_sha256": file_sha256(summary_path),
        "log_sha256": file_sha256(log_path),
    }


def analyze(root: Path, output_dir: Path) -> dict[str, object]:
    rows = [read_level(root, level) for level in LEVELS]
    coarse, medium, fine = rows
    power_medium_fine = relative_difference(
        float(medium["integrated_joule_2d_w_per_m_depth"]),
        float(fine["integrated_joule_2d_w_per_m_depth"]),
    )
    rise_medium_fine = relative_difference(
        float(medium["max_temperature_rise_k"]), float(fine["max_temperature_rise_k"])
    )
    power_coarse_fine = relative_difference(
        float(coarse["integrated_joule_2d_w_per_m_depth"]),
        float(fine["integrated_joule_2d_w_per_m_depth"]),
    )
    rise_coarse_fine = relative_difference(
        float(coarse["max_temperature_rise_k"]), float(fine["max_temperature_rise_k"])
    )
    finite_keys = (
        "mesh_hmax_um",
        "mesh_hmin_um",
        "minimum_element_quality",
        "integrated_joule_2d_w_per_m_depth",
        "max_temperature_k",
        "max_temperature_rise_k",
    )
    gates = {
        "all_solve_success_gate": all(row["solve_status"] == "success" for row in rows),
        "clean_log_gate": all(not row["log_error"] for row in rows),
        "finite_positive_result_gate": all(
            all(math.isfinite(float(row[key])) for key in finite_keys)
            and float(row["integrated_joule_2d_w_per_m_depth"]) > 0.0
            and float(row["max_temperature_rise_k"]) > 0.0
            for row in rows
        ),
        "refinement_order_gate": all(
            float(rows[index]["mesh_hmax_um"]) > float(rows[index + 1]["mesh_hmax_um"])
            for index in range(len(rows) - 1)
        ),
        "element_growth_gate": all(
            int(rows[index]["element_count"]) < int(rows[index + 1]["element_count"])
            for index in range(len(rows) - 1)
        ),
        "minimum_quality_gate": all(float(row["minimum_element_quality"]) >= 0.2 for row in rows),
        "medium_fine_power_gate": power_medium_fine <= 0.01,
        "medium_fine_temperature_gate": rise_medium_fine <= 0.01,
        "coarse_fine_power_gate": power_coarse_fine <= 0.03,
        "coarse_fine_temperature_gate": rise_coarse_fine <= 0.03,
    }
    decision = "mesh_pass" if all(gates.values()) else "review"
    result: dict[str, object] = {
        "decision": decision,
        "mesh_levels": rows,
        "comparisons": {
            "medium_fine_power_relative_difference": power_medium_fine,
            "medium_fine_temperature_rise_relative_difference": rise_medium_fine,
            "coarse_fine_power_relative_difference": power_coarse_fine,
            "coarse_fine_temperature_rise_relative_difference": rise_coarse_fine,
        },
        "gates": gates,
        "interpretation_boundary": (
            "Mesh convergence is evaluated for the fixed homogenized smoke model only; "
            "it does not calibrate contact resistance or material properties."
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "mesh_convergence_summary.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    write_csv(output_dir / "mesh_convergence.csv", rows)
    write_acceptance(output_dir / "acceptance.csv", gates, decision)
    write_report(output_dir / "report.md", result)
    write_figure(output_dir / "mesh_convergence.png", rows)
    return result


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_acceptance(path: Path, gates: dict[str, bool], decision: str) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([*gates, "decision"])
        writer.writerow([*("pass" if value else "fail" for value in gates.values()), decision])


def write_report(path: Path, result: dict[str, object]) -> None:
    rows = result["mesh_levels"]
    comparisons = result["comparisons"]
    lines = [
        "# Stage 04 COMSOL Mesh Convergence Report",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "| Level | hmax (um) | hmin (um) | Elements | DOF | Min quality | Joule power (W/m) | Max rise (K) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['level']} | {row['mesh_hmax_um']:.3f} | {row['mesh_hmin_um']:.3f} | "
            f"{row['element_count']} | {row['dof_count']} | {row['minimum_element_quality']:.4f} | "
            f"{row['integrated_joule_2d_w_per_m_depth']:.6f} | {row['max_temperature_rise_k']:.6f} |"
        )
    lines.extend(
        [
            "",
            f"- Medium/fine Joule-power difference: `{comparisons['medium_fine_power_relative_difference']:.3%}`.",
            f"- Medium/fine maximum-rise difference: `{comparisons['medium_fine_temperature_rise_relative_difference']:.3%}`.",
            f"- Coarse/fine Joule-power difference: `{comparisons['coarse_fine_power_relative_difference']:.3%}`.",
            f"- Coarse/fine maximum-rise difference: `{comparisons['coarse_fine_temperature_rise_relative_difference']:.3%}`.",
            "",
            "## Boundary",
            "",
            str(result["interpretation_boundary"]),
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_figure(path: Path, rows: list[dict[str, object]]) -> None:
    elements = [int(row["element_count"]) for row in rows]
    powers = [float(row["integrated_joule_2d_w_per_m_depth"]) for row in rows]
    rises = [float(row["max_temperature_rise_k"]) for row in rows]
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.8), constrained_layout=True)
    axes[0].plot(elements, powers, marker="o", color="#35618f")
    axes[0].set(xlabel="Triangular elements", ylabel="Joule power (W/m depth)", title="Energy convergence")
    axes[1].plot(elements, rises, marker="o", color="#c84d3a")
    axes[1].set(xlabel="Triangular elements", ylabel="Maximum temperature rise (K)", title="Thermal convergence")
    for axis in axes:
        axis.grid(alpha=0.25)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze three-level COMSOL mesh convergence")
    parser.add_argument("mesh_evidence_root", type=Path)
    parser.add_argument("output_dir", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = analyze(args.mesh_evidence_root, args.output_dir)
    print(json.dumps(result, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
