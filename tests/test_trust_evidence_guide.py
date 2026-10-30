import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

from scripts.article_index import parse_index
from scripts.generate_feed import article_schema

ROOT = Path(__file__).parents[1]
PATH = "articles/website-trust-pages.html"


class TrustParser(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.evidence = []
        self.cases = []
        self.links = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "data-trust-evidence" in attrs:
            self.evidence.append(attrs["data-trust-evidence"])
        if "data-trust-case" in attrs:
            self.cases.append(attrs["data-trust-case"])
        if tag == "a":
            self.links.append(attrs.get("href", ""))


class TrustEvidenceGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / PATH).read_text(encoding="utf-8")
        cls.parsed = TrustParser(cls.source)
        cls.article = article_schema(ROOT / PATH)

    def test_six_evidence_rows_and_four_hypothetical_cases(self):
        self.assertEqual(self.parsed.evidence, ["identity", "scope", "fees", "contact", "data", "claims"])
        self.assertEqual(self.parsed.cases, ["identity-mismatch", "fee-mismatch", "data-mismatch", "verification-not-policy"])
        for section in ["trust-boundary", "evidence-checks", "consistency", "trust-cases", "review-records", "questions", "next-step"]:
            self.assertIn("#" + section, self.parsed.links)
            self.assertIn(f'id="{section}"', self.source)
        self.assertIn("以下均为假设，不是本站实测、客户案例、账号诊断或申诉结果", self.source)

    def test_publication_and_identity_boundaries(self):
        self.assertEqual(self.article["datePublished"], "2026-09-11")
        self.assertEqual(self.article["dateModified"], "2026-10-30T18:14:15+08:00")
        self.assertIn('datetime="' + self.article["dateModified"] + '"', self.source)
        self.assertEqual(self.article["mainEntityOfPage"], "https://shumaojs.com/" + PATH)
        self.assertEqual(self.article["headline"], "广告投放站点必须补齐哪些信任页面")
        for phrase in ["不是增加几个页面就能", "未确认的登记字段不能从旧截图复制回来", "没有账号反馈不记", "不建议统一价格、退费比例或付款期限", "增强型转化等专门功能有各自条件"]:
            self.assertIn(phrase, self.source)
        self.assertNotIn("91530103MACQG57N6E", self.source)

    def test_primary_sources_and_service_journey_links(self):
        for policy in ["6020955?hl=zh-Hans", "6368661?hl=en", "6086450?hl=zh-Hans", "6020956?hl=zh-Hans"]:
            self.assertIn("https://support.google.com/adspolicy/answer/" + policy, self.parsed.links)
        for link in ["google-search-ads-cost-guide.html#management-fees", "landing-page-checklist.html#preflight", "sem-landing-tracking.html#acceptance-cases", "../google-ads.html#service-scope", "../company.html", "../privacy.html", "../terms.html"]:
            self.assertIn(link, self.parsed.links)

    def test_original_cover_and_website_card_retained(self):
        self.assertEqual(self.article["image"], "https://shumaojs.com/assets/articles/site-trust-evidence-v1.jpg")
        for name in ["site-trust-evidence-v1.jpg", "site-trust-evidence-thumb-v1.webp"]:
            self.assertTrue((ROOT / "assets/articles" / name).is_file())
            self.assertIn(name, self.source)
        hub = (ROOT / "articles.html").read_text(encoding="utf-8")
        parsed = parse_index(hub)
        self.assertEqual(len(parsed.cards), 49)
        card = next(c for c in parsed.cards if c["href"] == PATH)
        self.assertIn(("data-article-category", "website"), card["attrs"])
        source = hub[card["start"]:card["end"]]
        self.assertIn("site-trust-evidence-thumb-v1.webp", source)
        self.assertIn("2026-10-30", source)

    def test_research_scope_does_not_invent_market_size_or_human_acceptance(self):
        brief = json.loads((ROOT / "reports/editorial/2026-10-30-trust-evidence/brief.json").read_text(encoding="utf-8"))
        self.assertEqual(brief["targetUrl"], self.article["mainEntityOfPage"])
        self.assertIsNone(brief["googleSearchVolume"])
        self.assertIsNone(brief["seoDifficulty"])
        self.assertFalse(brief["localizedMarketDemandVerified"])
        self.assertEqual(len(brief["titleCandidates"]), 3)
        self.assertEqual(len(brief["outline"]), 7)
        self.assertEqual(brief["humanReviewScope"], "This trust-page revision only; independent from every accepted article and actual account or legal review.")


if __name__ == "__main__":
    unittest.main()
