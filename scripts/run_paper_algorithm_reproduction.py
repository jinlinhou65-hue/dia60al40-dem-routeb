"""Generate first-pass reproductions of the four powder-compaction papers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = REPO_ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from paper_reproduction import (
    generate_paper_report,
    reproduce_all,
    reproduce_li,
    reproduce_liu,
    reproduce_yuan,
    reproduce_zhang,
    validate_algorithm_reproduction,
    write_acceptance_outputs,
    write_manifest_outputs,
)


PAPER_RUNNERS = {
    "zhang": reproduce_zhang,
    "yuan": reproduce_yuan,
    "liu": reproduce_liu,
    "li": reproduce_li,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper", choices=["all", "zhang", "yuan", "liu", "li"], default="all")
    parser.add_argument("--outdir", default="outputs/paper_algorithm_reproduction")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    if args.paper == "all":
        result = reproduce_all(outdir)
    else:
        result = {
            args.paper: PAPER_RUNNERS[args.paper](outdir / args.paper),
        }
        checks, acceptance = validate_algorithm_reproduction(outdir, papers=[args.paper])
        write_acceptance_outputs(outdir, checks, acceptance, prefix="paper")
        write_manifest_outputs(outdir, keys=[args.paper])
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "summary.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        generate_paper_report(outdir, papers=[args.paper])
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
