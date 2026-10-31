import unittest
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

from scripts.generate_feed import article_schema, build_feed, collect_articles

ROOT = Path(__file__).resolve().parents[1]
PAGES = (
    ("google-ads-account-ownership-usa.html", "en-US"),
    ("google-ads-account-access-hong-kong.html", "zh-Hant-HK"),
)
MODIFIED = "2026-10-31T08:29:37+08:00"


class Markup(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.elements = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class HandoverDependenciesTests(unittest.TestCase):
    def test_six_distinct_checks_three_examples_and_native_anchors(self):
        for name, _ in PAGES:
            with self.subTest(page=name):
                markup = Markup((ROOT / "articles" / name).read_text(encoding="utf-8"))
                checks = [a["data-handover-check"] for _, a in markup.elements if "data-handover-check" in a]
                cases = [a["data-handover-example"] for _, a in markup.elements if "data-handover-example" in a]
                self.assertEqual(checks, ["admin", "owner", "billing", "conversion", "audience", "payments"])
                self.assertEqual(cases, ["access", "payer", "measurement"])
                for anchor in ("handover-dependencies", "handover-examples", "handover-records"):
                    self.assertTrue(any(a.get("id") == anchor for _, a in markup.elements))
                    self.assertTrue(any(a.get("href") == "#" + anchor for _, a in markup.elements))
                self.assertTrue(any(a.get("tabindex") == "0" and a.get("role") == "region" for _, a in markup.elements))

    def test_dates_locales_alternates_and_image_metadata(self):
        for name, locale in PAGES:
            with self.subTest(page=name):
                source = (ROOT / "articles" / name).read_text(encoding="utf-8")
                schema = article_schema(ROOT / "articles" / name)
                self.assertEqual(schema["datePublished"], "2026-09-28")
                self.assertEqual(schema["dateModified"], MODIFIED)
                self.assertEqual(schema["inLanguage"], locale)
                self.assertIn(f'datetime="{MODIFIED}"', source)
                self.assertIn('width="1200" height="675"', source)
                self.assertEqual(source.count('https://shumaojs.com/assets/articles/account-handover-controls-v1.jpg'), 3)
                for other, lang in PAGES:
                    self.assertIn(f'hreflang="{lang}" href="https://shumaojs.com/articles/{other}"', source)

    def test_official_sources_and_scope_boundaries(self):
        for name, _ in PAGES:
            source = (ROOT / "articles" / name).read_text(encoding="utf-8")
            for answer in ("9978556", "7456532", "9357343", "3061730", "7458428", "16305123", "7520231"):
                self.assertIn("support.google.com/google-ads/answer/" + answer, source)
            self.assertIn("hypothetical" if name.endswith("usa.html") else "假設情境", source)
            self.assertIn("unknown" if name.endswith("usa.html") else "未知", source)
            self.assertIn("unauthorized" if name.endswith("usa.html") else "未經授權", source)
            self.assertNotIn("../assets/article-materials.png", source)

    def test_thumbnail_feed_and_sitemap_consistency(self):
        hub = (ROOT / "articles.html").read_text(encoding="utf-8")
        self.assertEqual(hub.count('src="assets/articles/account-handover-controls-thumb-v1.webp"'), 2)
        for name in ("account-handover-controls-v1.jpg", "account-handover-controls-thumb-v1.webp"):
            asset = ROOT / "assets/articles" / name
            self.assertTrue(asset.is_file())
            self.assertLess(asset.stat().st_size, 200_000)
        sitemap = ElementTree.parse(ROOT / "sitemap.xml")
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        dates = {u.findtext("s:loc", namespaces=ns): u.findtext("s:lastmod", namespaces=ns) for u in sitemap.findall("s:url", ns)}
        for name, _ in PAGES:
            self.assertEqual(dates["https://shumaojs.com/articles/" + name], "2026-10-31")
        self.assertEqual((ROOT / "feed.xml").read_bytes(), build_feed(collect_articles(ROOT)))


if __name__ == "__main__":
    unittest.main()
