import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from scripts.structured_data_check import SchemaParser


ROOT = Path(__file__).parents[1]


class AudienceParser(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.fields = {key: [] for key in ["data-remarketing-control", "data-remarketing-case"]}
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        for key in self.fields:
            if key in values:
                self.fields[key].append(values[key])


class RemarketingGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "articles/remarketing-basics.html").read_text(encoding="utf-8")

    def test_control_and_case_inventory(self):
        fields = AudienceParser(self.source).fields
        self.assertEqual(fields["data-remarketing-control"], ["source", "eligibility", "observation", "targeting", "expansion", "exclusions"])
        self.assertEqual(fields["data-remarketing-case"], ["small-list", "new-users", "sensitive"])

    def test_platform_and_measurement_boundaries(self):
        for phrase in ["观察不会限制投放范围", "优化型定位可超出所选受众", "不等于 GA4 总用户数",
                       "截至本次核对", "近 30 天至少 100", "旧客户列表", "购买或抓取的名单不能当作自有客户资料",
                       "原创教学情境", "不是客户案例", "未知状态不填成零", "不替代当地法律意见",
                       "本教程不增加数据上传、价格或效果承诺"]:
            self.assertIn(phrase, self.source)
        self.assertNotIn("直接放进广告 URL、标签参数或数据源", self.source)
        for source_id in ["7558048", "6299717", "7068417", "10537509", "143465"]:
            self.assertIn("/answer/" + source_id, self.source)

    def test_article_identity_and_original_asset_metadata(self):
        parser = SchemaParser()
        parser.feed(self.source)
        article = next(json.loads(block) for block in parser.blocks if json.loads(block).get("@type") == "Article")
        self.assertEqual(article["headline"], "再营销广告基础：适合什么时候做")
        self.assertEqual(article["datePublished"], "2026-09-11")
        self.assertEqual(article["dateModified"], "2026-10-28T15:42:29+08:00")
        self.assertTrue(article["mainEntityOfPage"].endswith("/articles/remarketing-basics.html"))
        self.assertIn('datetime="' + article["dateModified"] + '"', self.source)
        self.assertTrue(article["image"].endswith("remarketing-audience-boundaries-v1.jpg"))
        self.assertIn("remarketing-audience-boundaries-thumb-v1.webp", (ROOT / "articles.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
