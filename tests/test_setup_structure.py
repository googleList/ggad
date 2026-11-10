import hashlib
import json
import unittest
from pathlib import Path

from scripts.generate_feed import article_schema

ROOT = Path(__file__).resolve().parents[1]


class SetupStructureTests(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / "articles/google-ads-basics.html").read_text(encoding="utf-8")

    def test_eight_existing_sections_are_byte_preserved_after_lf_normalization(self):
        proof = json.loads((ROOT / "reports/editorial/2026-11-01-setup-structure/protected-sections.json").read_text(encoding="utf-8"))
        self.assertEqual(len(proof["sections"]), 8)
        for section, expected in proof["sections"].items():
            with self.subTest(section=section):
                start = self.source.index(f'<section id="{section}">')
                end = self.source.index("</section>", start) + len("</section>")
                self.assertEqual(hashlib.sha256(self.source[start:end].encode("utf-8")).hexdigest(), expected)

    def test_duplicate_generic_blocks_removed_without_losing_intent_routes(self):
        for heading in ("Google Ads 是什么", "投放前要准备什么", "Google Ads 怎么计费", "哪些项目适合先做 Google Ads", "谷歌广告排名和自然搜索排名有什么不同"):
            self.assertNotIn(f"<h2>{heading}</h2>", self.source)
        self.assertLess(self.source.index("Google Ads 是 Google 的广告投放系统"), self.source.index('<section id="preparation">'))
        self.assertIn('href="google-seo-ranking-guide.html"', self.source)
        self.assertIn('href="google-search-ads-guide.html"', self.source)
        self.assertIn('href="google-ads-not-showing.html#checks"', self.source)

    def test_truthful_dates_and_existing_responsive_image(self):
        schema = article_schema(ROOT / "articles/google-ads-basics.html")
        self.assertEqual(schema["datePublished"], "2026-09-11")
        self.assertEqual(schema["dateModified"], "2026-11-10T15:25:30+08:00")
        self.assertIn('datetime="' + schema["dateModified"] + '"', self.source)
        self.assertIn("account-setup-readiness-thumb-v1.webp 480w", self.source)
        self.assertIn("account-setup-readiness-v1.jpg 1200w", self.source)
        self.assertTrue(schema["image"].endswith("account-setup-readiness-v1.jpg"))


if __name__ == "__main__":
    unittest.main()
