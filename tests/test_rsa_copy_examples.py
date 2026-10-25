import unittest
import unicodedata
from html.parser import HTMLParser
from pathlib import Path


class CopyParser(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.examples = {"headline": [], "description": []}
        self.current = None
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        kind = dict(attrs).get("data-rsa-copy")
        if kind in self.examples:
            self.current = (tag, kind, [])

    def handle_data(self, data):
        if self.current:
            self.current[2].append(data)

    def handle_endtag(self, tag):
        if self.current and self.current[0] == tag:
            self.examples[self.current[1]].append("".join(self.current[2]).strip())
            self.current = None


def example_units(text):
    # These frozen examples use only basic Han, ASCII and listed CJK punctuation.
    # This is not an arbitrary-input Google Ads validation or dynamic-insertion engine.
    for char in text:
        if not ("\u4e00" <= char <= "\u9fff" or char.isascii() or char in "，。；、"):
            raise ValueError(f"Unreviewed example character: {char!r}")
    return sum(2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1 for char in text)


class RsaCopyExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = (Path(__file__).parents[1] / "articles/google-ads-responsive-search-ads.html").read_text(encoding="utf-8")
        cls.examples = CopyParser(source).examples

    def test_headline_examples_are_distinct_and_fit(self):
        headlines = self.examples["headline"]
        self.assertEqual(len(headlines), 15)
        self.assertEqual(len(set(headlines)), len(headlines))
        for text in headlines:
            with self.subTest(text=text):
                self.assertLessEqual(example_units(text), 30)

    def test_description_examples_are_distinct_and_fit(self):
        descriptions = self.examples["description"]
        self.assertEqual(len(descriptions), 4)
        self.assertEqual(len(set(descriptions)), len(descriptions))
        for text in descriptions:
            with self.subTest(text=text):
                self.assertLessEqual(example_units(text), 90)

    def test_published_counting_examples_and_supported_character_boundary(self):
        self.assertEqual(example_units("谷歌广告代投咨询"), 16)
        self.assertEqual(example_units("Google Ads 投放管理"), 19)
        with self.assertRaises(ValueError):
            example_units("\U0001f600")


if __name__ == "__main__":
    unittest.main()
