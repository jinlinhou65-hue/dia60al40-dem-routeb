from __future__ import annotations

import argparse
import math
from pathlib import Path


def write_ascii_stl(path: Path, name: str, triangles: list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(f"solid {name}\n")
        for a, b, c in triangles:
            fh.write("  facet normal 0 0 0\n")
            fh.write("    outer loop\n")
            for x, y, z in (a, b, c):
                fh.write(f"      vertex {x:.12g} {y:.12g} {z:.12g}\n")
            fh.write("    endloop\n")
            fh.write("  endfacet\n")
        fh.write(f"endsolid {name}\n")


def disk_triangles(radius_cm: float, z_cm: float, segments: int, flip: bool) -> list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]:
    tris = []
    center = (0.0, 0.0, z_cm)
    for i in range(segments):
        a0 = 2.0 * math.pi * i / segments
        a1 = 2.0 * math.pi * (i + 1) / segments
        p0 = (radius_cm * math.cos(a0), radius_cm * math.sin(a0), z_cm)
        p1 = (radius_cm * math.cos(a1), radius_cm * math.sin(a1), z_cm)
        tris.append((center, p1, p0) if flip else (center, p0, p1))
    return tris


def cylinder_side_triangles(radius_cm: float, height_cm: float, segments: int) -> list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]:
    tris = []
    z0 = 0.0
    z1 = height_cm
    for i in range(segments):
        a0 = 2.0 * math.pi * i / segments
        a1 = 2.0 * math.pi * (i + 1) / segments
        p00 = (radius_cm * math.cos(a0), radius_cm * math.sin(a0), z0)
        p01 = (radius_cm * math.cos(a1), radius_cm * math.sin(a1), z0)
        p10 = (radius_cm * math.cos(a0), radius_cm * math.sin(a0), z1)
        p11 = (radius_cm * math.cos(a1), radius_cm * math.sin(a1), z1)
        tris.append((p00, p01, p11))
        tris.append((p00, p11, p10))
    return tris


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="liggghts/alumina3d/meshes")
    ap.add_argument("--diameter-um", type=float, default=450.0)
    ap.add_argument("--height-um", type=float, default=600.0)
    ap.add_argument("--segments", type=int, default=96)
    args = ap.parse_args()

    if args.segments < 24:
        raise SystemExit("[FAIL] use at least 24 cylinder segments")
    outdir = Path(args.outdir)
    radius_cm = args.diameter_um * 0.5 * 1.0e-4
    height_cm = args.height_um * 1.0e-4

    write_ascii_stl(outdir / "DieCylinder.stl", "DieCylinder", cylinder_side_triangles(radius_cm, height_cm, args.segments))
    write_ascii_stl(outdir / "BottomPlate.stl", "BottomPlate", disk_triangles(radius_cm, 0.0, args.segments, flip=True))
    write_ascii_stl(outdir / "TopPunch.stl", "TopPunch", disk_triangles(radius_cm, height_cm, args.segments, flip=False))

    for path in (outdir / "DieCylinder.stl", outdir / "BottomPlate.stl", outdir / "TopPunch.stl"):
        if path.stat().st_size <= 0:
            raise SystemExit(f"[FAIL] empty mesh: {path}")
        print(f"[OK] {path} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
