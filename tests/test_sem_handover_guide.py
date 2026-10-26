import unittest
from html.parser import HTMLParser
from pathlib import Path


class HandoverParser(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.fields = {key: [] for key in ["data-handover-field", "data-acceptance-case", "data-handover-example"]}
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        for key in self.fields:
            if key in attributes:
                self.fields[key].append(attributes[key])


class SemHandoverGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (Path(__file__).parents[1] / "articles/sem-landing-tracking.html").read_text(encoding="utf-8")

    def test_original_handover_and_failure_case_inventory(self):
        fields = HandoverParser(self.source).fields
        self.assertEqual(fields["data-handover-field"], ["intent", "destination", "success", "measurement", "privacy", "release"])
        self.assertEqual(fields["data-acceptance-case"], ["success", "invalid", "failure", "repeat", "consent"])
        self.assertEqual(fields["data-handover-example"], ["defect", "visibility", "unknown"])

    def test_safety_and_evidence_boundaries_remain_explicit(self):
        for phrase in ["内部对照不等于把个人信息发给分析工具", "不应在其中传递姓名、邮箱、电话",
                       "自定义目标时也可用于出价", "不要求三个后台实时逐条相等",
                       "预览通过不替代发布后复测", "不表示本站或客户账户已经通过这些测试",
                       "不能把这次事件算作真实询盘", "无 Cookie 信号", "不自动扩大服务承诺"]:
            self.assertIn(phrase, self.source)
        self.assertNotIn("确认广告平台、分析工具和后台订单能够用同一标识核对", self.source)


if __name__ == "__main__":
    unittest.main()
