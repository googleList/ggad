import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from scripts.structured_data_check import SchemaParser


ROOT = Path(__file__).parents[1]


class GuideParser(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.fields = {key: [] for key in ["data-seo-field", "data-seo-example", "data-seo-case"]}
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        for key in self.fields:
            if key in values:
                self.fields[key].append(values[key])


class SeoTitleGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "articles/seo-title-meta-basics.html").read_text(encoding="utf-8")

    def test_fields_examples_and_diagnoses(self):
        fields = GuideParser(self.source).fields
        self.assertEqual(fields["data-seo-field"], ["title", "heading", "social", "anchors", "description", "snippet"])
        self.assertEqual(fields["data-seo-example"], ["service", "article", "category", "product"])
        self.assertEqual(fields["data-seo-case"], ["old-template", "different-snippet", "language"])

    def test_identity_and_source_backed_optimization(self):
        parser = SchemaParser()
        parser.feed(self.source)
        article = next(json.loads(block) for block in parser.blocks if json.loads(block).get("@type") == "Article")
        self.assertEqual(article["headline"], "SEO 标题和描述怎么写更适合外贸网站")
        self.assertEqual(article["datePublished"], "2026-09-11")
        self.assertEqual(article["dateModified"], "2026-10-27T23:50:48+08:00")
        self.assertTrue(article["mainEntityOfPage"].endswith("/articles/seo-title-meta-basics.html"))
        self.assertIn('datetime="' + article["dateModified"] + '"', self.source)
        self.assertIn(article["description"], self.source)
        self.assertTrue(article["image"].endswith("seo-title-summary-plan-v1.jpg"))
        self.assertIn("seo-title-summary-plan-thumb-v1.webp", (ROOT / "articles.html").read_text(encoding="utf-8"))
        for fragment in ["/appearance/title-link", "/appearance/snippet", "/managing-multi-regional-sites", "/answer/7576553"]:
            self.assertIn(fragment, self.source)

    def test_claim_and_measurement_boundaries(self):
        for phrase in ["原创假设示例", "不是客户案例", "不表示本站销售该产品", "不是 Google Ads 的广告标题",
                       "没有统一的强制字符上限", "查询语言与访问者国家不是一回事", "缺少访问或询盘数据不填零",
                       "100 次展示、5 次点击", "200 次展示、6 次点击", "CTR 从 5% 变为 3%", "点击多了 1 次",
                       "不能直接归因", "查询未报告不等于零需求", "不增加收费、交付或排名承诺"]:
            self.assertIn(phrase, self.source)
        self.assertNotIn("若排名尚低，先补内容和内链", self.source)


if __name__ == "__main__":
    unittest.main()
