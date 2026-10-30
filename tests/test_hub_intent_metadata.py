import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from scripts.structured_data_check import SchemaParser
from scripts.article_index import parse_index

ROOT = Path(__file__).parents[1]


class HubMetadataParser(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.h1 = ""
        self.active = None
        self.meta = {}
        self.ids = set()
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if "id" in values:
            self.ids.add(values["id"])
        if tag in {"title", "h1"}:
            self.active = tag
        if tag == "meta":
            self.meta[values.get("name") or values.get("property")] = values.get("content")

    def handle_endtag(self, tag):
        if tag == self.active:
            self.active = None

    def handle_data(self, value):
        if self.active:
            setattr(self, self.active, getattr(self, self.active) + value)


class HubIntentMetadataTests(unittest.TestCase):
    def test_research_briefs_reuse_real_pages_and_anchors(self):
        brief = json.loads((ROOT / "reports/editorial/2026-10-30-primary-intent/briefs.json").read_text(encoding="utf-8"))
        self.assertEqual({t["seed"] for t in brief["topics"]}, {"谷歌开户", "谷歌排名", "谷歌广告"})
        for topic in brief["topics"]:
            target = (ROOT / topic["target"]).resolve()
            self.assertTrue(target.is_relative_to(ROOT.resolve()))
            parsed = HubMetadataParser(target.read_text(encoding="utf-8"))
            self.assertTrue(set(topic["anchors"]) <= parsed.ids)
            self.assertIsNone(topic["googleSearchVolume"])
            self.assertFalse(topic["USMarketDemandScaleVerified"])
            self.assertFalse(topic["HKMarketDemandScaleVerified"])
            self.assertEqual(len(topic["titleCandidates"]), 3)

    def test_visible_and_structured_names_agree_with_organic_intent(self):
        source = (ROOT / "articles.html").read_text(encoding="utf-8")
        p = HubMetadataParser(source)
        self.assertEqual(p.h1, "谷歌代投、开户与 SEO 排名指南")
        self.assertEqual(p.title, p.meta["og:title"])
        self.assertEqual(p.title, p.meta["twitter:title"])
        self.assertTrue(p.title.startswith(p.h1))
        schema = SchemaParser()
        schema.feed(source)
        collection = next(json.loads(b) for b in schema.blocks if json.loads(b).get("@type") == "CollectionPage")
        self.assertEqual(collection["name"], p.h1)
        self.assertEqual(p.meta["description"], p.meta["og:description"])
        self.assertEqual(p.meta["description"], p.meta["twitter:description"])
        self.assertIn("自然搜索 SEO 排名", p.meta["description"])
        self.assertIn("分清广告位置与自然排名", p.meta["description"])
        self.assertIn("广告位置教程另行说明广告评级", source)

    def test_native_routes_and_international_content_remain(self):
        source = (ROOT / "articles.html").read_text(encoding="utf-8")
        parsed = parse_index(source)
        urls = {c["href"] for c in parsed.cards}
        for href in ["articles/google-seo-ranking-guide.html", "articles/google-search-ads-guide.html",
                     "articles/google-ads-basics.html", "articles/google-ads-monthly-reporting-usa.html",
                     "articles/google-ads-monthly-reporting-hong-kong.html"]:
            self.assertIn(href, urls)
        self.assertEqual(HubMetadataParser(source).meta["robots"], "index,follow")
        self.assertNotIn("guaranteed", HubMetadataParser(source).title.lower())


if __name__ == "__main__":
    unittest.main()
