import shutil
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "google-budget-pacing.html": ("zh-CN", "USD"),
    "google-ads-bidding-budget-usa.html": ("en-US", "USD"),
    "google-ads-bidding-budget-hong-kong.html": ("zh-Hant-HK", "HKD"),
}


class CalculatorParser(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.nodes = []
        self.fallback = []
        self.in_fallback = False
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.nodes.append((tag, dict(attrs)))
        if tag == "p" and "data-budget-unavailable" in dict(attrs):
            self.in_fallback = True

    def handle_endtag(self, tag):
        if tag == "p":
            self.in_fallback = False

    def handle_data(self, data):
        if self.in_fallback:
            self.fallback.append(data)


class BudgetCalculatorMarkupTests(unittest.TestCase):
    def test_three_locales_have_honest_inactive_source_state(self):
        for name, (locale, currency) in PAGES.items():
            with self.subTest(page=name):
                parser = CalculatorParser((ROOT / "articles" / name).read_text(encoding="utf-8"))
                forms = [attrs for tag, attrs in parser.nodes if tag == "form" and "data-budget-calculator" in attrs]
                self.assertEqual(len(forms), 1)
                self.assertEqual(forms[0]["data-locale"], locale)
                self.assertEqual(forms[0]["data-currency"], currency)
                self.assertTrue(any(tag == "fieldset" and "disabled" in attrs for tag, attrs in parser.nodes))
                self.assertTrue(any(tag == "button" and attrs.get("type") == "reset" and "disabled" in attrs
                                    for tag, attrs in parser.nodes))
                self.assertTrue(any("budget-calculator-results" in attrs.get("class", "") and "hidden" in attrs
                                    for _, attrs in parser.nodes))
                self.assertIn("JavaScript", "".join(parser.fallback))

    def test_numeric_fields_are_required_and_preserve_explicit_zero(self):
        for name in PAGES:
            parser = CalculatorParser((ROOT / "articles" / name).read_text(encoding="utf-8"))
            inputs = [attrs for tag, attrs in parser.nodes if tag == "input"]
            self.assertEqual(len(inputs), 4, name)
            for attrs in inputs:
                self.assertEqual(attrs.get("type"), "number")
                self.assertIn("required", attrs)
                if "data-budget-days" in attrs or "data-budget-elapsed" in attrs:
                    self.assertEqual(attrs.get("step"), "1")
                if "data-budget-spent" in attrs or "data-budget-elapsed" in attrs:
                    self.assertEqual(attrs.get("min"), "0")

    def test_shared_asset_versions_match_across_locales(self):
        versions = {"budget-calculator.js": set(), "budget-calculator.css": set()}
        for name in PAGES:
            parser = CalculatorParser((ROOT / "articles" / name).read_text(encoding="utf-8"))
            seen = set()
            for _, attrs in parser.nodes:
                source = attrs.get("src") or attrs.get("href") or ""
                parsed = urlparse(source)
                key = Path(parsed.path).name
                if key in versions:
                    self.assertTrue(parsed.query.startswith("v="))
                    versions[key].add(parsed.query)
                    seen.add(key)
            self.assertEqual(seen, set(versions), name)
        self.assertTrue(all(len(values) == 1 for values in versions.values()))

    def test_shared_script_parses_in_node(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node is unavailable; browser verification is recorded separately")
        result = subprocess.run([node, "--check", str(ROOT / "budget-calculator.js")],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_tools_directory_exposes_a_native_calculator_link(self):
        parser = CalculatorParser((ROOT / "nav.html").read_text(encoding="utf-8"))
        links = [attrs for tag, attrs in parser.nodes if tag == "a" and
                 attrs.get("href") == "articles/google-budget-pacing.html#calculator"]
        self.assertEqual(len(links), 1)
        self.assertNotIn("target", links[0])


if __name__ == "__main__":
    unittest.main()
