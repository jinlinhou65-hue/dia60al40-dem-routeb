"""Scan Zhang force-chain parameters on a direct contact-force stage series."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = REPO_ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from paper_reproduction import calibrate_zhang_force_chains


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-dir", required=True)
    parser.add_argument("--pressure-curve", required=True)
    parser.add_argument("--contact-dir", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--contact-glob", default="{stage_id}_contacts.csv")
    parser.add_argument("--threshold-factors", default="0.05,0.1,0.25,0.5,0.75,1.0,1.25,1.5,2.0")
    parser.add_argument("--min-chain-lengths", default="3")
    parser.add_argument("--length-unit", choices=["um", "micron", "cm", "m"], default="um")
    args = parser.parse_args()

    summary = calibrate_zhang_force_chains(
        snapshot_dir=Path(args.snapshot_dir),
        pressure_curve=Path(args.pressure_curve),
        contact_dir=Path(args.contact_dir),
        outdir=Path(args.outdir),
        contact_glob=args.contact_glob,
        threshold_factors=parse_float_list(args.threshold_factors),
        min_chain_lengths=parse_int_list(args.min_chain_lengths),
        length_unit=args.length_unit,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


def parse_float_list(value: str) -> list[float]:
    values = [float(item.strip()) for item in value.split(",") if item.strip()]
    if not values:
        raise ValueError("at least one threshold factor is required")
    if any(item <= 0.0 for item in values):
        raise ValueError("threshold factors must be positive")
    return values


def parse_int_list(value: str) -> list[int]:
    values = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not values:
        raise ValueError("at least one minimum chain length is required")
    if any(item < 2 for item in values):
        raise ValueError("minimum chain lengths must be at least 2")
    return values


if __name__ == "__main__":
    main()
