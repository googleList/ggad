import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TriageParser(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.states = []
        self.examples = []
        self.links = []
        self.forms = 0
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "data-verification-state" in attrs:
            self.states.append(attrs["data-verification-state"])
        if "data-verification-example" in attrs:
            self.examples.append(attrs["data-verification-example"])
        if tag == "a":
            self.links.append(attrs.get("href"))
        if tag == "form":
            self.forms += 1


class SetupVerificationTriageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = (ROOT / "articles/google-ads-basics.html").read_text(encoding="utf-8")
        start = source.index('<section id="verification-triage">')
        cls.section = source[start:source.index("</section>", start) + len("</section>")]

    def test_six_states_three_hypothetical_examples_and_no_document_collection(self):
        parsed = TriageParser(self.section)
        self.assertEqual(parsed.states, ["required", "review", "documents", "relationships", "paused", "suspended"])
        self.assertEqual(parsed.examples, ["name", "agency", "policy"])
        self.assertEqual(parsed.forms, 0)
        self.assertIn('aria-labelledby="verification-triage-caption" tabindex="0"', self.section)

    def test_four_official_sources_and_independent_suspension_boundary(self):
        links = TriageParser(self.section).links
        for target in ("answer/15577076", "table/15333054", "answer/11938893", "answer/9703665"):
            self.assertIn(f"https://support.google.com/adspolicy/{target}?hl=en", links)
        for phrase in ("验证成功不是自动解封", "不能通过买号、借号或新号绕过限制", "管理员权限，不自动证明品牌授权", "不能代替真实业务关系"):
            self.assertIn(phrase, self.section)

    def test_hypotheses_privacy_and_no_universal_timeline(self):
        for phrase in ("没有统一适用于所有账户的材料包或完成时限", "不加工主体名称或日期", "以上是教学假设", "不是客户案例、本站资质或实际申诉结果", "记录中不保存密码或验证码", "以原账户通知为准", "不承诺恢复投放"):
            self.assertIn(phrase, self.section)


if __name__ == "__main__":
    unittest.main()
