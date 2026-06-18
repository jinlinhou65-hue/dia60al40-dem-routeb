"""Write the paper reproduction target manifest without generating data."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = REPO_ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from paper_reproduction import write_manifest_outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper", choices=["all", "zhang", "yuan", "liu", "li"], default="all")
    parser.add_argument("--outdir", default="outputs/paper_algorithm_reproduction")
    args = parser.parse_args()

    keys = None if args.paper == "all" else [args.paper]
    paths = write_manifest_outputs(Path(args.outdir), keys=keys)
    print(
        json.dumps(
            {name: str(path) for name, path in paths.items()},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
