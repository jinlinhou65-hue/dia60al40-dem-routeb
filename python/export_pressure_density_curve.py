from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

from dem_stage_metadata import (
    UM_PER_CM,
    W_UM,
    contact_counts,
    read_liggghts_dump,
    stages_from_model_parameters,
    total_particle_area_um2,
)

T_CM = 0.0090
UM_TO_CM = 1.0e-4


FIELDNAMES = [
    "stage_id",
    "target_rho_total",
    "actual_rho_total",
    "current_height_um",
    "top_displacement_um",
    "al_modulus_gpa",
    "top_force_y_dyne",
    "top_force_n",
    "pressure_mpa",
    "bottom_force_y_dyne",
    "bottom_pressure_mpa",
    "left_force_x_dyne",
    "left_pressure_mpa",
    "right_force_x_dyne",
    "right_pressure_mpa",
    "avg_contact_count",
    "max_contact_count",
    "max_overlap_um",
    "max_overlap_ratio",
    "worst_overlap_pair",
]


def fmt(value: float) -> str:
    return f"{value:.9g}"


def read_macro_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return {row["stage_id"]: row for row in csv.DictReader(f)}


def latest_stage_dump(root: Path, stage_id: str) -> Path:
    matches = sorted(root.glob(f"{stage_id}_*.dump"))
    if not matches:
        raise SystemExit(f"[FAIL] no dump found for stage_id={stage_id} under {root}")
    return matches[-1]


def overlap_summary(rows: list[dict[str, str]]) -> tuple[float, float, str]:
    worst_gap = 0.0
    worst_pair = "-"
    min_radius = min((float(row["radius"]) * UM_PER_CM for row in rows), default=0.0)
    for i, a in enumerate(rows):
        ax = float(a["x"]) * UM_PER_CM
        ay = float(a["y"]) * UM_PER_CM
        ar = float(a["radius"]) * UM_PER_CM
        aid = str(a.get("id", i + 1))
        for j, b in enumerate(rows[i + 1 :], start=i + 1):
            bx = float(b["x"]) * UM_PER_CM
            by = float(b["y"]) * UM_PER_CM
            br = float(b["radius"]) * UM_PER_CM
            bid = str(b.get("id", j + 1))
            gap = math.hypot(ax - bx, ay - by) - (ar + br)
            if gap < worst_gap:
                worst_gap = gap
                worst_pair = f"{aid}-{bid}"
    max_overlap = max(0.0, -worst_gap)
    ratio = max_overlap / min_radius if min_radius > 0.0 else 0.0
    return max_overlap, ratio, worst_pair


def raw_float(row: dict[str, str], key: str, default: float = 0.0) -> float:
    value = row.get(key, "")
    return default if value == "" else float(value)


def side_pressure_mpa(force_dyne: float, current_height_um: float) -> float:
    side_area_cm2 = current_height_um * UM_TO_CM * T_CM
    return abs(force_dyne) / side_area_cm2 * 1.0e-7 if side_area_cm2 > 0.0 else 0.0


def export_curve(root: Path, raw_path: Path, output_path: Path, contact_gap_um: float) -> None:
    raw_by_stage = read_macro_rows(raw_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()

        for stage_id, target_rho, current_height_um, _, _ in stages_from_model_parameters(root):
            if stage_id not in raw_by_stage:
                raise SystemExit(f"[FAIL] {raw_path} is missing force row for {stage_id}")

            dump = latest_stage_dump(root, stage_id)
            rows = read_liggghts_dump(dump)
            actual_rho = total_particle_area_um2(rows) / (W_UM * current_height_um)
            counts = contact_counts(rows, contact_gap_um)
            count_values = list(counts.values())
            avg_contact = sum(count_values) / len(count_values) if count_values else 0.0
            max_contact = max(count_values) if count_values else 0
            max_overlap_um, max_overlap_ratio, worst_pair = overlap_summary(rows)

            raw = raw_by_stage[stage_id]
            al_modulus_gpa = raw_float(raw, "al_modulus_gpa", float("nan"))
            top_force_y_dyne = float(raw["top_force_y_dyne"])
            top_force_n = abs(top_force_y_dyne) * 1.0e-5
            pressure_mpa = float(raw["pressure_mpa"])
            bottom_force_y_dyne = raw_float(raw, "bottom_force_y_dyne")
            bottom_pressure_mpa = raw_float(raw, "bottom_pressure_mpa")
            left_force_x_dyne = raw_float(raw, "left_force_x_dyne")
            right_force_x_dyne = raw_float(raw, "right_force_x_dyne")
            left_pressure_mpa = side_pressure_mpa(left_force_x_dyne, current_height_um)
            right_pressure_mpa = side_pressure_mpa(right_force_x_dyne, current_height_um)

            writer.writerow(
                {
                    "stage_id": stage_id,
                    "target_rho_total": fmt(target_rho),
                    "actual_rho_total": fmt(actual_rho),
                    "current_height_um": fmt(current_height_um),
                    "top_displacement_um": raw["top_displacement_um"],
                    "al_modulus_gpa": fmt(al_modulus_gpa),
                    "top_force_y_dyne": fmt(top_force_y_dyne),
                    "top_force_n": fmt(top_force_n),
                    "pressure_mpa": fmt(pressure_mpa),
                    "bottom_force_y_dyne": fmt(bottom_force_y_dyne),
                    "bottom_pressure_mpa": fmt(bottom_pressure_mpa),
                    "left_force_x_dyne": fmt(left_force_x_dyne),
                    "left_pressure_mpa": fmt(left_pressure_mpa),
                    "right_force_x_dyne": fmt(right_force_x_dyne),
                    "right_pressure_mpa": fmt(right_pressure_mpa),
                    "avg_contact_count": fmt(avg_contact),
                    "max_contact_count": max_contact,
                    "max_overlap_um": fmt(max_overlap_um),
                    "max_overlap_ratio": fmt(max_overlap_ratio),
                    "worst_overlap_pair": worst_pair,
                }
            )

    print(f"[OK] wrote {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="liggghts/DEM")
    parser.add_argument("--raw", default="liggghts/DEM/pressure_density_curve_raw.csv")
    parser.add_argument("--output", default="liggghts/DEM/pressure_density_curve.csv")
    parser.add_argument(
        "--contact-gap-um",
        type=float,
        default=0.5,
        help="Count a particle pair as contacting when projected surface gap <= this value.",
    )
    args = parser.parse_args()

    export_curve(Path(args.root), Path(args.raw), Path(args.output), args.contact_gap_um)


if __name__ == "__main__":
    main()
