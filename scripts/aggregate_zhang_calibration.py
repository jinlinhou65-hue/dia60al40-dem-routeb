"""Aggregate Zhang force-chain calibration scans across DEM workflow artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = REPO_ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from paper_reproduction import aggregate_zhang_calibration


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="ensemble_inputs")
    parser.add_argument("--outdir", default="ensemble_summary")
    args = parser.parse_args()

    summary = aggregate_zhang_calibration(Path(args.root), Path(args.outdir))
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
