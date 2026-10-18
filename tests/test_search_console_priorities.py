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

    def test_simplified_chinese_themes_are_prioritized_across_countries(self):
        rows = [
            {"market": "CN", "query": "谷歌代投", "page": "https://shumaojs.com/google-ads.html", "clicks": 1, "impressions": 10, "ctr": 0.1, "position": 12, "source": "cn.csv"},
            {"market": "HK", "query": "google 廣告收費", "page": "https://shumaojs.com/google-ads-agency-hong-kong.html", "clicks": 0, "impressions": 20, "ctr": 0, "position": 30, "source": "hk.csv"},
            {"market": "US", "query": "Google Ads audit", "page": "https://shumaojs.com/google-ads-management-usa.html", "clicks": 0, "impressions": 15, "ctr": 0, "position": 25, "source": "us.csv"},
        ]

        self.assertEqual(MODULE.infer_market("中国", "queries.csv"), "CN")
        self.assertEqual(MODULE.simplified_query_theme("谷歌广告代投服务"), "谷歌代投")
        self.assertEqual(MODULE.simplified_query_theme("谷歌开户流程"), "谷歌开户")
        self.assertEqual(MODULE.simplified_query_theme("谷歌广告排名"), "谷歌排名")
        self.assertEqual(MODULE.simplified_query_theme("Google Ads audit"), "")

        priorities = MODULE.aggregate(rows)
        report = MODULE.render_markdown({"generatedAt": "2026-10-19", "notes": [], "priorities": priorities})
        focus_section = report.split("## All market and language queries", 1)[0]
        self.assertIn("谷歌代投 | CN |", focus_section)
        self.assertIn("## All market and language queries", report)
        self.assertIn("google 廣告收費", report)
        self.assertIn("Google Ads audit", report)


if __name__ == "__main__":
    unittest.main()
