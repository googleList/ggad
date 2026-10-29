import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from scripts.structured_data_check import SchemaParser

ROOT = Path(__file__).parents[1]
URL = "https://shumaojs.com/articles/google-seo-ranking-guide.html"


class OrganicGuideParser(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.fields = {key: [] for key in ["data-seo-diagnosis", "data-seo-case"]}
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        for key in self.fields:
            if key in values:
                self.fields[key].append(values[key])


class OrganicSeoGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "articles/google-seo-ranking-guide.html").read_text(encoding="utf-8")
        cls.plan = json.loads((ROOT / "data/seo-keywords.json").read_text(encoding="utf-8"))

    def test_eight_diagnoses_and_four_original_cases(self):
        parser = OrganicGuideParser(self.source)
        self.assertEqual(parser.fields["data-seo-diagnosis"],
                         ["access", "indexability", "canonical", "intent", "content", "snippet", "links", "experience"])
        self.assertEqual(parser.fields["data-seo-case"],
                         ["not-indexed", "weak-visibility", "ctr-with-mix", "click-no-enquiry"])

    def test_four_seeds_with_owner_confirmed_organic_intent(self):
        self.assertEqual(self.plan["prioritySeedQueries"], ["谷歌代投", "谷歌开户", "谷歌排名", "谷歌广告"])
        organic = next(c for c in self.plan["clusters"] if "谷歌排名" in c.get("primaryKeywords", []))
        self.assertEqual(organic["targetUrl"], URL)
        self.assertEqual(organic["intent"], "informational")
        self.assertIsNone(organic["evidence"]["googleSearchVolume"])
        self.assertIsNone(organic["evidence"]["seoDifficulty"])
        paid = next(c for c in self.plan["clusters"] if c["targetUrl"].endswith("/google-search-ads-guide.html"))
        self.assertNotIn("谷歌排名", paid["primaryKeywords"])
        self.assertIn("谷歌广告排名", paid["primaryKeywords"])

    def test_duplicate_service_plan_consolidated_without_losing_observation(self):
        plans = [c for c in self.plan["clusters"]
                 if c["targetUrl"] == "https://shumaojs.com/google-ads.html" and c["intent"] == "commercial"]
        self.assertEqual(len(plans), 1)
        self.assertEqual(plans[0]["priority"], "primary")
        self.assertIn("Google Ads 投放咨询", plans[0]["supportingKeywords"])
        signal = plans[0]["observedSearchSignal"]
        self.assertEqual([(r["country"], r["impressions"]) for r in signal["directCountryQueryPage"]],
                         [("US", 2), ("HK", 1)])
        self.assertFalse(signal["countryDemandScaleVerified"])

    def test_real_new_publication_and_aligned_article_assets(self):
        parser = SchemaParser()
        parser.feed(self.source)
        article = next(json.loads(b) for b in parser.blocks if json.loads(b).get("@type") == "Article")
        self.assertEqual(article["mainEntityOfPage"], URL)
        self.assertEqual(article["articleSection"], "SEO")
        self.assertEqual(article["datePublished"], "2026-10-29T22:10:36+08:00")
        self.assertEqual(article["dateModified"], article["datePublished"])
        self.assertIn('datetime="' + article["datePublished"] + '"', self.source)
        self.assertIn(article["headline"], self.source)
        for name in ["organic-seo-ranking-plan-v1.jpg", "organic-seo-ranking-plan-thumb-v1.webp"]:
            self.assertTrue((ROOT / "assets/articles" / name).is_file())

    def test_navigation_keeps_paid_and_organic_distinct(self):
        hub = (ROOT / "articles.html").read_text(encoding="utf-8")
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        for href in ["articles/google-seo-ranking-guide.html", "articles/google-search-ads-guide.html"]:
            self.assertIn('href="' + href + '"', hub)
        self.assertIn('href="articles/google-seo-ranking-guide.html"', home)
        self.assertIn('data-article-category="seo" data-search-priority="95"', hub)
        for phrase in ["投放广告不会提高自然搜索排名", "不是本站实测、客户效果或排名预测",
                       "没有后端记录就不要计算成交提升", "搜索量继续写未知", "CTR 为 3%", "CTR 为 10%"]:
            self.assertIn(phrase, self.source)

    def test_mobile_acceptance_does_not_approve_new_guide(self):
        state = json.loads((ROOT / "reports/seo-growth-state.json").read_text(encoding="utf-8"))
        mobile = state["editorialWorkflow"]["latestMobilePerformanceReview"]
        self.assertEqual(mobile["status"], "accepted")
        self.assertEqual(mobile["ownerReply"], "内容符合，可保留")
        self.assertEqual(mobile["contentRevision"], "7b08e4baa52382f31643726b538751bd6c031216")
        self.assertNotEqual(state["editorialWorkflow"]["latestOrganicSeoReview"]["status"], "accepted")


if __name__ == "__main__":
    unittest.main()
