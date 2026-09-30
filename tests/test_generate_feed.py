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


if __name__ == "__main__":
    unittest.main()
