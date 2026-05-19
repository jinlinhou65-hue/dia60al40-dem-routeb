from __future__ import annotations
import argparse, csv, math

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    args=ap.parse_args()
    rows=[]
    with open(args.input, newline='') as f:
        sample=f.read(4096); f.seek(0)
        dialect=csv.Sniffer().sniff(sample, delimiters=', \t')
        reader=csv.DictReader(f, dialect=dialect)
        for r in reader: rows.append(r)
    if not rows:
        raise SystemExit('[FAIL] no rows')
    xs=[float(r.get('x') or r.get('Points:0') or r.get('Points_0')) for r in rows]
    ys=[float(r.get('y') or r.get('Points:1') or r.get('Points_1')) for r in rows]
    rs=[float(r.get('radius') or r.get('Radius') or 0) for r in rows]
    print(f'[DEM] particles={len(rows)}')
    print(f'[DEM] x=[{min(xs):.6g},{max(xs):.6g}] cm y=[{min(ys):.6g},{max(ys):.6g}] cm')
    if any(rs): print(f'[DEM] radius=[{min([r for r in rs if r]):.6g},{max(rs):.6g}] cm')

if __name__ == '__main__': main()
