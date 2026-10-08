import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "deployment_drift_audit.py"
SPEC = importlib.util.spec_from_file_location("deployment_drift_audit", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class DeploymentDriftAuditTests(unittest.TestCase):
    def test_parse_and_compare_sitemaps(self):
        local = MODULE.parse_sitemap(
            '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            '<url><loc>https://example.com/</loc></url>'
            '<url><loc>https://example.com/new.html</loc></url></urlset>'
        )
        live = {"https://example.com/", "https://example.com/old.html"}
        result = MODULE.compare_sitemaps(local, live)
        self.assertEqual(result["missingFromProduction"], ["https://example.com/new.html"])
        self.assertEqual(result["productionOnly"], ["https://example.com/old.html"])
        self.assertEqual(result["shared"], ["https://example.com/"])

    def test_report_checks_only_missing_urls(self):
        checked = []

        def fake_check(url):
            checked.append(url)
            return MODULE.UrlResult(url=url, status=404, error="Not Found")

        report = MODULE.build_report(
            {"https://example.com/", "https://example.com/new.html"},
            {"https://example.com/"},
            checker=fake_check,
        )
        self.assertEqual(checked, ["https://example.com/new.html"])
        self.assertEqual(report["missingUrlStatus"][0]["status"], 404)

    def test_protocol_redirect_requires_https_final_url(self):
        passing = MODULE.build_report(
            {"https://example.com/"},
            {"https://example.com/"},
            protocol_url="http://example.com/",
            protocol_checker=lambda url: MODULE.UrlResult(
                url=url, status=200, final_url="https://example.com/", redirect_statuses=[301]
            ),
        )
        failing = MODULE.build_report(
            {"https://example.com/"},
            {"https://example.com/"},
            protocol_url="http://example.com/",
            protocol_checker=lambda url: MODULE.UrlResult(
                url=url, status=200, final_url="http://example.com/", redirect_statuses=[]
            ),
        )
        self.assertTrue(passing["protocolRedirectOk"])
        self.assertFalse(failing["protocolRedirectOk"])

    def test_protocol_redirect_must_be_permanent(self):
        for redirect_status in (302, 307):
            report = MODULE.build_report(
                {"https://example.com/"},
                {"https://example.com/"},
                protocol_url="http://example.com/",
                protocol_checker=lambda url, status=redirect_status: MODULE.UrlResult(
                    url=url,
                    status=200,
                    final_url="https://example.com/",
                    redirect_statuses=[status],
                ),
            )
            self.assertFalse(report["protocolRedirectOk"])

    def test_www_alias_must_redirect_to_canonical_https_host(self):
        report = MODULE.build_report(
            {"https://example.com/"},
            {"https://example.com/"},
            alias_urls=["http://www.example.com/", "https://www.example.com/"],
            canonical_url="https://example.com/",
            alias_checker=lambda url: MODULE.UrlResult(
                url=url,
                status=200,
                final_url=("https://example.com/" if url.startswith("https://") else "http://example.com/"),
                redirect_statuses=[301],
            ),
        )
        self.assertFalse(report["hostAliasRedirectsOk"])


if __name__ == "__main__":
    unittest.main()
