import csv
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from scripts.structured_data_check import SchemaParser


ROOT = Path(__file__).parents[1]
CSV_PATH = ROOT / "assets/resources/keyword-page-map-v1.csv"


class ClusterParser(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.fields = {key: [] for key in ["data-cluster-map", "data-cluster-decision"]}
        self.map_urls = []
        self.in_map_row = False
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        for key in self.fields:
            if key in values:
                self.fields[key].append(values[key])
        if tag == "tr":
            self.in_map_row = "data-cluster-map" in values
        if tag == "a" and self.in_map_row:
            self.map_urls.append(values["href"])

    def handle_endtag(self, tag):
        if tag == "tr":
            self.in_map_row = False


class ContentClusterGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "articles/seo-content-cluster.html").read_text(encoding="utf-8")

    def test_map_and_page_decisions(self):
        parser = ClusterParser(self.source)
        self.assertEqual(parser.fields["data-cluster-map"], ["management", "setup", "ad-rank", "seo-title", "keywords", "learning"])
        self.assertEqual(parser.fields["data-cluster-decision"], ["improve", "separate", "verify-duplicate"])

    def test_csv_is_safe_example_and_matches_actual_pages(self):
        self.assertTrue(CSV_PATH.read_bytes().startswith(b"\xef\xbb\xbf"))
        with CSV_PATH.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 6)
        self.assertTrue(all(len(row) == 9 and None not in row for row in rows))
        parser = ClusterParser(self.source)
        expected_paths = ["/" + href.removeprefix("../") if href.startswith("../") else "/articles/" + href for href in parser.map_urls]
        self.assertEqual([urlparse(row["既有网址"]).path for row in rows], expected_paths)
        for row in rows:
            self.assertEqual(urlparse(row["既有网址"]).netloc, "shumaojs.com")
            self.assertTrue((ROOT / urlparse(row["既有网址"]).path.lstrip("/")).is_file())
            self.assertIn("非搜索量结论", row["证据状态"])
            self.assertIn("待按查询与地区分别验证", row["国家地区证据"])
            for cell in row.values():
                self.assertFalse(cell.startswith(("=", "+", "-", "@", "\t", "\r")))
        self.assertIn('download="keyword-page-map-v1.csv"', self.source)

    def test_no_automatic_merge_or_measured_result_claim(self):
        for phrase in ["不足以证明关键词内耗", "本教程不会执行删除、301 或 noindex", "不是客户成功案例",
                       "没有分析权限时写未知", "不保证自然名次", "不需要虚构商城商品",
                       "不存在“必须 4 至 8 篇才算集群”的通用门槛", "不等于独立、可索引的类目网址"]:
            self.assertIn(phrase, self.source)
        self.assertNotIn("多个页面争夺同一查询时，合并重复内容并保留更强页面", self.source)

    def test_original_identity_and_asset_metadata(self):
        parser = SchemaParser()
        parser.feed(self.source)
        article = next(json.loads(block) for block in parser.blocks if json.loads(block).get("@type") == "Article")
        self.assertEqual(article["headline"], "外贸网站 SEO 内容集群怎么规划")
        self.assertEqual(article["datePublished"], "2026-09-11")
        self.assertEqual(article["dateModified"], "2026-10-28T16:08:24+08:00")
        self.assertIn('datetime="' + article["dateModified"] + '"', self.source)
        self.assertTrue(article["image"].endswith("content-cluster-map-v1.jpg"))
        self.assertIn("content-cluster-map-thumb-v1.webp", (ROOT / "articles.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
