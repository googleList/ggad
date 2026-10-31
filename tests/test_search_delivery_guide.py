import unittest
from html.parser import HTMLParser
from pathlib import Path

from scripts.generate_feed import article_schema

ROOT = Path(__file__).resolve().parents[1]
ARTICLE = ROOT / "articles/google-ads-not-showing.html"


class Nodes(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.nodes = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.nodes.append((tag, dict(attrs)))


class SearchDeliveryGuideTests(unittest.TestCase):
    def setUp(self):
        self.source = ARTICLE.read_text(encoding="utf-8")
        self.nodes = Nodes(self.source).nodes

    def count(self, attribute):
        return sum(attribute in attrs for _, attrs in self.nodes)

    def test_original_workflow_has_distinct_evidence_stages(self):
        self.assertEqual(self.count("data-delivery-symptom"), 4)
        self.assertEqual(self.count("data-delivery-check"), 7)
        self.assertEqual(self.count("data-delivery-example"), 4)
        self.assertEqual(self.count("data-delivery-log"), 3)
        self.assertIn("尚未更新", self.source)
        self.assertIn("不是账户诊断结论", self.source)
        self.assertIn("全是原创教学假设", self.source)
        self.assertIn("未批准前保持暂停", self.source)

    def test_native_contents_and_table_accessibility(self):
        ids = [a["id"] for _, a in self.nodes if "id" in a]
        self.assertEqual(len(ids), len(set(ids)))
        anchors = [a["href"][1:] for t, a in self.nodes if t == "a" and a.get("href", "").startswith("#")]
        self.assertEqual(len(anchors), 6)
        self.assertTrue(all(anchor in ids for anchor in anchors))
        regions = [a for _, a in self.nodes if a.get("class") == "article-table-wrap"]
        self.assertEqual(len(regions), 2)
        for attrs in regions:
            self.assertEqual(attrs["tabindex"], "0")
            self.assertEqual(attrs["role"], "region")
            self.assertIn(attrs["aria-labelledby"], ids)

    def test_current_primary_references_and_no_account_form(self):
        links = [a.get("href", "") for t, a in self.nodes if t == "a"]
        for identifier in ("148778", "2544985", "9208915", "1722120", "2616014", "13457532", "13456810"):
            self.assertTrue(any(f"support.google.com/google-ads/answer/{identifier}?" in href for href in links))
        self.assertFalse(any(t == "form" for t, _ in self.nodes))
        self.assertEqual(self.count("data-preview-steps"), 1)
        self.assertEqual(self.count("data-delivery-records"), 1)

    def test_new_publication_and_discovery_do_not_rewrite_old_dates(self):
        schema = article_schema(ARTICLE)
        self.assertEqual(schema["datePublished"], "2026-11-01T01:00:00+08:00")
        self.assertEqual(schema["dateModified"], schema["datePublished"])
        self.assertEqual(schema["articleSection"], "SEM")
        for page in ("articles.html", "sitemap.xml", "feed.xml"):
            self.assertIn("articles/google-ads-not-showing.html", (ROOT / page).read_text(encoding="utf-8"))
        for page in ("google-ads-basics.html", "google-search-ads-guide.html"):
            self.assertIn('href="google-ads-not-showing.html#checks"', (ROOT / "articles" / page).read_text(encoding="utf-8"))
        self.assertEqual(article_schema(ROOT / "articles/google-ads-basics.html")["datePublished"], "2026-09-11")
        self.assertEqual(article_schema(ROOT / "articles/google-ads-basics.html")["dateModified"], "2026-11-01T01:18:00+08:00")

    def test_original_responsive_asset_contract(self):
        for name in ("search-delivery-diagnosis-v1.jpg", "search-delivery-diagnosis-thumb-v1.webp"):
            self.assertTrue((ROOT / "assets/articles" / name).is_file())
            self.assertIn(name, self.source)
            self.assertLess((ROOT / "assets/articles" / name).stat().st_size, 120000)
        self.assertIn('sizes="calc(100vw - 36px)"', self.source)
        self.assertIn('width="1200" height="675"', self.source)


if __name__ == "__main__":
    unittest.main()
