import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from scripts.structured_data_check import SchemaParser


ROOT = Path(__file__).parents[1]


class MobileGuideParser(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.fields = {key: [] for key in ["data-mobile-metric", "data-mobile-diagnosis", "data-mobile-case"]}
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        for key in self.fields:
            if key in values:
                self.fields[key].append(values[key])


class MobilePerformanceGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "articles/website-speed-mobile.html").read_text(encoding="utf-8")

    def test_metrics_diagnoses_and_original_cases(self):
        parser = MobileGuideParser(self.source)
        self.assertEqual(parser.fields["data-mobile-metric"], ["lcp", "inp", "cls"])
        self.assertEqual(parser.fields["data-mobile-diagnosis"], ["late-image", "slow-document", "blocked-input", "layout-shift", "lab-field", "submission"])
        self.assertEqual(parser.fields["data-mobile-case"], ["no-field", "waiting-submit", "small-but-shifting"])

    def test_metric_scope_and_missing_data_boundaries(self):
        for phrase in ["不超过 2.5 秒", "不超过 200 毫秒", "不超过 0.1，无单位", "第 75 百分位",
                       "过去 28 天", "当前 URL 还是整个来源", "不能替它补一个 INP 通过",
                       "一次测试值或平均值", "不要对 LCP 图片使用懒加载", "不表示本文已经测得",
                       "不是本站实测、客户案例或效果数据", "测试提交会自动排除", "不保证转化或排名提升"]:
            self.assertIn(phrase, self.source)

    def test_identity_date_and_original_asset(self):
        parser = SchemaParser()
        parser.feed(self.source)
        article = next(json.loads(block) for block in parser.blocks if json.loads(block).get("@type") == "Article")
        self.assertEqual(article["headline"], "建站时如何减少移动端广告流量流失")
        self.assertEqual(article["datePublished"], "2026-09-11")
        self.assertEqual(article["dateModified"], "2026-10-28T21:21:44+08:00")
        self.assertIn('datetime="' + article["dateModified"] + '"', self.source)
        self.assertTrue(article["image"].endswith("mobile-landing-performance-v1.jpg"))
        for name in ["mobile-landing-performance-v1.jpg", "mobile-landing-performance-thumb-v1.webp"]:
            self.assertTrue((ROOT / "assets/articles" / name).is_file())
        self.assertIn('width="1200" height="675"', self.source)
        self.assertIn('width="480" height="270"', (ROOT / "articles.html").read_text(encoding="utf-8"))

    def test_conversions_and_functional_paths_remain_distinct(self):
        for href in ["landing-page-checklist.html", "conversion-tracking-basics.html", "sem-landing-tracking.html#acceptance-cases", "../google-ads.html#service-scope"]:
            self.assertIn('href="' + href + '"', self.source)
        for phrase in ["即时视觉反馈与业务处理完成是两件事", "不假设本站部署了表单数据库", "不能用点击事件替代成功事件", "需要他人复核的业务或隐私项单独确认"]:
            self.assertIn(phrase, self.source)


if __name__ == "__main__":
    unittest.main()
