import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from article_index import parse_index, synchronize, validate_article_index


def card(href, title, priority=0, extra=""):
    return (
        f'<article class="article-card" data-article-card data-search-priority="{priority}" {extra}>'
        f'<img src="image.png" alt="Example"><h3><a href="{href}">{title}</a></h3>'
        '<p>Keep this description exactly.</p></article>'
    )


def page(cards):
    schema = {"@context": "https://schema.org", "@type": "CollectionPage",
              "mainEntity": {"@type": "ItemList", "numberOfItems": 0, "itemListElement": []}}
    return (
        '<html><head><link rel="canonical" href="https://shumaojs.com/articles.html">'
        f'<script type="application/ld+json">{json.dumps(schema)}</script></head><body>'
        + "\n\n".join(cards) + '</body></html>'
    )


class ArticleIndexTests(unittest.TestCase):
    def test_priority_order_static_visibility_and_schema(self):
        source = page([card("articles/old.html", "Other", extra='hidden data-article-page="2"'),
                       card("articles/main.html", "Google &amp; Ads", 100)])
        fixed = synchronize(source)
        parsed = parse_index(fixed)
        self.assertEqual([c["href"] for c in parsed.cards], ["articles/main.html", "articles/old.html"])
        self.assertNotIn("hidden", fixed)
        self.assertNotIn("data-article-page", fixed)
        listing = parsed.schemas[0][2]["mainEntity"]
        self.assertEqual(listing["numberOfItems"], 2)
        self.assertEqual(listing["itemListElement"][0], {
            "@type": "ListItem", "position": 1, "url": "https://shumaojs.com/articles/main.html",
            "name": "Google & Ads",
        })
        self.assertEqual(validate_article_index(fixed), [])
        self.assertTrue(validate_article_index(source))

    def test_preserves_body_and_stable_equal_priority_order(self):
        source = page([card("a.html", "<span>A</span>", 20), card("b.html", "B", 20)])
        fixed = synchronize(source)
        before, after = parse_index(source), parse_index(fixed)
        for original, result in zip(before.cards, after.cards):
            self.assertEqual(original["href"], result["href"])
            self.assertEqual(source[original["start"] + original["opening_length"]:original["end"]],
                             fixed[result["start"] + result["opening_length"]:result["end"]])
        self.assertEqual(synchronize(fixed), fixed)

    def test_duplicate_urls_are_rejected(self):
        self.assertTrue(validate_article_index(page([card("a.html", "A"), card("a.html", "B")])))

    def test_does_not_silently_remove_interleaved_content(self):
        source = page([card("a.html", "A"), card("b.html", "B")])
        source = source.replace("</article>\n\n", "</article><aside>Keep me</aside>", 1)
        with self.assertRaisesRegex(ValueError, "non-card content"):
            synchronize(source)

    def test_malformed_priority_and_missing_schema_are_rejected(self):
        source = page([card("a.html", "A")])
        self.assertTrue(validate_article_index(source.replace('priority="0"', 'priority="bad"')))
        self.assertTrue(validate_article_index(source.replace('"CollectionPage"', '"WebPage"')))

    def test_schema_title_and_url_drift_are_repaired(self):
        fixed = synchronize(page([card("a.html", "A")]))
        self.assertTrue(validate_article_index(fixed.replace('"name": "A"', '"name": "Wrong"')))
        self.assertTrue(validate_article_index(fixed.replace('"url": "https://shumaojs.com/a.html"',
                                                             '"url": "https://shumaojs.com/wrong.html"')))


if __name__ == "__main__":
    unittest.main()
