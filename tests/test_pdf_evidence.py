from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = REPO_ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from paper_reproduction import build_manifest, get_pdf_evidence, reproduce_all


class PdfEvidenceTest(unittest.TestCase):
    def test_manifest_contains_pdf_evidence_for_each_paper(self):
        manifest = build_manifest()
        papers = {paper["key"]: paper for paper in manifest["papers"]}
        self.assertEqual(set(papers), {"zhang", "yuan", "liu", "li"})
        for key, paper in papers.items():
            evidence = paper["pdf_evidence"]
            self.assertGreaterEqual(len(evidence), 4, key)
            self.assertTrue(all(item["page"] > 0 for item in evidence))
            self.assertTrue(all(item["reproduction_use"] for item in evidence))

        self.assertIn(3, {item["page"] for item in papers["zhang"]["pdf_evidence"]})
        self.assertIn(40, {item["page"] for item in papers["yuan"]["pdf_evidence"]})
        self.assertIn(11, {item["page"] for item in papers["liu"]["pdf_evidence"]})
        self.assertIn(52, {item["page"] for item in papers["li"]["pdf_evidence"]})

    def test_pdf_evidence_export_honors_subset(self):
        evidence = get_pdf_evidence(["yuan"])
        self.assertEqual(set(evidence), {"yuan"})
        self.assertTrue(any("Arch" in item["reproduction_use"] for item in evidence["yuan"]))

    def test_generated_reports_include_pdf_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            outdir = Path(tmp) / "paper"
            reproduce_all(outdir)
            manifest = json.loads(
                (outdir / "paper_reproduction_manifest.json").read_text(encoding="utf-8")
            )
            report = (outdir / "paper_reproduction_report.md").read_text(encoding="utf-8")
            self.assertTrue(all(paper["pdf_evidence"] for paper in manifest["papers"]))
            self.assertIn("PDF Evidence", (outdir / "paper_reproduction_manifest.md").read_text(encoding="utf-8"))
            self.assertIn("PDF evidence anchors", report)
            self.assertIn("p40", report)


if __name__ == "__main__":
    unittest.main()
