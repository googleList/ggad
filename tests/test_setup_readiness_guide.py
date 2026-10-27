import json
import unittest
from html.parser import HTMLParser
from pathlib import Path


class ReadinessParser(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.fields = {name: [] for name in ["data-setup-check", "data-setup-example"]}
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        for name in self.fields:
            if name in attributes:
                self.fields[name].append(attributes[name])


class SetupReadinessGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (Path(__file__).parents[1] / "articles/google-ads-basics.html").read_text(encoding="utf-8")

    def test_readiness_and_original_teaching_case_inventory(self):
        fields = ReadinessParser(self.source).fields
        self.assertEqual(fields["data-setup-check"], ["delivery", "measurement", "intent", "maturity", "economics"])
        self.assertEqual(fields["data-setup-example"], ["failure", "irrelevant", "unknown"])

    def test_conditional_not_calendar_and_unknown_not_zero(self):
        for phrase in ["不是统一的否词、加预算或判定失败门槛", "真实故障应及时处理",
                       "点击按钮不等于收到询盘", "不同转化动作应分别观察",
                       "销售尚未反馈不是零个合格线索", "预测不是已经收到的询盘",
                       "报告不是全部查询清单", "不是本站客户案例", "不编造稳定周期或统一最低点击数"]:
            self.assertIn(phrase, self.source)
        self.assertNotIn("第 8 到 14 天开始排除无关搜索词", self.source)

    def test_original_identity_and_preparation_remain(self):
        from scripts.structured_data_check import SchemaParser
        parser = SchemaParser()
        parser.feed(self.source)
        article = next(json.loads(block) for block in parser.blocks if json.loads(block).get("@type") == "Article")
        self.assertEqual(article["datePublished"], "2026-09-11")
        self.assertEqual(article["headline"], "谷歌广告开户流程：账户准备与投放入门")
        self.assertTrue(article["mainEntityOfPage"].endswith("/articles/google-ads-basics.html"))
        for anchor in ["preparation", "setup", "location", "verification", "costs", "troubleshooting"]:
            self.assertIn(f'id="{anchor}"', self.source)


if __name__ == "__main__":
    unittest.main()
