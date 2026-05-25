"""Generate STL boundary meshes for the Dia60/Al40 quasi-2D DEM preload.

Coordinates are CGS centimeters for LIGGGHTS.
Physical cavity: 400 um wide x 220 um high x 90 um thick.
Meshes:
  - DieBox.stl: five fixed walls (left, right, bottom, front, back), open at top
  - DieLeft.stl / DieRight.stl / DieBottom.stl: separate stress-output walls
  - DieFrontBack.stl: quasi-2D front/back confinement
  - TopPlate.stl: moving upper plate at y=220 um
  - InsertFace.stl: injection plane just below the top opening
"""
from __future__ import annotations
from pathlib import Path

UM_TO_CM = 1e-4
W = 400 * UM_TO_CM      # x width
H = 220 * UM_TO_CM      # y height
T = 90 * UM_TO_CM       # z thickness: quasi-2D single layer with front/back confinement
WALL = 20 * UM_TO_CM
TOP_THICK = 18 * UM_TO_CM
OUT = Path(__file__).resolve().parents[1] / "liggghts" / "meshes"


def tri_normal(a, b, c):
    import math
    ux, uy, uz = b[0]-a[0], b[1]-a[1], b[2]-a[2]
    vx, vy, vz = c[0]-a[0], c[1]-a[1], c[2]-a[2]
    nx, ny, nz = uy*vz-uz*vy, uz*vx-ux*vz, ux*vy-uy*vx
    n = math.sqrt(nx*nx+ny*ny+nz*nz) or 1.0
    return nx/n, ny/n, nz/n


def write_stl(path: Path, name: str, tris):
    with path.open("w", encoding="ascii", newline="\n") as f:
        f.write(f"solid {name}\n")
        for a, b, c in tris:
            nx, ny, nz = tri_normal(a, b, c)
            f.write(f"  facet normal {nx:.9e} {ny:.9e} {nz:.9e}\n")
            f.write("    outer loop\n")
            for p in (a, b, c):
                f.write(f"      vertex {p[0]:.9e} {p[1]:.9e} {p[2]:.9e}\n")
            f.write("    endloop\n  endfacet\n")
        f.write(f"endsolid {name}\n")


def quad(p1, p2, p3, p4):
    return [(p1, p2, p3), (p1, p3, p4)]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # Coordinates: x width, y vertical/load direction, z thickness.
    x0, x1 = 0.0, W
    y0, y1 = 0.0, H
    z0, z1 = -T/2, T/2

    die = []
    left = []
    right = []
    bottom = []
    frontback = []
    # left wall inner surface x=0, outward normal into cavity roughly +x if vertex order chosen.
    left += quad((x0,y0,z0), (x0,y1,z0), (x0,y1,z1), (x0,y0,z1))
    # right wall x=W
    right += quad((x1,y0,z1), (x1,y1,z1), (x1,y1,z0), (x1,y0,z0))
    # bottom wall y=0
    bottom += quad((x0,y0,z1), (x1,y0,z1), (x1,y0,z0), (x0,y0,z0))
    # front/back confining planes z=+/-T/2
    frontback += quad((x0,y0,z0), (x1,y0,z0), (x1,y1,z0), (x0,y1,z0))
    frontback += quad((x1,y0,z1), (x0,y0,z1), (x0,y1,z1), (x1,y1,z1))
    die = left + right + bottom + frontback
    write_stl(OUT / "DieBox.stl", "DieBox", die)
    write_stl(OUT / "DieLeft.stl", "DieLeft", left)
    write_stl(OUT / "DieRight.stl", "DieRight", right)
    write_stl(OUT / "DieBottom.stl", "DieBottom", bottom)
    write_stl(OUT / "DieFrontBack.stl", "DieFrontBack", frontback)

    top = []
    # lower face of top plate at y=H; extended across cavity only.
    top += quad((x0,y1,z0), (x1,y1,z0), (x1,y1,z1), (x0,y1,z1))
    # optional upper face/sides to keep STL watertight-ish for readers.
    y2 = y1 + TOP_THICK
    top += quad((x0,y2,z1), (x1,y2,z1), (x1,y2,z0), (x0,y2,z0))
    top += quad((x0,y1,z0), (x0,y2,z0), (x0,y2,z1), (x0,y1,z1))
    top += quad((x1,y1,z1), (x1,y2,z1), (x1,y2,z0), (x1,y1,z0))
    top += quad((x0,y1,z1), (x0,y2,z1), (x1,y2,z1), (x1,y1,z1))
    top += quad((x1,y1,z0), (x1,y2,z0), (x0,y2,z0), (x0,y1,z0))
    write_stl(OUT / "TopPlate.stl", "TopPlate", top)

    # Injection face: a horizontal rectangle slightly below the open top.
    yi = y1 - 2 * UM_TO_CM
    insert = quad((x0,yi,z0), (x1,yi,z0), (x1,yi,z1), (x0,yi,z1))
    write_stl(OUT / "InsertFace.stl", "InsertFace", insert)

    for fn in [
        "DieBox.stl",
        "DieLeft.stl",
        "DieRight.stl",
        "DieBottom.stl",
        "DieFrontBack.stl",
        "TopPlate.stl",
        "InsertFace.stl",
    ]:
        p = OUT / fn
        print(f"[OK] {p} ({p.stat().st_size} bytes)")
    print(f"[UNITS] cm; W={W:g}, H={H:g}, T={T:g}")

if __name__ == "__main__":
    main()
