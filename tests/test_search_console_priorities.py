import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "prioritize_search_console.py"
SPEC = importlib.util.spec_from_file_location("prioritize_search_console", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class SearchConsolePriorityTests(unittest.TestCase):
    def test_multilingual_export_and_market_assignment(self):
        fixture = ROOT / "tests" / "fixtures" / "search-console-sample.csv"
        rows, notes = MODULE.read_rows([fixture])

        self.assertEqual(len(rows), 3)
        self.assertEqual({row["market"] for row in rows}, {"US", "HK", "UNASSIGNED"})
        self.assertIn("Read 3 rows", notes[0])
        self.assertAlmostEqual(rows[0]["ctr"], 0.02)

    def test_priority_output_keeps_observed_metrics(self):
        fixture = ROOT / "tests" / "fixtures" / "search-console-sample.csv"
        rows, _ = MODULE.read_rows([fixture])
        priorities = MODULE.aggregate(rows)
        us = next(item for item in priorities if item["market"] == "US")
        hk = next(item for item in priorities if item["market"] == "HK")

        self.assertEqual(us["impressions"], 800)
        self.assertEqual(us["position"], 14.0)
        self.assertEqual(hk["clicks"], 12)
        self.assertIn("internal links", us["recommendedAction"])


if __name__ == "__main__":
    unittest.main()
