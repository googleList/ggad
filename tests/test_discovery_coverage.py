import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree

from scripts.article_index import synchronize
from scripts.discovery_coverage_check import ROOT, check_coverage
from scripts.generate_feed import build_feed, collect_articles


ORIGIN = "https://shumaojs.com"


class DiscoveryCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "articles").mkdir()
        for name in ["a", "b"]:
            url = ORIGIN + f"/articles/{name}.html"
            schema = {"@type": "Article", "headline": name, "description": "Guide",
                      "mainEntityOfPage": url, "datePublished": "2026-09-11",
                      "dateModified": "2026-10-28", "inLanguage": "zh-CN", "articleSection": "SEM"}
            self.write_page(f"articles/{name}.html", url, schema)
        self.write_page("tool.html", ORIGIN + "/tool.html", {"@type": "WebApplication"})
        self.write_hub(["articles/a.html", "articles/b.html", "tool.html"])
        (self.root / "feed.xml").write_bytes(build_feed(collect_articles(self.root)))
        self.write_sitemap(["articles/a.html", "articles/b.html", "tool.html"])

    def write_page(self, relative, canonical, schema, robots="index,follow"):
        (self.root / relative).write_text(
            f'<html><head><link rel="canonical" href="{canonical}">'
            f'<meta name="robots" content="{robots}">'
            f'<script type="application/ld+json">{json.dumps(schema)}</script></head></html>', encoding="utf-8")

    def write_hub(self, paths):
        schema = {"@type": "CollectionPage", "mainEntity": {"@type": "ItemList", "itemListElement": []}}
        source = '<link rel="canonical" href="' + ORIGIN + '/articles.html">'
        source += '<script type="application/ld+json">' + json.dumps(schema) + '</script>'
        source += "\n".join(f'<article data-article-card><h3><a href="{p}">{p}</a></h3></article>' for p in paths)
        (self.root / "articles.html").write_text(synchronize(source), encoding="utf-8")

    def write_sitemap(self, paths):
        sitemap = ElementTree.Element("urlset", {"xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9"})
        for p in paths:
            ElementTree.SubElement(ElementTree.SubElement(sitemap, "url"), "loc").text = ORIGIN + "/" + p
        ElementTree.ElementTree(sitemap).write(self.root / "sitemap.xml", encoding="utf-8")

    def errors(self):
        return "\n".join(check_coverage(self.root)["errors"])

    def test_articles_and_tools_are_not_forced_to_equal_rss(self):
        result = check_coverage(self.root)
        self.assertEqual(result["errors"], [])
        self.assertEqual((result["articles"], result["hubItems"], result["rssItems"]), (2, 3, 2))
        self.assertEqual(result["toolItems"], [ORIGIN + "/tool.html"])

    def test_missing_rss_article_fails(self):
        (self.root / "feed.xml").write_bytes(build_feed(collect_articles(self.root)[:1]))
        self.assertIn("Article missing from RSS", self.errors())

    def test_duplicate_or_non_editorial_rss_items_fail(self):
        feed = ElementTree.parse(self.root / "feed.xml")
        channel = feed.getroot().find("channel")
        for url in [ORIGIN + "/tool.html", ORIGIN + "/articles/a.html"]:
            ElementTree.SubElement(ElementTree.SubElement(channel, "item"), "link").text = url
        feed.write(self.root / "feed.xml", encoding="utf-8")
        self.assertIn("RSS has duplicate item URLs", self.errors())
        self.assertIn("RSS item is not an editorial Article", self.errors())

    def test_missing_hub_entry_or_sitemap_entry_fails(self):
        self.write_hub(["articles/a.html", "tool.html"])
        self.assertIn("Article missing from hub", self.errors())
        self.write_sitemap(["articles/a.html", "articles/b.html"])
        self.assertIn("Hub item missing from sitemap", self.errors())

    def test_noindex_and_wrong_canonical_fail(self):
        self.write_page("tool.html", ORIGIN + "/other.html", {"@type": "WebApplication"}, robots="noindex,follow")
        self.assertIn("Hub lists a noindex page", self.errors())
        self.assertIn("differs from target canonical", self.errors())

    def test_unknown_non_editorial_page_is_not_silently_allowed(self):
        self.write_page("tool.html", ORIGIN + "/tool.html", {"@type": "WebPage"})
        self.assertIn("not a declared WebApplication", self.errors())

    def test_external_and_encoded_traversal_urls_fail(self):
        self.write_hub(["articles/a.html", "articles/b.html", "https://example.com/tool.html"])
        self.assertIn("local canonical HTTPS URL", self.errors())
        self.write_hub(["articles/a.html", "articles/b.html", "/%2e%2e/outside.html"])
        self.assertIn("no safe local file", self.errors())

    def test_real_site_contract_without_hardcoded_content_count(self):
        result = check_coverage(ROOT)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["rssItems"], result["articles"])
        self.assertEqual(result["hubItems"], result["articles"] + len(result["toolItems"]))


if __name__ == "__main__":
    unittest.main()
