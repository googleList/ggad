import unittest

from scripts.generate_feed import build_feed, rfc_date


class GenerateFeedTests(unittest.TestCase):
    def test_build_feed_includes_language_and_permalink(self):
        payload = build_feed(
            [
                {
                    "title": "Guide",
                    "description": "Useful guide.",
                    "url": "https://shumaojs.com/articles/guide.html",
                    "published": "2026-09-29",
                    "modified": "2026-09-29",
                    "language": "en-US",
                    "category": "SEM",
                }
            ]
        ).decode("utf-8")
        self.assertIn("https://shumaojs.com/articles/guide.html", payload)
        self.assertIn("<dc:language>en-US</dc:language>", payload)
        self.assertIn('isPermaLink="true"', payload)

    def test_rfc_date_is_utc(self):
        self.assertEqual(rfc_date("2026-09-29"), "Tue, 29 Sep 2026 00:00:00 +0000")

    def test_rfc_datetime_preserves_the_actual_instant(self):
        self.assertEqual(rfc_date("2026-10-20T16:21:48+08:00"), "Tue, 20 Oct 2026 08:21:48 +0000")
        self.assertEqual(rfc_date("2026-10-20T08:21:48Z"), "Tue, 20 Oct 2026 08:21:48 +0000")
        with self.assertRaises(ValueError):
            rfc_date("2026-10-20T08:21:48")

    def test_feed_last_build_compares_actual_instants_not_date_strings(self):
        from xml.etree import ElementTree

        base = {
            "title": "Guide", "description": "Useful guide.",
            "published": "2026-09-29", "language": "en-US", "category": "SEM",
        }
        articles = [
            dict(base, url="https://example.com/a", modified="2026-10-20T01:00:00+08:00"),
            dict(base, url="https://example.com/b", modified="2026-10-19T18:00:00Z"),
        ]
        root = ElementTree.fromstring(build_feed(articles))
        self.assertEqual(root.findtext("channel/lastBuildDate"), "Mon, 19 Oct 2026 18:00:00 +0000")


if __name__ == "__main__":
    unittest.main()
