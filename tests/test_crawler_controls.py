import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from scripts.structured_data_check import SchemaParser

ROOT = Path(__file__).parents[1]


class CrawlerParser(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.fields = {k: [] for k in ["data-crawler-role", "data-crawler-control", "data-crawler-case"]}
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        for key in self.fields:
            if key in values:
                self.fields[key].append(values[key])


class CrawlerControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "articles/googlebot-ai-crawlers-seo-geo.html").read_text(encoding="utf-8")

    def test_roles_controls_and_hypothetical_cases(self):
        p = CrawlerParser(self.source)
        self.assertEqual(p.fields["data-crawler-role"], ["googlebot", "adsbot", "extended"])
        self.assertEqual(p.fields["data-crawler-control"], ["robots", "noindex", "nosnippet", "max-snippet", "data-nosnippet", "access"])
        self.assertEqual(p.fields["data-crawler-case"], ["blocked-noindex", "extended-search", "claimed-bot", "ads-only"])

    def test_scope_and_verification_boundaries(self):
        for text in ["没有单独的 HTTP User-Agent", "不影响网站列入 Google 搜索", "忽略 robots.txt 的全局",
                     "不是访问认证", "Google 必须能抓取并读取指令", "布尔属性写成 false",
                     "正向解析", "核对是否返回原 IP", "不是本站真实日志", "本文没有修改"]:
            self.assertIn(text, self.source)
        for path in ["google-common-crawlers", "google-special-case-crawlers", "robots-meta-tag",
                     "block-indexing", "robots/intro", "verify-google-requests", "appearance/ai-features"]:
            self.assertIn(path, self.source)

    def test_identity_publication_and_new_cover(self):
        p = SchemaParser()
        p.feed(self.source)
        a = next(json.loads(b) for b in p.blocks if json.loads(b).get("@type") == "Article")
        self.assertEqual(a["datePublished"], "2026-09-11")
        self.assertEqual(a["dateModified"], "2026-10-29T22:21:37+08:00")
        self.assertEqual(a["headline"], "Googlebot 是什么？网络爬虫和 AI 爬虫对 SEO/GEO 的影响")
        self.assertEqual(a["articleSection"], "GEO")
        self.assertTrue(a["image"].endswith("crawler-control-scope-v1.jpg"))
        for file in ["crawler-control-scope-v1.jpg", "crawler-control-scope-thumb-v1.webp"]:
            self.assertTrue((ROOT / "assets/articles" / file).is_file())

    def test_tutorial_does_not_apply_restrictive_controls(self):
        self.assertIn('<meta name="robots" content="index,follow">', self.source)
        self.assertNotIn('<meta name="robots" content="noindex', self.source)
        self.assertNotIn('<span data-nosnippet', self.source)
        self.assertEqual((ROOT / "robots.txt").read_text(encoding="utf-8").strip(),
                         "User-agent: *\nAllow: /\n\nSitemap: https://shumaojs.com/sitemap.xml")
        self.assertIn('href="google-seo-ranking-guide.html#seo-diagnosis"', self.source)
        self.assertIn('href="https://t.me/qichuanggg"', self.source)


if __name__ == "__main__":
    unittest.main()
