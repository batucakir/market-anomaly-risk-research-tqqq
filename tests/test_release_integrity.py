from __future__ import annotations

import ast
import csv
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "research_pipeline.ipynb"
MANIFEST = ROOT / "pipeline_cells" / "manifest.csv"
RESULTS = ROOT / "results" / "official_10000_summary.csv"


class ReleaseIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
        cls.code_cells = [
            cell for cell in cls.notebook["cells"] if cell["cell_type"] == "code"
        ]

    def test_notebook_is_clean(self):
        for cell in self.code_cells:
            self.assertEqual(cell.get("outputs", []), [])
            self.assertIsNone(cell.get("execution_count"))

    def test_required_final_modules_are_present(self):
        source = "\n".join("".join(cell.get("source", [])) for cell in self.code_cells)
        self.assertIn("MODULE 47 — OFFICIAL ACCOUNTING CORRECTION", source)
        self.assertIn("MODULE 48 — ALL VERSIONS $10,000 COMPARISON", source)
        self.assertIn("MODULE 49 — NOTEBOOK OUTPUT AND LIVE-STATE HANDOFF EXPORT", source)

    def test_duplicate_sources_are_absent(self):
        sources = ["".join(cell.get("source", [])) for cell in self.code_cells]
        self.assertEqual(len(sources), len(set(sources)))

    def test_exported_cells_match_notebook_and_compile(self):
        with MANIFEST.open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), len(self.code_cells))
        for row, cell in zip(rows, self.code_cells):
            source = "".join(cell.get("source", []))
            exported = (ROOT / row["path"]).read_text(encoding="utf-8")
            self.assertEqual(exported, source)
            self.assertEqual(hashlib.sha256(source.encode()).hexdigest(), row["sha256"])
            ast.parse(source, filename=row["path"])

    def test_official_results(self):
        with RESULTS.open(encoding="utf-8") as handle:
            rows = {row["Version"]: row for row in csv.DictReader(handle)}
        expected = {
            "V16": 4.365779600738577,
            "V8": 4.184168637789576,
            "TQQQ": 3.5634331693004357,
        }
        for name, value in expected.items():
            self.assertAlmostEqual(float(rows[name]["Final_Wealth"]), value, places=12)


if __name__ == "__main__":
    unittest.main()
