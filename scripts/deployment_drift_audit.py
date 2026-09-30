#!/usr/bin/env python3
"""Compare the local sitemap with production and verify production URL status."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree


SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


@dataclass
class UrlResult:
    url: str
    status: int | None
    error: str | None = None


def parse_sitemap(xml_text: str) -> set[str]:
    root = ElementTree.fromstring(xml_text)
    return {
        node.text.strip()
        for node in root.findall("sm:url/sm:loc", SITEMAP_NS)
        if node.text and node.text.strip()
    }


def fetch_text(url: str, timeout: int = 20) -> str:
    request = Request(url, headers={"User-Agent": "ShumaoJS-Deployment-Audit/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def check_url(url: str, timeout: int = 20) -> UrlResult:
    request = Request(url, method="HEAD", headers={"User-Agent": "ShumaoJS-Deployment-Audit/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return UrlResult(url=url, status=response.status)
    except HTTPError as error:
        return UrlResult(url=url, status=error.code, error=str(error.reason))
    except URLError as error:
        return UrlResult(url=url, status=None, error=str(error.reason))


def compare_sitemaps(local_urls: set[str], live_urls: set[str]) -> dict[str, list[str]]:
    return {
        "missingFromProduction": sorted(local_urls - live_urls),
        "productionOnly": sorted(live_urls - local_urls),
        "shared": sorted(local_urls & live_urls),
    }


def build_report(
    local_urls: set[str],
    live_urls: set[str],
    checker: Callable[[str], UrlResult] = check_url,
) -> dict[str, object]:
    comparison = compare_sitemaps(local_urls, live_urls)
    checks = [checker(url) for url in comparison["missingFromProduction"]]
    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "localUrlCount": len(local_urls),
        "productionUrlCount": len(live_urls),
        **comparison,
        "missingUrlStatus": [asdict(result) for result in checks],
    }


def markdown(report: dict[str, object], live_sitemap_url: str) -> str:
    missing = report["missingFromProduction"]
    production_only = report["productionOnly"]
    lines = [
        "# Production deployment drift audit",
        "",
        f"Generated: {report['generatedAt']}",
        f"Production sitemap: {live_sitemap_url}",
        "",
        "## Summary",
        "",
        f"- Local sitemap URLs: {report['localUrlCount']}",
        f"- Production sitemap URLs: {report['productionUrlCount']}",
        f"- Missing from production sitemap: {len(missing)}",
        f"- Production-only URLs: {len(production_only)}",
        "",
        "## Missing from production",
        "",
    ]
    status_by_url = {item["url"]: item for item in report["missingUrlStatus"]}
    if missing:
        for url in missing:
            result = status_by_url[url]
            status = result["status"] if result["status"] is not None else "request failed"
            lines.append(f"- `{status}` {url}")
    else:
        lines.append("- None")
    lines.extend(["", "## Production-only URLs", ""])
    lines.extend(f"- {url}" for url in production_only) if production_only else lines.append("- None")
    lines.extend([
        "",
        "## Interpretation",
        "",
        "A local page is not deployable or indexable evidence until it appears on production and returns a successful HTTP response. Submit the production sitemap to Search Console only after the deployment difference is cleared.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-sitemap", default="sitemap.xml")
    parser.add_argument("--live-sitemap", default="https://shumaojs.com/sitemap.xml")
    parser.add_argument("--json-output", default="reports/deployment-drift.json")
    parser.add_argument("--markdown-output", default="reports/deployment-drift.md")
    parser.add_argument("--fail-on-drift", action="store_true")
    args = parser.parse_args()

    local_xml = Path(args.local_sitemap).read_text(encoding="utf-8")
    live_xml = fetch_text(args.live_sitemap)
    report = build_report(parse_sitemap(local_xml), parse_sitemap(live_xml))

    json_path = Path(args.json_output)
    markdown_path = Path(args.markdown_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(markdown(report, args.live_sitemap), encoding="utf-8")

    print(
        f"Deployment audit: {report['localUrlCount']} local, "
        f"{report['productionUrlCount']} production, "
        f"{len(report['missingFromProduction'])} missing from production."
    )
    return 1 if args.fail_on_drift and report["missingFromProduction"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
