from __future__ import annotations

import math


UM_PER_CM = 10000.0
W_UM = 400.0


# stage_id, target_rho_total, current_height_um, acceptable low/high bounds.
STAGES = [
    ("stage0_preload", 0.5668, 201.779948, 0.55, 0.60),
    ("stage1_rho065", 0.6500, 175.952115, 0.63, 0.67),
    ("stage2_rho072", 0.7200, 158.845659, 0.70, 0.74),
    ("stage3_rho080", 0.8000, 142.961093, 0.78, 0.82),
    ("stage4_rho088", 0.8800, 129.964630, 0.86, 0.90),
    ("stage5_rho095", 0.9500, 120.388289, 0.93, 0.97),
]

STAGE_BY_ID = {stage[0]: stage for stage in STAGES}


def stage_ids() -> list[str]:
    return [stage[0] for stage in STAGES]


def read_liggghts_dump(path) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    try:
        atoms_i = next(i for i, line in enumerate(lines) if line.startswith("ITEM: ATOMS"))
    except StopIteration:
        raise SystemExit(f"[FAIL] no ITEM: ATOMS section in {path}")
    cols = lines[atoms_i].split()[2:]
    rows: list[dict[str, str]] = []
    for line in lines[atoms_i + 1 :]:
        if not line.strip() or line.startswith("ITEM:"):
            break
        vals = line.split()
        if len(vals) >= len(cols):
            rows.append(dict(zip(cols, vals)))
    return rows


def particle_shape(row: dict[str, str]) -> str:
    typ = int(float(row["type"]))
    radius_um = float(row["radius"]) * UM_PER_CM
    if typ == 1:
        return "Al"
    return "DL" if radius_um > 24.0 else "DS"


def particle_material(row: dict[str, str]) -> str:
    return "Al" if int(float(row["type"])) == 1 else "Diamond"


def particle_area_um2(row: dict[str, str]) -> float:
    r_um = float(row["radius"]) * UM_PER_CM
    if particle_shape(row) == "Al":
        return math.pi * r_um * r_um
    # Match COMSOL Route-B geometry: all diamond particles are regular octagons.
    return 2.0 * math.sqrt(2.0) * r_um * r_um


def total_particle_area_um2(rows: list[dict[str, str]]) -> float:
    return sum(particle_area_um2(row) for row in rows)


def contact_counts(rows: list[dict[str, str]], gap_tol_um: float) -> dict[str, int]:
    counts = {str(row.get("id", i + 1)): 0 for i, row in enumerate(rows)}
    for i, a in enumerate(rows):
        ax = float(a["x"]) * UM_PER_CM
        ay = float(a["y"]) * UM_PER_CM
        ar = float(a["radius"]) * UM_PER_CM
        aid = str(a.get("id", i + 1))
        for j, b in enumerate(rows[i + 1 :], start=i + 1):
            bx = float(b["x"]) * UM_PER_CM
            by = float(b["y"]) * UM_PER_CM
            br = float(b["radius"]) * UM_PER_CM
            bid = str(b.get("id", j + 1))
            gap = math.hypot(ax - bx, ay - by) - (ar + br)
            if gap <= gap_tol_um:
                counts[aid] += 1
                counts[bid] += 1
    return counts
