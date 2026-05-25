from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", default="liggghts/DEM/plastic_morphology_metrics.csv")
    parser.add_argument("--min-nonempty-fraction", type=float, default=0.95)
    parser.add_argument("--min-al-area-ratio", type=float, default=0.70)
    parser.add_argument("--max-al-area-ratio", type=float, default=1.03)
    args = parser.parse_args()

    path = Path(args.metrics)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        raise SystemExit(f"[FAIL] {path} is empty")

    nonempty = [row for row in rows if float(row["rendered_area_um2"]) > 1.0 and int(row["polygon_vertices"]) >= 3]
    fraction = len(nonempty) / len(rows)
    if fraction < args.min_nonempty_fraction:
        raise SystemExit(
            f"[FAIL] only {fraction:.3f} of morphology particles have nonempty polygons; "
            f"required {args.min_nonempty_fraction:.3f}"
        )

    stage_ids = sorted(set(row["stage_id"] for row in rows))
    print("[MORPH VERIFY] nonempty_fraction={:.3f} rows={}".format(fraction, len(rows)))
    for stage_id in stage_ids:
        stage_rows = [row for row in rows if row["stage_id"] == stage_id]
        al_flat = [float(row["flattening"]) for row in stage_rows if row["material"] == "Al"]
        dia_flat = [float(row["flattening"]) for row in stage_rows if row["material"] == "Diamond"]
        al_nominal = sum(float(row["nominal_area_um2"]) for row in stage_rows if row["material"] == "Al")
        al_rendered = sum(float(row["rendered_area_um2"]) for row in stage_rows if row["material"] == "Al")
        al_area_ratio = al_rendered / al_nominal if al_nominal > 0.0 else math.nan
        if not (args.min_al_area_ratio <= al_area_ratio <= args.max_al_area_ratio):
            raise SystemExit(
                f"[FAIL] {stage_id} Al rendered/nominal area ratio={al_area_ratio:.6g} outside "
                f"[{args.min_al_area_ratio},{args.max_al_area_ratio}]"
            )
        print(
            "[MORPH VERIFY] {} max_flat_Al={:.6g} max_flat_Diamond={:.6g} "
            "Al_area_ratio={:.6g}".format(
                stage_id,
                max(al_flat) if al_flat else 0.0,
                max(dia_flat) if dia_flat else 0.0,
                al_area_ratio,
            )
        )


if __name__ == "__main__":
    main()
