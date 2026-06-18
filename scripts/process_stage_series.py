"""Process a pressure-density stage series through paper reproduction metrics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = REPO_ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from paper_reproduction import process_stage_series


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-dir", required=True)
    parser.add_argument("--pressure-curve", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--snapshot-glob", default="dem_fem_handoff_stage*.csv")
    parser.add_argument("--length-unit", choices=["um", "micron", "cm", "m"], default="um")
    parser.add_argument("--width-um", type=float, default=None)
    parser.add_argument("--gap-tolerance-um", type=float, default=0.0)
    parser.add_argument("--normal-stiffness", type=float, default=1.0)
    parser.add_argument("--force-exponent", type=float, default=1.5)
    parser.add_argument("--min-contact-force", type=float, default=0.0)
    parser.add_argument("--sintering-time-s", type=float, default=1.0)
    parser.add_argument("--sintering-law", default="blended")
    parser.add_argument("--sintering-rate-scale", type=float, default=1.0)
    args = parser.parse_args()

    summary = process_stage_series(
        snapshot_dir=Path(args.snapshot_dir),
        pressure_curve=Path(args.pressure_curve),
        outdir=Path(args.outdir),
        snapshot_glob=args.snapshot_glob,
        length_unit=args.length_unit,
        width_um=args.width_um,
        gap_tolerance_um=args.gap_tolerance_um,
        normal_stiffness=args.normal_stiffness,
        force_exponent=args.force_exponent,
        min_contact_force=args.min_contact_force,
        sintering_time_s=args.sintering_time_s,
        sintering_law=args.sintering_law,
        sintering_rate_scale=args.sintering_rate_scale,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
