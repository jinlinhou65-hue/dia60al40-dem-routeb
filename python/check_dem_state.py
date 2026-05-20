from __future__ import annotations
import argparse, csv
from pathlib import Path


def read_dump(path: Path):
    lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
    atoms_i = next(i for i, line in enumerate(lines) if line.startswith('ITEM: ATOMS'))
    cols = lines[atoms_i].split()[2:]
    rows = []
    for line in lines[atoms_i + 1:]:
        if not line.strip() or line.startswith('ITEM:'):
            break
        vals = line.split()
        if len(vals) >= len(cols):
            rows.append(dict(zip(cols, vals)))
    return rows


def read_table(path: Path):
    with path.open(newline='') as f:
        sample = f.read(4096); f.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters=', \t')
        return list(csv.DictReader(f, dialect=dialect))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    args = ap.parse_args()
    p = Path(args.input)
    head = p.read_text(encoding='utf-8', errors='replace')[:128]
    rows = read_dump(p) if p.suffix.lower() == '.dump' or 'ITEM: TIMESTEP' in head else read_table(p)
    if not rows:
        raise SystemExit('[FAIL] no rows')
    xs = [float(r.get('x') or r.get('Points:0') or r.get('Points_0')) for r in rows]
    ys = [float(r.get('y') or r.get('Points:1') or r.get('Points_1')) for r in rows]
    rs = [float(r.get('radius') or r.get('Radius') or 0) for r in rows]
    print(f'[DEM] particles={len(rows)}')
    print(f'[DEM] x=[{min(xs):.6g},{max(xs):.6g}] cm y=[{min(ys):.6g},{max(ys):.6g}] cm')
    if any(rs):
        nz = [r for r in rs if r]
        print(f'[DEM] radius=[{min(nz):.6g},{max(rs):.6g}] cm')


if __name__ == '__main__':
    main()
