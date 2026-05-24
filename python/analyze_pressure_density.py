from __future__ import annotations

import argparse
import csv
from pathlib import Path


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def interpolate_pressure(rows: list[dict[str, str]], target_rho: float) -> float:
    points = sorted((float(row["actual_rho_total"]), float(row["pressure_mpa"])) for row in rows)
    for (rho0, p0), (rho1, p1) in zip(points, points[1:]):
        if rho0 <= target_rho <= rho1:
            if rho1 == rho0:
                return p1
            return p0 + (p1 - p0) * (target_rho - rho0) / (rho1 - rho0)
    # If the target is just outside the achieved range, report the closest end
    # instead of inventing an extrapolated pressure.
    return min(points, key=lambda item: abs(item[0] - target_rho))[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--curve", default="liggghts/DEM/pressure_density_curve.csv")
    parser.add_argument("--output", default="liggghts/DEM/pressure_density_summary.csv")
    parser.add_argument("--target-rho", type=float, default=0.95)
    parser.add_argument("--target-pressure-mpa", type=float, default=200.0)
    args = parser.parse_args()

    curve = Path(args.curve)
    rows = read_rows(curve)
    p_target = interpolate_pressure(rows, args.target_rho)
    delta = p_target - args.target_pressure_mpa
    ratio = p_target / args.target_pressure_mpa if args.target_pressure_mpa else 0.0

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "target_rho_total",
                "p_target_mpa",
                "reference_mpa",
                "delta_mpa",
                "ratio_to_reference",
                "judgement",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "target_rho_total": f"{args.target_rho:.6g}",
                "p_target_mpa": f"{p_target:.9g}",
                "reference_mpa": f"{args.target_pressure_mpa:.9g}",
                "delta_mpa": f"{delta:.9g}",
                "ratio_to_reference": f"{ratio:.9g}",
                "judgement": "near" if abs(delta) <= 0.15 * args.target_pressure_mpa else ("high" if delta > 0 else "low"),
            }
        )
    print(f"[SUMMARY] P{args.target_rho:.3f}={p_target:.3f} MPa; reference={args.target_pressure_mpa:.3f} MPa; delta={delta:.3f} MPa")
    print(f"[OK] wrote {out}")


if __name__ == "__main__":
    main()
