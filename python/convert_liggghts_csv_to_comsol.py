"""Convert a LIGGGHTS DEM dump (or pre-flattened CSV) into a COMSOL-ready particle table.

This converter is the LAST gate before the COMSOL FEM model consumes DEM positions.
It refuses by default to emit a CSV whose particle composition disagrees with the
target (34 Al + 8 DS + 4 DL = 46). Without this guard, a deck that silently dropped
DL or under-inserted Al (as happened on Run #8: Al=26, DS=8, DL=0) would still
produce a clean-looking CSV and silently corrupt the downstream FEM run.

Use --allow-incomplete only for diagnostic dumps that should NOT be fed to COMSOL.
"""
from __future__ import annotations
import argparse, csv, sys, math
from pathlib import Path

UM_PER_CM = 10000.0


def pick(row, *names):
    for n in names:
        if n in row and row[n] not in ('', None):
            return row[n]
    raise KeyError(names)


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
    ap.add_argument('--mode', default='2d')
    ap.add_argument('--output', default='D:/CodexProjects/scripts/comsol_particles.csv')
    # Composition gate. Defaults match the project target 34 Al + 8 DS + 4 DL = 46.
    # Keep the radius-based DS/DL split threshold in sync with verify_liggghts_dump.py
    # and with the deck's templates (DS r=18 um, DL r=42 um → 30 um is the safe split).
    ap.add_argument('--expect-al', type=int, default=34)
    ap.add_argument('--expect-ds', type=int, default=8)
    ap.add_argument('--expect-dl', type=int, default=4)
    ap.add_argument('--allow-incomplete', action='store_true',
                    help='emit CSV even when composition disagrees with target. '
                         'For diagnostic dumps only — DO NOT feed the result to COMSOL.')
    args = ap.parse_args()
    inpath = Path(args.input)

    if inpath.suffix.lower() == '.dump' or 'ITEM: TIMESTEP' in inpath.read_text(encoding='utf-8', errors='replace')[:128]:
        rows = read_dump(inpath)
    else:
        rows = read_table(inpath)

    out = []
    counts = {'Al': 0, 'DS': 0, 'DL': 0}
    for r in rows:
        typ = int(float(pick(r, 'type', 'Type')))
        x = float(pick(r, 'x', 'Points:0', 'Points_0')) * UM_PER_CM
        y = float(pick(r, 'y', 'Points:1', 'Points_1')) * UM_PER_CM
        rad = float(pick(r, 'radius', 'Radius')) * UM_PER_CM
        shape = 'Al' if typ == 1 else ('DL' if rad > 30 else 'DS')
        counts[shape] = counts.get(shape, 0) + 1
        out.append({'id': pick(r, 'id', 'ID'), 'type': typ, 'shape': shape, 'x_um': x, 'y_um': y, 'r_um': rad})

    # 2D handoff validity gate: Route-B collapses DEM to x-y. If centers are not
    # already on z=0, or if the projection creates severe overlaps, COMSOL receives
    # an impossible initial geometry and will fail at uTop=0.
    zvals = []
    severe = []
    for i, a in enumerate(rows):
        try:
            zvals.append(float(a.get('z', 0.0)) * UM_PER_CM)
        except Exception:
            zvals.append(0.0)
        ax, ay, ar = float(pick(a, 'x', 'Points:0', 'Points_0'))*UM_PER_CM, float(pick(a, 'y', 'Points:1', 'Points_1'))*UM_PER_CM, float(pick(a, 'radius', 'Radius'))*UM_PER_CM
        for b in rows[i+1:]:
            bx, by, br = float(pick(b, 'x', 'Points:0', 'Points_0'))*UM_PER_CM, float(pick(b, 'y', 'Points:1', 'Points_1'))*UM_PER_CM, float(pick(b, 'radius', 'Radius'))*UM_PER_CM
            gap = math.hypot(ax-bx, ay-by) - (ar+br)
            if gap < -1.0:
                severe.append((gap, pick(a, 'id', 'ID'), pick(b, 'id', 'ID')))
    zmax = max((abs(z) for z in zvals), default=0.0)
    geom_bad = zmax > 0.05 or bool(severe)
    if geom_bad:
        print(f'[VERIFY] 2D handoff invalid: max|z|={zmax:.6g} um severe_overlaps={len(severe)}', file=sys.stderr)
        if severe:
            severe.sort()
            print(f'[VERIFY] worst projected overlap gap={severe[0][0]:.6g} um pair={severe[0][1]}-{severe[0][2]}', file=sys.stderr)
        if not args.allow_incomplete:
            print('[FAIL] refusing to write CSV because projected DEM geometry is invalid for 2D COMSOL.', file=sys.stderr)
            raise SystemExit(1)

    # Composition gate — runs BEFORE any file is written, so a failing dump cannot
    # silently produce a COMSOL-ready CSV. This is the second-line defense (the first
    # being verify_liggghts_dump.py in CI); covers the case where someone runs the
    # converter locally on a bad dump.
    expected = {'Al': args.expect_al, 'DS': args.expect_ds, 'DL': args.expect_dl}
    mismatches = {k: (counts.get(k, 0), v) for k, v in expected.items() if counts.get(k, 0) != v}
    if mismatches:
        print(f'[VERIFY] particles={len(rows)} got={counts} expected={expected}', file=sys.stderr)
        for k, (got, want) in mismatches.items():
            print(f'[VERIFY] {k}: got {got}, expected {want}', file=sys.stderr)
        if not args.allow_incomplete:
            print('[FAIL] composition does not match target — refusing to write CSV. '
                  'Re-run the DEM, or pass --allow-incomplete for a diagnostic-only dump '
                  '(such output MUST NOT be fed to COMSOL).', file=sys.stderr)
            raise SystemExit(1)
        print('[WARN] --allow-incomplete set: writing CSV despite composition mismatch. '
              'DO NOT feed this CSV to COMSOL.', file=sys.stderr)

    outpath = Path(args.output)
    outpath.parent.mkdir(parents=True, exist_ok=True)
    with outpath.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['id', 'type', 'shape', 'x_um', 'y_um', 'r_um'])
        w.writeheader(); w.writerows(out)
    print(f'[OK] wrote {outpath} rows={len(out)} counts={counts}')


if __name__ == '__main__':
    main()
