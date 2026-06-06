from __future__ import annotations

import argparse
import csv
from pathlib import Path


UM_PER_CM = 10000.0


def read_params(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
        return {row["parameter"]: row["value"] for row in csv.DictReader(fh) if row.get("parameter")}


def read_dump(path: Path) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    try:
        atoms_i = next(i for i, line in enumerate(lines) if line.startswith("ITEM: ATOMS"))
    except StopIteration:
        raise SystemExit(f"[FAIL] no ITEM: ATOMS section in {path}")
    cols = lines[atoms_i].split()[2:]
    rows = []
    for line in lines[atoms_i + 1 :]:
        if not line.strip() or line.startswith("ITEM:"):
            break
        vals = line.split()
        if len(vals) >= len(cols):
            rows.append(dict(zip(cols, vals)))
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--params", default=None)
    ap.add_argument("--expect-count", type=int, default=None)
    ap.add_argument("--diameter-um", type=float, default=None)
    ap.add_argument("--diameter-tol-um", type=float, default=1.0e-3)
    args = ap.parse_args()

    params = read_params(Path(args.params)) if args.params else {}
    expect_count = args.expect_count or int(float(params.get("particle_count", "2000")))
    diameter_um = args.diameter_um or float(params.get("particle_diameter_um", "30"))
    die_diameter_um = float(params.get("die_diameter_um", "450"))

    rows = read_dump(Path(args.input))
    type_counts: dict[int, int] = {}
    for row in rows:
        typ = int(float(row["type"]))
        type_counts[typ] = type_counts.get(typ, 0) + 1

    got = type_counts.get(1, 0)
    print(f"[VERIFY] particles={len(rows)} alumina_type1={got}")
    if got != expect_count:
        raise SystemExit(f"[FAIL] alumina count got {got}, expected {expect_count}")
    if len(rows) != expect_count:
        raise SystemExit(f"[FAIL] dump has non-alumina atoms or missing rows: rows={len(rows)} expected={expect_count}")

    radii_um = [float(row["radius"]) * UM_PER_CM for row in rows]
    min_d = min(radii_um) * 2.0
    max_d = max(radii_um) * 2.0
    print(f"[VERIFY] diameter range {min_d:.9g}..{max_d:.9g} um")
    if abs(min_d - diameter_um) > args.diameter_tol_um or abs(max_d - diameter_um) > args.diameter_tol_um:
        raise SystemExit(f"[FAIL] particle diameter not {diameter_um} um within {args.diameter_tol_um} um")

    die_radius_um = die_diameter_um * 0.5
    worst_radial_um = max((float(row["x"]) ** 2 + float(row["y"]) ** 2) ** 0.5 * UM_PER_CM + float(row["radius"]) * UM_PER_CM for row in rows)
    z_min_um = min(float(row["z"]) * UM_PER_CM - float(row["radius"]) * UM_PER_CM for row in rows)
    print(f"[VERIFY] radial envelope={worst_radial_um:.6g} um die_radius={die_radius_um:.6g} um z_min={z_min_um:.6g} um")
    if worst_radial_um > die_radius_um + 2.0:
        raise SystemExit("[FAIL] particle envelope exceeds die radius")
    if z_min_um < -2.0:
        raise SystemExit("[FAIL] particles leaked below bottom punch")

    print("[OK] 3D alumina DEM dump matches count, size, and die bounds")


if __name__ == "__main__":
    main()
