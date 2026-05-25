"""Convert a LIGGGHTS DEM dump (or pre-flattened CSV) into a COMSOL-ready particle table.

This converter is the LAST gate before the COMSOL FEM model consumes DEM positions.
It refuses by default to emit a CSV whose particle composition disagrees with the
target (34 Al + 8 DS + 8 DL = 50). Without this guard, a deck that silently dropped
DL or under-inserted Al (as happened on Run #8: Al=26, DS=8, DL=0) would still
produce a clean-looking CSV and silently corrupt the downstream FEM run.

Compressed DEM stages can contain Hertz contact overlap. The raw overlap is
valid DEM physics but invalid as a COMSOL geometry import, because COMSOL would
start from intersecting domains. Use --auto-shrink-overlap for stage handoff
CSVs; the raw, unmodified DEM state is preserved by export_dem_stage_handoff.py.

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


def particle_xy_radius_um(row):
    x = float(pick(row, 'x', 'Points:0', 'Points_0')) * UM_PER_CM
    y = float(pick(row, 'y', 'Points:1', 'Points_1')) * UM_PER_CM
    rad = float(pick(row, 'radius', 'Radius')) * UM_PER_CM
    return x, y, rad


def projected_overlap_summary(rows, overlap_tol_um):
    severe = []
    worst_gap = None
    worst_pair = ('?', '?')
    for i, a in enumerate(rows):
        ax, ay, ar = particle_xy_radius_um(a)
        for b in rows[i + 1:]:
            bx, by, br = particle_xy_radius_um(b)
            gap = math.hypot(ax - bx, ay - by) - (ar + br)
            if worst_gap is None or gap < worst_gap:
                worst_gap = gap
                worst_pair = (pick(a, 'id', 'ID'), pick(b, 'id', 'ID'))
            if gap < -overlap_tol_um:
                severe.append((gap, pick(a, 'id', 'ID'), pick(b, 'id', 'ID')))
    severe.sort()
    return severe, worst_gap if worst_gap is not None else 0.0, worst_pair


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--mode', default='2d')
    ap.add_argument('--output', default='D:/CodexProjects/scripts/comsol_particles.csv')
    # Composition gate. Defaults match the project target 34 Al + 8 DS + 8 DL = 50.
    # Keep the radius-based DS/DL split threshold in sync with verify_liggghts_dump.py
    # and with the deck's templates (DS r=18 um, DL r=30 um -> 24 um is the safe split).
    ap.add_argument('--expect-al', type=int, default=34)
    ap.add_argument('--expect-ds', type=int, default=8)
    ap.add_argument('--expect-dl', type=int, default=8)
    ap.add_argument('--allow-incomplete', action='store_true',
                    help='emit CSV even when composition disagrees with target. '
                         'For diagnostic dumps only — DO NOT feed the result to COMSOL.')
    ap.add_argument('--radius-shrink-um', type=float, default=0.0,
                    help='Uniformly shrink every particle radius in the COMSOL geometry CSV.')
    ap.add_argument('--auto-shrink-overlap', action='store_true',
                    help='Increase radius shrink enough to remove projected DEM contact overlap.')
    ap.add_argument('--overlap-tol-um', type=float, default=1.0,
                    help='Projected overlap deeper than this is reported as a severe DEM overlap.')
    ap.add_argument('--clearance-um', type=float, default=0.02,
                    help='Extra geometric clearance added when --auto-shrink-overlap computes shrink.')
    args = ap.parse_args()
    inpath = Path(args.input)

    if inpath.suffix.lower() == '.dump' or 'ITEM: TIMESTEP' in inpath.read_text(encoding='utf-8', errors='replace')[:128]:
        rows = read_dump(inpath)
    else:
        rows = read_table(inpath)

    counts = {'Al': 0, 'DS': 0, 'DL': 0}
    for r in rows:
        typ = int(float(pick(r, 'type', 'Type')))
        _, _, rad = particle_xy_radius_um(r)
        shape = 'Al' if typ == 1 else ('DL' if rad > 24 else 'DS')
        counts[shape] = counts.get(shape, 0) + 1

    # 2D handoff validity gate: Route-B collapses DEM to x-y. z drift remains
    # fatal. Projected overlaps are DEM contact compression; for COMSOL geometry
    # we remove them by uniform radius shrink when requested.
    zvals = []
    for a in rows:
        try:
            zvals.append(float(a.get('z', 0.0)) * UM_PER_CM)
        except Exception:
            zvals.append(0.0)
    zmax = max((abs(z) for z in zvals), default=0.0)
    if zmax > 0.05:
        print(f'[FAIL] 2D handoff invalid: max|z|={zmax:.6g} um > 0.05 um', file=sys.stderr)
        raise SystemExit(1)

    severe, worst_gap, worst_pair = projected_overlap_summary(rows, args.overlap_tol_um)
    shrink_um = max(0.0, args.radius_shrink_um)
    if severe:
        suggested = max(0.0, -severe[0][0] / 2.0 + args.clearance_um)
        print(
            f'[VERIFY] projected DEM overlaps={len(severe)} worst_gap_um={severe[0][0]:.6g} '
            f'pair={severe[0][1]}-{severe[0][2]} suggested_radius_shrink_um={suggested:.6g}',
            file=sys.stderr,
        )
        if args.auto_shrink_overlap:
            shrink_um = max(shrink_um, suggested)
        elif not args.allow_incomplete:
            print(
                '[FAIL] refusing to write intersecting COMSOL geometry. '
                'Pass --auto-shrink-overlap for COMSOL handoff, or --allow-incomplete for diagnostics.',
                file=sys.stderr,
            )
            raise SystemExit(1)

    min_radius_um = min((particle_xy_radius_um(row)[2] for row in rows), default=0.0)
    if min_radius_um <= 0.0:
        raise SystemExit('[FAIL] no positive particle radii found')
    if shrink_um >= 0.5 * min_radius_um:
        raise SystemExit(
            f'[FAIL] radius_shrink_um={shrink_um:.6g} um is >= half the smallest particle radius '
            f'({0.5 * min_radius_um:.6g} um); geometry would no longer represent the DEM stage'
        )

    out = []
    for r in rows:
        typ = int(float(pick(r, 'type', 'Type')))
        x, y, rad = particle_xy_radius_um(r)
        shape = 'Al' if typ == 1 else ('DL' if rad > 24 else 'DS')
        out.append(
            {
                'id': pick(r, 'id', 'ID'),
                'type': typ,
                'shape': shape,
                'x_um': x,
                'y_um': y,
                'r_um': rad - shrink_um,
            }
        )

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
    print(
        f'[OK] wrote {outpath} rows={len(out)} counts={counts} '
        f'radius_shrink_um={shrink_um:.6g} worst_raw_gap_um={worst_gap:.6g} '
        f'worst_pair={worst_pair[0]}-{worst_pair[1]}'
    )


if __name__ == '__main__':
    main()
