from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

from dem_stage_metadata import (
    STAGE_BY_ID,
    UM_PER_CM,
    W_UM,
    contact_counts,
    read_liggghts_dump,
    total_particle_area_um2,
)


FIELDNAMES = [
    "stage_id",
    "target_rho_total",
    "actual_rho_total",
    "current_height_um",
    "top_displacement_um",
    "top_force_y_dyne",
    "top_force_n",
    "pressure_mpa",
    "avg_contact_count",
    "max_contact_count",
    "max_overlap_um",
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


def overlap_summary(rows: list[dict[str, str]]) -> tuple[float, str]:
    worst_gap = 0.0
    worst_pair = "-"
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
    return max(0.0, -worst_gap), worst_pair


def export_curve(root: Path, raw_path: Path, output_path: Path, contact_gap_um: float) -> None:
    raw_by_stage = read_macro_rows(raw_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()

        for stage_id, target_rho, current_height_um, _, _ in STAGE_BY_ID.values():
            if stage_id not in raw_by_stage:
                raise SystemExit(f"[FAIL] {raw_path} is missing force row for {stage_id}")

            dump = latest_stage_dump(root, stage_id)
            rows = read_liggghts_dump(dump)
            actual_rho = total_particle_area_um2(rows) / (W_UM * current_height_um)
            counts = contact_counts(rows, contact_gap_um)
            count_values = list(counts.values())
            avg_contact = sum(count_values) / len(count_values) if count_values else 0.0
            max_contact = max(count_values) if count_values else 0
            max_overlap_um, worst_pair = overlap_summary(rows)

            raw = raw_by_stage[stage_id]
            top_force_y_dyne = float(raw["top_force_y_dyne"])
            top_force_n = abs(top_force_y_dyne) * 1.0e-5
            pressure_mpa = float(raw["pressure_mpa"])

            writer.writerow(
                {
                    "stage_id": stage_id,
                    "target_rho_total": fmt(target_rho),
                    "actual_rho_total": fmt(actual_rho),
                    "current_height_um": fmt(current_height_um),
                    "top_displacement_um": raw["top_displacement_um"],
                    "top_force_y_dyne": fmt(top_force_y_dyne),
                    "top_force_n": fmt(top_force_n),
                    "pressure_mpa": fmt(pressure_mpa),
                    "avg_contact_count": fmt(avg_contact),
                    "max_contact_count": max_contact,
                    "max_overlap_um": fmt(max_overlap_um),
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
