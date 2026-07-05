from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_JSON = (
    REPO_ROOT
    / "docs"
    / "reproduction_goal"
    / "03_zhang_particle_scale"
    / "data"
    / "zhang_contact_parameter_audit.json"
)
CORE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "dia60al40-dem.yml"
CLOUD_SCRIPT = REPO_ROOT / "scripts" / "cloud_run_liggghts_routeb.sh"
PINNED_LIGGGHTS_COMMIT = "3d5c00f20519e6bb6eb6756f51f1ad36564e649d"


class ZhangContactParameterAuditTests(unittest.TestCase):
    def test_audit_rejects_direct_damping_to_restitution_mapping(self) -> None:
        audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))

        self.assertEqual(audit["paper"]["document_type"], "journal_article")
        self.assertEqual(audit["paper_parameters"]["normal_damping_coefficient"], 0.2)
        self.assertEqual(audit["paper_parameters"]["damping_definition_status"], "not_reported")
        self.assertEqual(audit["liggghts_audit"]["damping_mapping"], "not_equivalent")
        self.assertEqual(audit["decision"]["next_variable"], "sidewall_friction_only")

    def test_renderer_scales_sidewall_pairs_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rendered = Path(tmp) / "wall-friction.liggghts"
            subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "python" / "render_dem_deck.py"),
                    "--input",
                    str(REPO_ROOT / "liggghts" / "in.dia60al40_dem_staged.liggghts"),
                    "--output",
                    str(rendered),
                    "--diamond-size-case",
                    "C",
                    "--particle-count-scale",
                    "2",
                    "--mu-scale",
                    "0.654",
                    "--mu-wall-scale",
                    "0.019113",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=True,
            )
            text = rendered.read_text(encoding="utf-8")

            self.assertIn("0.1962 0.1962 0.05232 0.000999992", text)
            self.assertIn("0.1962 0.0654 0.05232 0.000999992", text)
            self.assertIn("mu_wall_scale,0.019113,1", text)
            self.assertIn("mu_Al_Wall,0.000999992,1", text)
            self.assertIn("mu_Diamond_Wall,0.000999992,1", text)
            self.assertIn("mu_Al_Tool,0.05232,1", text)
            self.assertIn("mu_Diamond_Tool,0.05232,1", text)

    def test_solver_source_is_pinned_and_recorded(self) -> None:
        workflow = CORE_WORKFLOW.read_text(encoding="utf-8")
        cloud_script = CLOUD_SCRIPT.read_text(encoding="utf-8")

        for text in (workflow, cloud_script):
            self.assertIn(PINNED_LIGGGHTS_COMMIT, text)
            self.assertIn("fetch --depth=1 origin", text)
            self.assertIn("solver_provenance.csv", text)

        self.assertIn("mu_wall_scale_json", workflow)
        self.assertIn("--mu-wall-scale", workflow)


if __name__ == "__main__":
    unittest.main()
