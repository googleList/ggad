import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

from scripts.article_index import parse_index
from scripts.generate_feed import article_schema

ROOT = Path(__file__).parents[1]
PATH = "articles/llms-txt-ai-search-guide.html"
TITLE = "llms.txt 是什么？作用、写法与 Google 搜索边界"


class GuideParser(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.boundaries, self.cases, self.links = [], [], []
        self.example, self.in_code = "", False
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key, values in [("data-llms-boundary", self.boundaries), ("data-llms-case", self.cases)]:
            if key in attrs:
                values.append(attrs[key])
        if tag == "a":
            self.links.append(attrs.get("href", ""))
        if tag == "code":
            self.in_code = True

    def handle_data(self, value):
        if self.in_code:
            self.example += value

    def handle_endtag(self, tag):
        if tag == "code":
            self.in_code = False


def markdown_links(text):
    return re.findall(r"^- \[([^\]]+)\]\((https://shumaojs\.com/[^\s)]*)\):", text, flags=re.M)


class LlmsGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / PATH).read_text(encoding="utf-8")
        cls.guide = GuideParser(cls.source)
        cls.article = article_schema(ROOT / PATH)
        cls.directory = (ROOT / "llms.txt").read_text(encoding="utf-8")

    def test_six_boundaries_four_hypothetical_cases_and_seven_anchors(self):
        self.assertEqual(self.guide.boundaries, ["proposal", "robots", "sitemap", "access", "full-file", "outcome"])
        self.assertEqual(self.guide.cases, ["search-goal", "blocked-target", "stale-version", "large-bundle"])
        for fragment in ["scope", "file-boundaries", "example", "release-checks", "situations", "measurement", "next-step"]:
            self.assertIn("#" + fragment, self.guide.links)
            self.assertIn(f'id="{fragment}"', self.source)
        for phrase in ["不是搜索引擎索引库", "不是本站日志、AI 引用实测、客户结果或排名预测", "不会因此提高 Google 搜索展示或排名", "缺数据记未知"]:
            self.assertIn(phrase, self.source)

    def test_original_publication_and_corrected_title(self):
        self.assertEqual(self.article["datePublished"], "2026-09-11")
        self.assertEqual(self.article["dateModified"], "2026-10-30T18:32:42+08:00")
        self.assertEqual(self.article["headline"], TITLE)
        self.assertEqual(self.article["mainEntityOfPage"], "https://shumaojs.com/" + PATH)
        self.assertIn('datetime="' + self.article["dateModified"] + '"', self.source)
        hub = (ROOT / "articles.html").read_text(encoding="utf-8")
        cards = parse_index(hub).cards
        self.assertEqual(len(cards), 49)
        card = next(c for c in cards if c["href"] == PATH)
        self.assertEqual(card["name"], TITLE)
        self.assertIn(("data-article-category", "geo"), card["attrs"])

    def test_actual_directory_and_example_only_link_existing_public_pages(self):
        for text in [self.directory, self.guide.example]:
            links = markdown_links(text)
            self.assertGreaterEqual(len(links), 6)
            for _, url in links:
                parsed = urlparse(url)
                target = (ROOT / unquote(parsed.path).lstrip("/")).resolve()
                if parsed.path == "/":
                    target = ROOT / "index.html"
                self.assertTrue(target.is_relative_to(ROOT.resolve()), url)
                self.assertTrue(target.is_file(), url)
                self.assertEqual(target.suffix, ".html", url)
        self.assertTrue(self.directory.startswith("# 振润达\n\n> "))
        self.assertNotIn("## 关键词与内容主题", self.directory)
        self.assertNotIn("广告广告管理", self.directory)
        self.assertNotIn("91530103MACQG57N6E", self.directory)
        self.assertIn("最后更新：2026-10-30", self.directory)

    def test_representative_labels_match_current_article_headlines(self):
        labels = {url: label for label, url in markdown_links(self.directory)}
        for path in [PATH, "articles/google-seo-ranking-guide.html", "articles/google-search-ads-guide.html", "articles/google-ads-basics.html"]:
            self.assertEqual(labels["https://shumaojs.com/" + path], article_schema(ROOT / path)["headline"])

    def test_primary_sources_and_original_responsive_cover(self):
        for url in ["https://llmstxt.org/", "https://llmstxt.org/changes.html", "https://developers.google.com/search/docs/fundamentals/ai-optimization-guide?hl=zh-cn", "https://www.mintlify.com/docs/ai/llmstxt"]:
            self.assertIn(url, self.guide.links)
        self.assertIn("https://shumaojs.com/assets/articles/llms-reading-guide-v1.jpg", self.article["image"])
        for name in ["llms-reading-guide-v1.jpg", "llms-reading-guide-thumb-v1.webp"]:
            self.assertTrue((ROOT / "assets/articles" / name).is_file())
        self.assertIn("不表示已提供对应 Markdown 副本", self.source)

    def test_research_limits_and_separate_human_scope(self):
        brief = json.loads((ROOT / "reports/editorial/2026-10-30-llms-boundaries/brief.json").read_text(encoding="utf-8"))
        self.assertEqual(brief["targetUrl"], self.article["mainEntityOfPage"])
        self.assertIsNone(brief["googleSearchVolume"])
        self.assertIsNone(brief["seoDifficulty"])
        self.assertFalse(brief["localizedDemandScaleVerified"])
        self.assertEqual(len(brief["titleCandidates"]), 3)
        self.assertEqual(len(brief["outline"]), 7)
        self.assertEqual(brief["humanReviewScope"], "This llms.txt article revision only; no inherited crawler, trust, service, organic-pillar or actual account approval.")


if __name__ == "__main__":
    unittest.main()
