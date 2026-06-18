"""Validate a real DEM run against paper-reproduction evidence gates."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = REPO_ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from paper_reproduction import write_dem_evidence_outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dem-dir", required=True)
    parser.add_argument("--outdir", default=None)
    parser.add_argument("--allow-review", action="store_true")
    args = parser.parse_args()

    outputs = write_dem_evidence_outputs(
        dem_dir=Path(args.dem_dir),
        outdir=Path(args.outdir) if args.outdir else None,
    )
    summary_rows = read_csv(outputs["summary"])
    status = str(summary_rows[0]["status"]) if summary_rows else "missing"
    print(json.dumps({key: str(value) for key, value in outputs.items()}, indent=2, sort_keys=True))
    print(f"[DEM EVIDENCE] status={status}")
    if status != "pass" and not (args.allow_review and status == "review"):
        raise SystemExit(2)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    main()
