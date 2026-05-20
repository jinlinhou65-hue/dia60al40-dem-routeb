from __future__ import annotations
import argparse
from collections import Counter
from pathlib import Path

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
    expected = {"Al": args.expect_al, "DS": args.expect_ds, "DL": args.expect_dl}
    bad = {k: (counts[k], v) for k, v in expected.items() if counts[k] != v}
    if bad:
        for k, (got, want) in bad.items():
            print(f"[FAIL] {k}: got {got}, expected {want}")
        raise SystemExit(1)
    print("[OK] DEM particle composition matches target 34 Al + 8 DS + 4 DL")


if __name__ == "__main__":
    main()
