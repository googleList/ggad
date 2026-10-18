import unittest
from urllib.parse import urlsplit

from scripts.collect_articles import collection_failed, encode_url


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


if __name__ == "__main__":
    unittest.main()
