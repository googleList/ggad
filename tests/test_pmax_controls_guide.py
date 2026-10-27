import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from scripts.structured_data_check import SchemaParser


class ControlParser(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.fields = {key: [] for key in ["data-pmax-control", "data-pmax-example"]}
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        for key in self.fields:
            if key in values:
                self.fields[key].append(values[key])


class PmaxControlsGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (Path(__file__).parents[1] / "articles/performance-max-basics.html").read_text(encoding="utf-8")

    def test_control_and_hypothetical_case_inventory(self):
        fields = ControlParser(self.source).fields
        self.assertEqual(fields["data-pmax-control"], ["campaign", "goals", "creative", "signals", "urls", "products"])
        self.assertEqual(fields["data-pmax-example"], ["geography", "destination", "lead-quality"])

    def test_scope_and_measurement_boundaries(self):
        for phrase in ["素材组不是一份独立国家预算", "受众信号不是封闭受众",
                       "页面 Feed 不是扩展开启时的网址白名单", "商品 Feed 不是页面 Feed",
                       "次要动作进入自定义目标时也可用于出价", "合格状态未知",
                       "不是客户案例", "不扩大已约定的服务承诺"]:
            self.assertIn(phrase, self.source)
        self.assertNotIn("完全不同的品类、国家和客户类型塞进同一组", self.source)

    def test_original_identity_and_market_links_remain(self):
        parser = SchemaParser()
        parser.feed(self.source)
        article = next(json.loads(block) for block in parser.blocks if json.loads(block).get("@type") == "Article")
        self.assertEqual(article["headline"], "Performance Max 怎么投？适用条件与上线清单")
        self.assertEqual(article["datePublished"], "2026-09-11")
        self.assertTrue(article["mainEntityOfPage"].endswith("/articles/performance-max-basics.html"))
        for slug in ["performance-max-lead-generation-usa.html", "performance-max-lead-generation-hong-kong.html"]:
            self.assertIn(f'href="{slug}"', self.source)


if __name__ == "__main__":
    unittest.main()
