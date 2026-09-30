import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from scripts.external_link_audit import request_url


class FakeResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def geturl(self):
        return "https://example.com/final"


class ExternalLinkAuditTests(unittest.TestCase):
    @patch("scripts.external_link_audit.urlopen", return_value=FakeResponse())
    def test_success_is_reachable(self, _urlopen):
        result = request_url("https://example.com", 1)
        self.assertEqual(result["result"], "ok")
        self.assertEqual(result["status"], 200)

    @patch(
        "scripts.external_link_audit.urlopen",
        side_effect=HTTPError("https://example.com/missing", 404, "Not Found", {}, None),
    )
    def test_404_is_broken(self, _urlopen):
        result = request_url("https://example.com/missing", 1)
        self.assertEqual(result["result"], "broken")

    @patch(
        "scripts.external_link_audit.urlopen",
        side_effect=HTTPError("https://example.com/blocked", 403, "Forbidden", {}, None),
    )
    def test_anti_bot_response_is_unverified(self, _urlopen):
        result = request_url("https://example.com/blocked", 1)
        self.assertEqual(result["result"], "unverified")

    @patch("scripts.external_link_audit.urlopen", side_effect=URLError("timeout"))
    def test_network_failure_is_unverified(self, _urlopen):
        result = request_url("https://example.com", 1)
        self.assertEqual(result["result"], "unverified")
        self.assertIsNone(result["status"])


if __name__ == "__main__":
    unittest.main()
