import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class Elements(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.items = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.items.append((tag, dict(attrs)))


class ToolNavigationTests(unittest.TestCase):
    def setUp(self):
        self.html = (ROOT / "nav.html").read_text(encoding="utf-8")
        self.elements = Elements(self.html).items

    def test_both_panels_are_available_before_javascript(self):
        panels = [attrs for _, attrs in self.elements if "data-tool-panel" in attrs]
        self.assertEqual({p["data-tool-panel"] for p in panels}, {"ai", "standard"})
        self.assertTrue(all("hidden" not in p for p in panels))
        self.assertTrue(all(p.get("tabindex") == "0" for p in panels))

    def test_each_sidebar_anchor_and_tab_has_a_real_target(self):
        ids = [attrs["id"] for _, attrs in self.elements if "id" in attrs]
        self.assertEqual(len(ids), len(set(ids)))
        jumps = [attrs for _, attrs in self.elements if "data-tool-jump" in attrs]
        self.assertEqual(len(jumps), 17)
        for link in jumps:
            self.assertIn(link["href"][1:], ids)
        for _, attrs in self.elements:
            if "data-tool-tab" in attrs:
                self.assertIn(attrs["aria-controls"], ids)

    def test_inert_tabs_are_hidden_until_tool_navigation_is_ready(self):
        css = (ROOT / "styles.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"\.tool-tabs\s*\{\s*display:\s*none;")
        self.assertRegex(css, r"\.tool-navigation-ready \.tool-tabs\s*\{\s*display:\s*inline-flex;")
        self.assertRegex(css, r"\.tool-navigation-ready \.tool-tabs\s*\{\s*display:\s*grid;")

    def test_tool_script_is_deferred_and_only_requested_by_directory(self):
        script = "assets/tool-navigation-v1.js"
        matches = [attrs for tag, attrs in self.elements if tag == "script" and attrs.get("src") == script]
        self.assertEqual(len(matches), 1)
        self.assertIn("defer", matches[0])
        self.assertIn('src="site-v20260930.js?v=tools-20261030"', self.html)
        self.assertIn('href="styles.css?v=tools-20261030"', self.html)
        self.assertTrue((ROOT / script).is_file())
        for page in [*(ROOT.glob("*.html")), *(ROOT / "articles").glob("*.html")]:
            if page.name != "nav.html":
                self.assertNotIn(script, page.read_text(encoding="utf-8"), str(page))
        self.assertNotIn("data-tool-tab", (ROOT / "site-v20260930.js").read_text(encoding="utf-8"))

    def test_tool_script_parses_in_ci_node(self):
        result = subprocess.run(["node", "--check", str(ROOT / "assets/tool-navigation-v1.js")],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
