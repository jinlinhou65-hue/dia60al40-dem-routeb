from __future__ import annotations
import argparse
from collections import Counter
from pathlib import Path
import math

UM_PER_CM = 10000.0


def read_liggghts_dump(path: str | Path):
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    try:
        atoms_i = next(i for i, line in enumerate(lines) if line.startswith("ITEM: ATOMS"))
    except StopIteration:
        raise SystemExit(f"[FAIL] no ITEM: ATOMS section in {path}")
    cols = lines[atoms_i].split()[2:]
    rows = []
    for line in lines[atoms_i + 1:]:
        if not line.strip() or line.startswith("ITEM:"):
            break
        vals = line.split()
        if len(vals) < len(cols):
            continue
        rows.append(dict(zip(cols, vals)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--expect-al", type=int, default=34)
    ap.add_argument("--expect-ds", type=int, default=8)
    ap.add_argument("--expect-dl", type=int, default=4)
    args = ap.parse_args()

    rows = read_liggghts_dump(args.input)
    counts = Counter()
    for row in rows:
        typ = int(float(row["type"]))
        rad_um = float(row["radius"]) * UM_PER_CM
        if typ == 1:
            counts["Al"] += 1
        elif typ == 2 and rad_um > 30.0:
            counts["DL"] += 1
        elif typ == 2:
            counts["DS"] += 1
        else:
            counts[f"type{typ}"] += 1

    print(f"[VERIFY] particles={len(rows)} Al={counts['Al']} DS={counts['DS']} DL={counts['DL']}")

    # Route-B is a 2D COMSOL model. The DEM handoff is only valid if all centers
    # are on the z=0 mid-plane and the x-y projection has no severe overlaps.
    zs_um = [float(r.get("z", 0.0)) * UM_PER_CM for r in rows]
    zmax = max(abs(z) for z in zs_um) if zs_um else 0.0
    print(f"[VERIFY] max|z|={zmax:.6g} um")
    if zmax > 0.05:
        print(f"[FAIL] projected 2D handoff invalid: max|z|={zmax:.6g} um > 0.05 um")
        raise SystemExit(1)

    severe = []
    for i, a in enumerate(rows):
        ax, ay, ar = float(a["x"])*UM_PER_CM, float(a["y"])*UM_PER_CM, float(a["radius"])*UM_PER_CM
        for b in rows[i+1:]:
            bx, by, br = float(b["x"])*UM_PER_CM, float(b["y"])*UM_PER_CM, float(b["radius"])*UM_PER_CM
            gap = math.hypot(ax-bx, ay-by) - (ar+br)
            if gap < -1.0:
                severe.append((gap, a.get("id", "?"), b.get("id", "?")))
    if severe:
        severe.sort()
        print(f"[FAIL] projected 2D severe overlaps={len(severe)} worst_gap_um={severe[0][0]:.6g} pair={severe[0][1]}-{severe[0][2]}")
        raise SystemExit(1)
    expected = {"Al": args.expect_al, "DS": args.expect_ds, "DL": args.expect_dl}
    bad = {k: (counts[k], v) for k, v in expected.items() if counts[k] != v}
    if bad:
        for k, (got, want) in bad.items():
            print(f"[FAIL] {k}: got {got}, expected {want}")
        raise SystemExit(1)
    print("[OK] DEM particle composition matches target 34 Al + 8 DS + 4 DL")


if __name__ == "__main__":
    main()
