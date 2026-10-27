import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit

from scripts.collect_articles import (METADATA_FIELDS, collection_failed, encode_url,
                                     enrich_items, extract_detail_brief, main,
                                     metadata_only_item, parse_listing, render_report,
                                     safe_http_url, sanitize_research_data)


class CollectArticlesTests(unittest.TestCase):
    def test_encode_url_percent_encodes_chinese_path_and_query(self):
        encoded = encode_url("https://example.com/教程/开户?关键词=谷歌广告&lang=zh-CN")
        self.assertTrue(encoded.isascii())
        self.assertIn("%E6%95%99%E7%A8%8B", encoded)
        self.assertIn("%E8%B0%B7%E6%AD%8C%E5%B9%BF%E5%91%8A", encoded)
        self.assertEqual(urlsplit(encoded).netloc, "example.com")

    def test_partial_source_failures_keep_the_successful_collection(self):
        self.assertFalse(collection_failed(6, 3))

    def test_collection_fails_when_no_source_is_usable(self):
        self.assertTrue(collection_failed(2, 2))
        self.assertTrue(collection_failed(0, 0))

    def legacy_item(self):
        return {"id": "original-id", "title": "Google Ads planning guide", "url": "https://example.com/blog/guide",
                "source": "Example", "sourceUrl": "https://example.com/blog", "category": "Google Ads",
                "publishedAt": "2026-09-11", "summary": "DO_NOT_COPY_SUMMARY", "detailSummary": "DO_NOT_COPY_DETAIL",
                "outline": ["DO_NOT_COPY_OUTLINE"], "researchNotes": ["DO_NOT_COPY_BODY"],
                "imageUrl": "https://example.com/private-image.jpg", "imageAlt": "DO_NOT_COPY_IMAGE",
                "rewriteBrief": "Preserve source structure", "reviewStatus": "human_approved"}

    def test_detail_lookup_reads_only_title_metadata(self):
        markup = '<title>Fallback topic</title><meta property><meta property="og:title" content="广告素材核对">' \
                 '<meta name="description" content="DO_NOT_COPY_SUMMARY"><article><h2>DO_NOT_COPY_OUTLINE</h2>' \
                 '<p>DO_NOT_COPY_BODY</p><img src="https://example.com/private-image.jpg"></article>'
        with patch("scripts.collect_articles.fetch", return_value=markup):
            result = extract_detail_brief("https://example.com/blog/guide")
        self.assertEqual(result["detailTitle"], "广告素材核对")
        self.assertEqual(set(result), {"detailTitle", "detailFetchedAt"})
        self.assertNotIn("DO_NOT_COPY", json.dumps(result))

    def test_listing_preserves_discovery_without_source_excerpt_or_image(self):
        markup = '<a href="/zh/ads-guide"><h2>Google Ads launch preparation</h2>' \
                 '<p>DO_NOT_COPY_SUMMARY</p><img src="/image.jpg" alt="DO_NOT_COPY_IMAGE">' \
                 '<time>2026-09-11</time></a>'
        rows = parse_listing({"url": "https://www.kickads.co/zh/blog", "name": "Example"}, markup)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["url"], "https://www.kickads.co/zh/ads-guide")
        self.assertFalse({"summary", "imageUrl", "imageAlt", "outline", "researchNotes"}.intersection(rows[0]))
        self.assertNotIn("DO_NOT_COPY", json.dumps(rows))

    def test_legacy_items_are_allowlisted_and_reviews_not_inherited(self):
        row = metadata_only_item(self.legacy_item())
        self.assertEqual(row["id"], "original-id")
        self.assertEqual(row["publishedAt"], "2026-09-11")
        self.assertEqual(row["reviewStatus"], "pending_independent_fact_and_human_review")
        self.assertTrue(set(row).issubset(set(METADATA_FIELDS) | {"usage", "editorialBrief", "reviewStatus"}))
        self.assertNotIn("DO_NOT_COPY", json.dumps(row))
        self.assertIn("不虚构", row["editorialBrief"])
        self.assertNotIn("保留核心主题和信息结构", row["editorialBrief"])

    def test_default_listing_only_enrichment_fetches_nothing(self):
        with patch("scripts.collect_articles.fetch") as fetch:
            result = enrich_items([self.legacy_item()], limit=0)
        fetch.assert_not_called()
        self.assertEqual(len(result), 1)
        self.assertNotIn("DO_NOT_COPY", json.dumps(result))

    def test_non_http_and_credential_urls_are_not_rendered_or_fetched(self):
        for url in ["javascript:alert(1)", "data:text/html,anything", "file:///secret", "https://user:password@example.com/a"]:
            self.assertEqual(safe_http_url(url), "")
            item = {**self.legacy_item(), "url": url}
            with patch("scripts.collect_articles.fetch") as fetch:
                self.assertEqual(enrich_items([item], limit=1), [])
            fetch.assert_not_called()

    def test_report_cannot_hotlink_images_or_restore_legacy_content(self):
        report = render_report({"generatedAt": "2026-09-14", "items": [self.legacy_item()]})
        self.assertIn('href="https://example.com/blog/guide"', report)
        self.assertNotIn("<img", report)
        self.assertNotIn("private-image", report)
        self.assertNotIn("DO_NOT_COPY", report)
        self.assertIn("待分别确认", report)

    def test_sanitization_preserves_collection_age_and_is_idempotent(self):
        result = sanitize_research_data({"generatedAt": "2026-09-14", "sourcesChecked": 2, "items": [self.legacy_item()]})
        self.assertEqual(result["generatedAt"], "2026-09-14")
        self.assertEqual(result["collectionPolicyVersion"], 2)
        self.assertEqual(sanitize_research_data(result), result)

    def test_local_migration_does_not_fetch_or_refresh_collection_time(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "research.json"
            report = Path(directory) / "report.html"
            output.write_text(json.dumps({"generatedAt": "2026-09-14", "sourcesChecked": 2,
                                         "items": [self.legacy_item()]}), encoding="utf-8")
            with patch("scripts.collect_articles.fetch") as fetch, patch("sys.argv", ["collector", "--sanitize-existing", "--output", str(output), "--report", str(report)]):
                self.assertEqual(main(), 0)
            fetch.assert_not_called()
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(result["generatedAt"], "2026-09-14")
            self.assertIn("policyUpdatedAt", result)
            self.assertNotIn("DO_NOT_COPY", output.read_text(encoding="utf-8"))
            self.assertNotIn("<img", report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
