import unittest
from pathlib import Path
from html.parser import HTMLParser
from scripts.generate_feed import build_feed, collect_articles

ROOT = Path(__file__).resolve().parents[1]


class LearningResourcesTests(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / "articles/seo-course-learning-path.html").read_text(encoding="utf-8")

    def test_official_resources_and_learning_anchors_exist(self):
        for anchor in ("official-resources", "practice-tasks", "course-evidence"):
            self.assertIn(f'id="{anchor}"', self.source)
            self.assertIn(f'href="#{anchor}"', self.source)
        for path in ("how-search-works", "seo-starter-guide", "search-console-start", "9012289", "7576553", "9205520"):
            self.assertIn(path, self.source)

    def test_exercises_and_evidence_are_distinct_and_counted(self):
        for name, expected in (("data-learning-resources", 6), ("data-learning-tasks", 4), ("data-course-evidence", 4)):
            class Counter(HTMLParser):
                def __init__(self):
                    super().__init__(); self.active = False; self.count = 0
                def handle_starttag(self, tag, attrs):
                    if name in dict(attrs): self.active = True
                    if self.active and tag == "li": self.count += 1
                def handle_endtag(self, tag):
                    if tag in ("ol", "ul"): self.active = False
            parser = Counter(); parser.feed(self.source)
            self.assertEqual(parser.count, expected)

    def test_true_publication_and_unknown_measurement_boundaries(self):
        self.assertIn('"datePublished": "2026-09-11"', self.source)
        self.assertIn('"dateModified": "2026-10-31T07:51:47+08:00"', self.source)
        for text in ("没有账户权限", "未知", "中文查询不自动等于中国市场", "不保证收录", "不是本站课程"):
            self.assertIn(text, self.source)

    def test_feed_contains_current_article_revision(self):
        feed = build_feed(collect_articles(ROOT)).decode("utf-8")
        self.assertIn("seo-course-learning-path.html", feed)
        self.assertEqual((ROOT / "feed.xml").read_bytes(), build_feed(collect_articles(ROOT)))
