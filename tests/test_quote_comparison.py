import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path
from scripts.generate_feed import article_schema, build_feed, collect_articles

ROOT = Path(__file__).resolve().parents[1]


class Elements(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.nodes = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.nodes.append((tag, dict(attrs)))


class QuoteComparisonTests(unittest.TestCase):
    def setUp(self):
        self.html = (ROOT / "articles/google-search-ads-cost-guide.html").read_text(encoding="utf-8")
        self.nodes = Elements(self.html).nodes

    def test_fixed_point_arithmetic_and_invalid_boundaries(self):
        run = subprocess.run(["node", str(ROOT / "tests/quote_comparison_cases.cjs")], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)

    def test_honest_source_fallback_and_required_inputs(self):
        self.assertEqual(sum("data-quote-comparison" in a for _, a in self.nodes), 1)
        self.assertEqual(sum("data-quote-offer" in a for _, a in self.nodes), 2)
        self.assertTrue(any("data-quote-fields" in a and "disabled" in a for _, a in self.nodes))
        self.assertTrue(any("data-quote-results" in a and "hidden" in a for _, a in self.nodes))
        self.assertTrue(any(a.get("type") == "reset" and "disabled" in a for _, a in self.nodes))
        for tag, attrs in self.nodes:
            if tag == "input":
                self.assertIn("required", attrs)
                self.assertIn("min", attrs)
                self.assertIn("max", attrs)
        self.assertIn("JavaScript", self.html)
        self.assertIn("USD 10,500", self.html)
        self.assertIn("公式、舍入", self.html)

    def test_truthful_scope_and_no_quote_input_transmission(self):
        for text in ("不是本站报价", "不会换汇", "空白不等于零", "设置费只加一次", "本演算脚本不发送或持久保存输入"):
            self.assertIn(text, self.html)
        script = (ROOT / "assets/quote-comparison-v1.js").read_text(encoding="utf-8")
        for token in ("fetch(", "XMLHttpRequest", "localStorage", "sessionStorage", "sendBeacon", "innerHTML"):
            self.assertNotIn(token, script)
        self.assertIn('form.addEventListener("submit", event => event.preventDefault())', script)

    def test_scoped_assets_discovery_and_preserved_publication(self):
        for asset in ("quote-comparison-v1.js", "quote-comparison-v1.css"):
            self.assertIn(asset + "?v=20261031", self.html)
            self.assertLess((ROOT / "assets" / asset).stat().st_size, 18000)
        schema = article_schema(ROOT / "articles/google-search-ads-cost-guide.html")
        self.assertEqual(schema["datePublished"], "2026-09-11")
        self.assertEqual(schema["dateModified"], "2026-10-31T08:45:37+08:00")
        self.assertEqual((ROOT / "feed.xml").read_bytes(), build_feed(collect_articles(ROOT)))
        self.assertIn('href="articles/google-search-ads-cost-guide.html#quote-comparison"', (ROOT / "nav.html").read_text(encoding="utf-8"))
        for other in (ROOT / "articles").glob("*.html"):
            if other.name != "google-search-ads-cost-guide.html":
                self.assertNotIn("quote-comparison-v1.js", other.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
