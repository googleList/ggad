import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "google-search-keywords": "search-keyword-intent-groups",
    "conversion-tracking-basics": "conversion-evidence-plan",
    "landing-page-checklist": "landing-page-preflight",
    "google-search-ads-guide": "search-terms-review",
    "seo-title-meta-basics": "seo-title-summary-plan",
}


class CoverParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sources = []
        self.cover = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "source":
            self.sources.append(attrs)
        if tag == "img" and "article-cover" in attrs.get("class", "").split():
            self.cover = attrs


class ArticleCoverDensityTests(unittest.TestCase):
    def test_mobile_candidates_keep_small_image_and_existing_large_fallback(self):
        for slug, image in PAGES.items():
            with self.subTest(slug=slug):
                parser = CoverParser()
                article = ROOT / "articles" / f"{slug}.html"
                parser.feed(article.read_text(encoding="utf-8"))
                self.assertEqual(len(parser.sources), 1)
                source = parser.sources[0]
                self.assertEqual(source["media"], "(max-width: 600px)")
                self.assertEqual(source["sizes"], "calc(100vw - 36px)")
                candidates = [tuple(item.strip().split()) for item in source["srcset"].split(",")]
                self.assertEqual(candidates, [
                    (f"../assets/articles/{image}-thumb-v1.webp", "480w"),
                    (f"../assets/articles/{image}-v1.jpg", "1200w"),
                ])
                self.assertEqual(parser.cover["src"], candidates[1][0])
                self.assertEqual((parser.cover["width"], parser.cover["height"]), ("1200", "675"))
                self.assertTrue(parser.cover["alt"].strip())
                for candidate, _ in candidates:
                    self.assertTrue((article.parent / candidate).is_file())


if __name__ == "__main__":
    unittest.main()
