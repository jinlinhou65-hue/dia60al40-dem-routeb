"""Generate the open-source DEM backend selection document."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = REPO_ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from paper_reproduction.dem_backend_selection import render_backend_selection_markdown


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="docs/dem_algorithm_selection.md",
        help="Markdown output path",
    )
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_backend_selection_markdown(), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
