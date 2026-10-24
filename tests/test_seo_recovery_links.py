import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from seo_quality_check import PageParser, html_files  # noqa: E402


class AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.references = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag in {"a", "link", "img", "script"}:
            target = values.get("href") or values.get("src")
            if target:
                self.references.append(target)
        if tag == "a":
            self.current = {"href": values.get("href", ""), "text": ""}

    def handle_data(self, data):
        if self.current is not None:
            self.current["text"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            self.links.append(self.current)
            self.current = None


class SeoRecoveryLinkTests(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / "404.html").read_text(encoding="utf-8")
        self.page = PageParser()
        self.page.feed(self.source)
        self.links = AnchorParser()
        self.links.feed(self.source)

    def test_404_resources_and_links_are_root_relative(self):
        self.assertGreater(len(self.links.references), 8)
        for target in self.links.references:
            with self.subTest(target=target):
                self.assertTrue(target.startswith("/") and not target.startswith("//"))
                self.assertTrue((ROOT / urlparse(target).path.lstrip("/")).is_file())

    def test_404_destinations_are_stable_at_arbitrary_depths(self):
        for missing in ["/missing.html", "/old/product.html", "/archive/products/deleted/"]:
            for target in self.links.references:
                with self.subTest(missing=missing, target=target):
                    resolved = urlparse(urljoin("https://shumaojs.com" + missing, target))
                    self.assertEqual(resolved.netloc, "shumaojs.com")
                    self.assertEqual(resolved.path, target)

    def test_404_keeps_noindex_and_native_home_recovery(self):
        self.assertIn("noindex", self.page.robots)
        self.assertEqual(self.page.canonical, "")
        self.assertEqual(self.page.h1_count, 1)
        links = AnchorParser()
        links.feed(self.source)
        self.assertTrue(any(link["href"] == "/index.html" and link["text"].strip() == "返回首页"
                            for link in links.links))

    def test_ad_rank_links_do_not_promise_a_setup_guide(self):
        checked = 0
        for page in html_files():
            parser = AnchorParser()
            parser.feed(page.read_text(encoding="utf-8"))
            source_url = "https://shumaojs.com/" + page.relative_to(ROOT).as_posix()
            for link in parser.links:
                if urlparse(urljoin(source_url, link["href"])).path != "/articles/google-search-ads-guide.html":
                    continue
                checked += 1
                label = " ".join(link["text"].split())
                with self.subTest(source=page.name, label=label):
                    self.assertNotIn(label, {"搜索广告搭建指南", "Google 搜索广告完整指南", "搜索广告指南", "搜索广告"})
        self.assertGreaterEqual(checked, 10)


if __name__ == "__main__":
    unittest.main()
