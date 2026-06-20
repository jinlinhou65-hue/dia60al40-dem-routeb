"""Summarize DEM particle-count refinement feasibility risks.

The Zhang reproduction uses 2D LIGGGHTS spheres as a fast surrogate for the
paper-scale diamond/Al bed. The case geometry keeps the paper-facing diamond
area as octagons, while the DEM solver still inserts circular particles. This
diagnostic makes that approximation explicit before expensive workflow runs.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = REPO_ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from dem_case_config import DIAMOND_CASES, RHO_STAGES, W_UM, DiamondCase, refined_diamond_case
from dem_case_geometry import al_count, initial_die_height_um, stage0_height_um, total_solid_area_um2


INSERT_MARGIN_UM = 13.0


def circle_area(radius_um: float) -> float:
    return math.pi * radius_um * radius_um


def actual_dem_disk_area(case: DiamondCase) -> float:
    return (
        al_count(case) * circle_area(case.al_dem_um)
        + case.ds_count * circle_area(case.ds_dem_um)
        + case.dl_count * circle_area(case.dl_dem_um)
    )


def parse_scales(raw: str) -> list[int]:
    scales = [int(part.strip()) for part in raw.split(",") if part.strip()]
    if not scales:
        raise SystemExit("[FAIL] at least one particle-count scale is required")
    if any(scale < 1 for scale in scales):
        raise SystemExit("[FAIL] particle-count scales must be >= 1")
    return scales


def risk_flags(row: dict[str, float | int | str]) -> str:
    flags: list[str] = []
    if float(row["stage5_disk_packing_fraction"]) >= 1.0:
        flags.append("final_disk_packing_ge_1")
    if float(row["insert_region_disk_packing_fraction"]) >= 0.50:
        flags.append("crowded_initial_insert_region")
    if float(row["largest_diameter_to_stage5_height"]) >= 0.30:
        flags.append("large_particle_spans_final_height")
    return ";".join(flags) or "none"


def build_rows(cases: list[str], scales: list[int]) -> list[dict[str, float | int | str]]:
    rows: list[dict[str, float | int | str]] = []
    stage5_rho = RHO_STAGES[-1][1]
    for case_id in cases:
        base = DIAMOND_CASES[case_id]
        for scale in scales:
            case = refined_diamond_case(base, scale)
            modeled_area = total_solid_area_um2(case)
            disk_area = actual_dem_disk_area(case)
            initial_height = initial_die_height_um(case)
            stage0_height = stage0_height_um(case)
            stage5_height = modeled_area / (W_UM * stage5_rho)
            insert_width = W_UM - 2.0 * INSERT_MARGIN_UM
            y_max = max(INSERT_MARGIN_UM, initial_height - INSERT_MARGIN_UM)
            insert_height = max(0.0, y_max - INSERT_MARGIN_UM)
            insert_region_area = insert_width * insert_height
            largest_radius = max(case.al_dem_um, case.ds_dem_um, case.dl_dem_um)
            row: dict[str, float | int | str] = {
                "diamond_size_case": case.case_id,
                "particle_count_scale": scale,
                "al_count": al_count(case),
                "ds_count": case.ds_count,
                "dl_count": case.dl_count,
                "particle_count_total": al_count(case) + case.ds_count + case.dl_count,
                "al_radius_um": case.al_dem_um,
                "ds_radius_um": case.ds_dem_um,
                "dl_radius_um": case.dl_dem_um,
                "largest_radius_um": largest_radius,
                "initial_height_um": initial_height,
                "stage0_height_um": stage0_height,
                "stage5_height_um": stage5_height,
                "modeled_solid_area_um2": modeled_area,
                "actual_dem_disk_area_um2": disk_area,
                "stage5_modeled_rho": stage5_rho,
                "stage5_disk_packing_fraction": disk_area / (W_UM * stage5_height),
                "insert_region_disk_packing_fraction": disk_area / insert_region_area
                if insert_region_area > 0
                else float("inf"),
                "largest_diameter_to_stage5_height": (2.0 * largest_radius) / stage5_height,
            }
            row["risk_flags"] = risk_flags(row)
            rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict[str, float | int | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise SystemExit("[FAIL] no rows to write")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default="C,D,E")
    parser.add_argument("--particle-count-scales", default="1,2")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    cases = [part.strip().upper() for part in args.cases.split(",") if part.strip()]
    unknown = sorted(set(cases) - set(DIAMOND_CASES))
    if unknown:
        raise SystemExit(f"[FAIL] unknown diamond cases: {','.join(unknown)}")
    rows = build_rows(cases, parse_scales(args.particle_count_scales))

    if args.output:
        write_csv(Path(args.output), rows)

    writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    for row in rows:
        writer.writerow(row)


if __name__ == "__main__":
    main()
