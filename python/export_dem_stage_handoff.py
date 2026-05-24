"""Export one LIGGGHTS stage dump into a DEM-FEM handoff CSV.

This file is intentionally richer than the legacy COMSOL geometry CSV. It keeps
stage identity, target density, current die height, particle material/shape,
velocity, an explicit rotation column, and a geometric contact-count estimate.

Current LIGGGHTS deck uses spherical DEM particles. Therefore `rotation_rad` is
0.0 by construction: there is no persistent octagon orientation in the dump.
If the DEM model later moves to clumps/superquadrics or dumps angular state,
this column is the stable place to pass that orientation into COMSOL.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from dem_stage_metadata import (
    STAGE_BY_ID,
    UM_PER_CM,
    contact_counts,
    particle_material,
    particle_shape,
    read_liggghts_dump,
    total_particle_area_um2,
)


FIELDNAMES = [
    "stage_id",
    "target_rho_total",
    "actual_rho_total",
    "current_height_um",
    "particle_id",
    "type",
    "shape",
    "material",
    "x_um",
    "y_um",
    "r_um",
    "rotation_rad",
    "vx_cm_s",
    "vy_cm_s",
    "contact_count",
]


def fmt(value: float) -> str:
    return f"{value:.9g}"


def export_stage(input_path: Path, stage_id: str, output_path: Path, contact_gap_um: float) -> None:
    if stage_id not in STAGE_BY_ID:
        known = ", ".join(STAGE_BY_ID)
        raise SystemExit(f"[FAIL] unknown stage_id={stage_id}; known stages: {known}")

    _, target_rho, current_height_um, _, _ = STAGE_BY_ID[stage_id]
    rows = read_liggghts_dump(input_path)
    actual_rho = total_particle_area_um2(rows) / (400.0 * current_height_um)
    counts = contact_counts(rows, contact_gap_um)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for index, row in enumerate(rows, start=1):
            particle_id = str(row.get("id", index))
            writer.writerow(
                {
                    "stage_id": stage_id,
                    "target_rho_total": fmt(target_rho),
                    "actual_rho_total": fmt(actual_rho),
                    "current_height_um": fmt(current_height_um),
                    "particle_id": particle_id,
                    "type": int(float(row["type"])),
                    "shape": particle_shape(row),
                    "material": particle_material(row),
                    "x_um": fmt(float(row["x"]) * UM_PER_CM),
                    "y_um": fmt(float(row["y"]) * UM_PER_CM),
                    "r_um": fmt(float(row["radius"]) * UM_PER_CM),
                    "rotation_rad": "0.0",
                    "vx_cm_s": fmt(float(row.get("vx", 0.0))),
                    "vy_cm_s": fmt(float(row.get("vy", 0.0))),
                    "contact_count": counts.get(particle_id, 0),
                }
            )
    print(f"[OK] wrote {output_path} rows={len(rows)} stage_id={stage_id} actual_rho_total={actual_rho:.6f}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--stage-id", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--contact-gap-um",
        type=float,
        default=0.5,
        help="Count another particle as a contact if projected surface gap <= this value.",
    )
    args = parser.parse_args()

    export_stage(Path(args.input), args.stage_id, Path(args.output), args.contact_gap_um)


if __name__ == "__main__":
    main()
