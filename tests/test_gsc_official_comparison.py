import csv
import json
import tempfile
import unittest
from pathlib import Path
from scripts.prioritize_search_console import header_map, read_rows, aggregate, markdown_cell, render_markdown

ROOT = Path(__file__).parents[1]


class OfficialComparisonTests(unittest.TestCase):
    def test_current_and_previous_are_not_added_together(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "queries.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as handle:
                csv.writer(handle).writerows([
                    ["热门查询", "过去 7 天 点击次数", "先前 7 天 点击次数", "过去 7 天 展示",
                     "先前 7 天 展示", "过去 7 天 点击率", "先前 7 天 点击率", "过去 7 天 排名", "先前 7 天 排名"],
                    ["谷歌代投", "1", "2", "13", "20", "7.69%", "10%", "3.54", "8"]])
            current, _ = read_rows([path])
            previous, _ = read_rows([path], "previous")
            self.assertEqual(current[0]["impressions"], 13)
            self.assertEqual(previous[0]["impressions"], 20)
            self.assertEqual(current[0]["clicks"], 1)
            self.assertAlmostEqual(current[0]["ctr"], .0769)
            self.assertEqual(current[0]["position"], 3.54)
            self.assertEqual(current[0]["market"], "UNASSIGNED")
            self.assertEqual(aggregate(current)[0]["impressions"], 13)

    def test_actual_official_exports_and_precision(self):
        for window in ["weekly", "monthly"]:
            folder = ROOT / "reports/search-console/2026-10-29-exports" / window
            paths = [p for p in folder.glob("*.csv") if "热门查询" in p.read_text(encoding="utf-8-sig").splitlines()[0]]
            rows, notes = read_rows(paths)
            target = next(r for r in rows if r["query"] == "谷歌代投")
            self.assertEqual(target["impressions"], 13)
            self.assertEqual(target["position"], 3.54)
            self.assertEqual(target["market"], "UNASSIGNED")
            prior, _ = read_rows(paths, "previous")
            self.assertFalse(any(r["query"] == "谷歌代投" for r in prior))
            self.assertFalse(any("missing" in n for n in notes))

    def test_page_dimension_alias_and_period_selection(self):
        fields = header_map(["排名靠前的网页", "过去 28 天 展示", "先前 28 天 展示"])
        self.assertEqual(fields["page"], "排名靠前的网页")
        self.assertEqual(fields["impressions"], "过去 28 天 展示")

    def test_ambiguous_and_mixed_windows_rejected(self):
        with self.assertRaises(ValueError):
            header_map(["过去 7 天 展示", "过去 28 天 点击次数"])
        with self.assertRaises(ValueError):
            header_map(["过去 7 天 展示", "过去 7 天 展示次数"])

    def test_previous_never_silently_uses_unlabelled_current_metrics(self):
        fields = header_map(["query", "clicks", "impressions", "ctr", "position"], "previous")
        self.assertEqual(fields, {"query": "query"})
        with self.assertRaises(ValueError):
            header_map(["query"], "combined")

    def test_simple_export_compatibility(self):
        fields = header_map(["query", "page", "country", "clicks", "impressions", "ctr", "position"])
        self.assertEqual(len(fields), 7)

    def test_multiline_query_does_not_break_markdown_rows(self):
        query = "site:example.com \nquoted\tquery | sample"
        self.assertEqual(markdown_cell(query), "site:example.com  quoted query \\| sample")
        row = {"market": "UNASSIGNED", "query": query, "page": "", "clicks": 0,
               "impressions": 1, "ctr": 0, "position": 5, "source": "queries.csv"}
        result = {"generatedAt": "2026-10-30", "notes": [], "priorities": aggregate([row])}
        report = render_markdown(result)
        self.assertEqual(sum(line.startswith("| 1 |") for line in report.splitlines()), 1)
        self.assertNotIn("\nquoted", report)
        self.assertEqual(row["query"], query)


if __name__ == "__main__":
    unittest.main()
