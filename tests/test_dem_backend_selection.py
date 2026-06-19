from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = REPO_ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from paper_reproduction.dem_backend_selection import (
    BACKEND_CANDIDATES,
    build_backend_selection_manifest,
    render_backend_selection_markdown,
    selected_backend,
)


class DemBackendSelectionTest(unittest.TestCase):
    def test_liggghts_is_selected_backend(self):
        selected = selected_backend()
        self.assertEqual("liggghts_public", selected.key)
        self.assertIn("GitHub Actions", " ".join(selected.source_basis))

    def test_selection_covers_required_open_source_candidates(self):
        names = {candidate.name for candidate in BACKEND_CANDIDATES}
        self.assertGreaterEqual(
            names,
            {
                "LIGGGHTS-PUBLIC",
                "LAMMPS GRANULAR package",
                "YADE",
                "MercuryDPM",
                "Project Chrono DEM / DEM-Engine",
            },
        )

    def test_selection_manifest_excludes_non_open_source_paper_tools(self):
        manifest = build_backend_selection_manifest()
        boundary = " ".join(manifest["non_open_source_paper_tools"])
        self.assertIn("PFC/PFC2D", boundary)
        self.assertIn("MSC.MARC", boundary)
        self.assertEqual("LIGGGHTS-PUBLIC", manifest["decision"])

    def test_tracked_backend_doc_matches_generator(self):
        docs_path = REPO_ROOT / "docs" / "dem_algorithm_selection.md"
        if not docs_path.exists():
            self.skipTest("tracked backend selection doc has not been generated yet")
        self.assertEqual(render_backend_selection_markdown(), docs_path.read_text(encoding="utf-8"))

    def test_generator_writes_backend_doc(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "dem_algorithm_selection.md"
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "generate_dem_backend_selection_doc.py"),
                    "--output",
                    str(output),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertTrue(output.exists())
            self.assertIn("dem_algorithm_selection.md", result.stdout)
            self.assertIn("LIGGGHTS-PUBLIC", output.read_text(encoding="utf-8"))

    def test_method_doc_covers_full_physics_chain(self):
        docs_path = REPO_ROOT / "docs" / "powder_compaction_simulation_method.md"
        text = docs_path.read_text(encoding="utf-8")
        for phrase in [
            "stress",
            "particle contacts",
            "arch candidates",
            "current",
            "temperature",
            "densification",
            "GitHub Actions",
            "Next Fidelity Upgrades",
        ]:
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
