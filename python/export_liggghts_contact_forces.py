"""Convert LIGGGHTS pair/gran/local contact dumps into stage contact CSVs."""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

from dem_stage_metadata import UM_PER_CM


FIELDNAMES = [
    "stage_id",
    "i",
    "j",
    "nx",
    "ny",
    "nz",
    "gap_um",
    "overlap_um",
    "force_x",
    "force_y",
    "force_z",
    "normal_force",
    "contact_point_x_um",
    "contact_point_y_um",
    "contact_point_z_um",
    "source",
    "force_unit",
]


def export_contacts(local_dump: Path, particles_csv: Path, stage_id: str, output_path: Path) -> None:
    particles = read_particles(particles_csv)
    rows = read_local_entries(local_dump)
    output_rows = [contact_row(row, particles, stage_id) for row in rows]
    output_rows = [row for row in output_rows if row is not None]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(output_rows)
    print(f"[OK] wrote {output_path} rows={len(output_rows)} source={local_dump}")


def read_particles(path: Path) -> dict[int, dict[str, float]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    particles: dict[int, dict[str, float]] = {}
    for row in rows:
        pid = int(float(row["particle_id"]))
        particles[pid] = {
            "x_um": float(row["x_um"]),
            "y_um": float(row["y_um"]),
            "z_um": float(row.get("z_um", 0.0)),
            "r_um": float(row["r_um"]),
        }
    return particles


def read_local_entries(path: Path) -> list[list[float]]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    try:
        entries_i = next(i for i, line in enumerate(lines) if line.startswith("ITEM: ENTRIES"))
    except StopIteration:
        raise SystemExit(f"[FAIL] no ITEM: ENTRIES section in {path}")
    rows: list[list[float]] = []
    for line in lines[entries_i + 1 :]:
        if not line.strip() or line.startswith("ITEM:"):
            break
        values = [float(value) for value in line.split()]
        if len(values) >= 13:
            rows.append(values)
    return rows


def contact_row(
    values: list[float],
    particles: dict[int, dict[str, float]],
    stage_id: str,
) -> dict[str, object] | None:
    i = int(values[0])
    j = int(values[1])
    a = particles.get(i)
    b = particles.get(j)
    if not a or not b:
        return None
    dx = b["x_um"] - a["x_um"]
    dy = b["y_um"] - a["y_um"]
    dz = b["z_um"] - a["z_um"]
    distance = math.sqrt(dx * dx + dy * dy + dz * dz)
    if distance == 0.0:
        return None
    nx = dx / distance
    ny = dy / distance
    nz = dz / distance
    force_x = values[3]
    force_y = values[4]
    force_z = values[5]
    normal_x = values[6]
    normal_y = values[7]
    normal_z = values[8]
    normal_force = math.sqrt(normal_x * normal_x + normal_y * normal_y + normal_z * normal_z)
    overlap_um = max(0.0, values[9] * UM_PER_CM)
    gap_um = distance - (a["r_um"] + b["r_um"])
    return {
        "stage_id": stage_id,
        "i": i,
        "j": j,
        "nx": format_float(nx),
        "ny": format_float(ny),
        "nz": format_float(nz),
        "gap_um": format_float(gap_um),
        "overlap_um": format_float(overlap_um),
        "force_x": format_float(force_x),
        "force_y": format_float(force_y),
        "force_z": format_float(force_z),
        "normal_force": format_float(normal_force),
        "contact_point_x_um": format_float(values[10] * UM_PER_CM),
        "contact_point_y_um": format_float(values[11] * UM_PER_CM),
        "contact_point_z_um": format_float(values[12] * UM_PER_CM),
        "source": "liggghts_pair_gran_local",
        "force_unit": "dyne",
    }


def format_float(value: float) -> str:
    return f"{value:.9g}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-dump", required=True)
    parser.add_argument("--particles", required=True)
    parser.add_argument("--stage-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    export_contacts(Path(args.local_dump), Path(args.particles), args.stage_id, Path(args.output))


if __name__ == "__main__":
    main()
