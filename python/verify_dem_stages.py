from __future__ import annotations

import argparse
import math
from collections import Counter
from pathlib import Path

from dem_stage_metadata import STAGES, UM_PER_CM, W_UM, read_liggghts_dump, total_particle_area_um2


def classify_counts(rows: list[dict[str, str]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        typ = int(float(row["type"]))
        radius_um = float(row["radius"]) * UM_PER_CM
        if typ == 1:
            counts["Al"] += 1
        elif typ == 2 and radius_um > 30.0:
            counts["DL"] += 1
        elif typ == 2:
            counts["DS"] += 1
        else:
            counts[f"type{typ}"] += 1
    return counts


def check_geometry(
    rows: list[dict[str, str]],
    z_tol_um: float,
    overlap_tol_um: float,
    clearance_um: float,
    fail_on_overlap: bool,
) -> None:
    zmax = max((abs(float(row.get("z", 0.0)) * UM_PER_CM) for row in rows), default=0.0)
    print(f"[VERIFY] max|z|={zmax:.6g} um")
    if zmax > z_tol_um:
        raise SystemExit(f"[FAIL] projected 2D handoff invalid: max|z|={zmax:.6g} um > {z_tol_um} um")

    severe: list[tuple[float, str, str]] = []
    for i, a in enumerate(rows):
        ax = float(a["x"]) * UM_PER_CM
        ay = float(a["y"]) * UM_PER_CM
        ar = float(a["radius"]) * UM_PER_CM
        for b in rows[i + 1 :]:
            bx = float(b["x"]) * UM_PER_CM
            by = float(b["y"]) * UM_PER_CM
            br = float(b["radius"]) * UM_PER_CM
            gap = math.hypot(ax - bx, ay - by) - (ar + br)
            if gap < -overlap_tol_um:
                severe.append((gap, a.get("id", "?"), b.get("id", "?")))
    if severe:
        severe.sort()
        gap, aid, bid = severe[0]
        shrink = max(0.0, -gap / 2.0 + clearance_um)
        level = "[FAIL]" if fail_on_overlap else "[VERIFY]"
        print(
            f"{level} projected overlaps={len(severe)} worst_gap_um={gap:.6g} "
            f"pair={aid}-{bid} suggested_radius_shrink_um={shrink:.6g}"
        )
        if fail_on_overlap:
            raise SystemExit(
                f"[FAIL] severe projected overlaps={len(severe)} worst_gap_um={gap:.6g} pair={aid}-{bid}"
            )


def verify_stage(root: Path, stage: str, target_rho: float, height_um: float, rho_min: float, rho_max: float, args) -> None:
    matches = sorted(root.glob(f"{stage}_*.dump"))
    if not matches:
        raise SystemExit(f"[FAIL] no dump found for {stage}: {root / (stage + '_*.dump')}")
    dump = matches[-1]
    print(f"[STAGE] {stage} dump={dump}")
    rows = read_liggghts_dump(dump)
    counts = classify_counts(rows)
    print(f"[VERIFY] particles={len(rows)} Al={counts['Al']} DS={counts['DS']} DL={counts['DL']}")
    if counts["Al"] != args.expect_al or counts["DS"] != args.expect_ds or counts["DL"] != args.expect_dl:
        raise SystemExit(
            f"[FAIL] composition mismatch for {stage}: "
            f"Al={counts['Al']}/{args.expect_al} DS={counts['DS']}/{args.expect_ds} DL={counts['DL']}/{args.expect_dl}"
        )
    check_geometry(rows, args.z_tol_um, args.overlap_tol_um, args.clearance_um, args.fail_on_overlap)
    area = total_particle_area_um2(rows)
    rho = area / (W_UM * height_um)
    print(f"[VERIFY] target_rho={target_rho:.4f} height_um={height_um:.6f} area_um2={area:.6f} rho_total={rho:.6f}")
    if not (rho_min <= rho <= rho_max):
        raise SystemExit(f"[FAIL] {stage} rho_total={rho:.6f} outside [{rho_min},{rho_max}]")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="liggghts/DEM")
    parser.add_argument("--expect-al", type=int, default=34)
    parser.add_argument("--expect-ds", type=int, default=8)
    parser.add_argument("--expect-dl", type=int, default=4)
    parser.add_argument("--z-tol-um", type=float, default=0.05)
    parser.add_argument("--overlap-tol-um", type=float, default=1.0)
    parser.add_argument("--clearance-um", type=float, default=0.02)
    parser.add_argument(
        "--fail-on-overlap",
        action="store_true",
        help="Fail when compressed DEM stages have projected Hertz overlap. Default is diagnostic-only.",
    )
    args = parser.parse_args()

    root = Path(args.root)
    for stage, target_rho, height_um, rho_min, rho_max in STAGES:
        verify_stage(root, stage, target_rho, height_um, rho_min, rho_max, args)
    print("[OK] all DEM stages passed composition, z-plane, and density gates")


if __name__ == "__main__":
    main()
