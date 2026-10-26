import unittest
from datetime import date
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).parents[1]
LOCALES = ("usa", "hong-kong")


class TimelineParser(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.rows = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if "data-report-stage" in attributes:
            self.rows.append((attributes["data-report-stage"], attributes.get("data-event-date")))


class ReportingDateExampleTests(unittest.TestCase):
    def source(self, locale):
        return (ROOT / f"articles/google-ads-monthly-reporting-{locale}.html").read_text(encoding="utf-8")

    def test_both_locales_keep_the_same_original_timeline(self):
        expected = [("interaction", "2026-09-29"), ("form", "2026-10-03"),
                    ("qualified", "2026-10-08"), ("upload", "2026-10-10")]
        for locale in LOCALES:
            with self.subTest(locale=locale):
                self.assertEqual(TimelineParser(self.source(locale)).rows, expected)

    def test_calendar_order_crosses_month_without_equating_upload_and_event(self):
        # This validates the teaching timeline, not an attribution engine.
        for locale in LOCALES:
            dates = [date.fromisoformat(value) for _, value in TimelineParser(self.source(locale)).rows]
            self.assertEqual(dates, sorted(set(dates)))
            self.assertEqual([value.month for value in dates], [9, 10, 10, 10])
            self.assertNotEqual(dates[2], dates[3])

    def test_reporting_boundaries_are_explicit_in_each_language(self):
        boundaries = {
            "usa": ["Upload date is not conversion date", "not two customers", "quality is unknown, not zero",
                    "does not measure the acquisition cost of the October click cohort", "original hypothetical"],
            "hong-kong": ["上傳日不是轉換日", "不能把兩個操作相加當作兩名客戶", "品質未知，不填零",
                          "十月點擊群組的獲客成本", "原創假設"],
        }
        for locale, phrases in boundaries.items():
            source = self.source(locale)
            for phrase in phrases:
                with self.subTest(locale=locale, phrase=phrase):
                    self.assertIn(phrase, source)


if __name__ == "__main__":
    unittest.main()
