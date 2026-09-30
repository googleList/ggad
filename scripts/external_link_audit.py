#!/usr/bin/env python3
"""Audit external HTTP links without treating anti-bot responses as broken links."""

from __future__ import annotations

import argparse
import json
import ssl
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

try:
    from seo_quality_check import ROOT, PageParser, html_files
except ModuleNotFoundError:  # Imported as scripts.external_link_audit by the test suite.
    from scripts.seo_quality_check import ROOT, PageParser, html_files


DEFAULT_JSON = ROOT / "data" / "external-link-audit.json"
DEFAULT_REPORT = ROOT / "reports" / "external-link-audit.md"
LOCAL_HOSTS = {"shumaojs.com", "www.shumaojs.com"}
BLOCKED_STATUSES = {401, 403, 405, 406, 409, 418, 429, 451}
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140 Safari/537.36"
)


def collect_links() -> dict[str, list[str]]:
    links: dict[str, set[str]] = defaultdict(set)
    for path in html_files():
        parser = PageParser()
        parser.feed(path.read_text(encoding="utf-8"))
        for target in parser.local_targets:
            parsed = urlparse(target)
            if parsed.scheme not in {"http", "https"} or parsed.netloc in LOCAL_HOSTS:
                continue
            links[target].add(path.relative_to(ROOT).as_posix())
    return {url: sorted(sources) for url, sources in sorted(links.items())}


def request_url(url: str, timeout: float) -> dict:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    try:
        with urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:
            status = response.status
            final_url = response.geturl()
    except HTTPError as error:
        status = error.code
        final_url = error.geturl()
    except (URLError, TimeoutError, OSError) as error:
        return {"status": None, "finalUrl": None, "result": "unverified", "detail": str(error)}

    if 200 <= status < 400:
        result = "ok"
    elif status in BLOCKED_STATUSES or status >= 500:
        result = "unverified"
    elif status in {404, 410}:
        result = "broken"
    else:
        result = "review"
    return {"status": status, "finalUrl": final_url, "result": result, "detail": ""}


def audit(hosts: set[str], timeout: float, workers: int) -> dict:
    links = collect_links()
    if hosts:
        links = {url: sources for url, sources in links.items() if urlparse(url).netloc in hosts}

    checked = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(request_url, url, timeout): url for url in links}
        for future in as_completed(futures):
            url = futures[future]
            result = future.result()
            checked.append({"url": url, "sources": links[url], **result})
    checked.sort(key=lambda item: (item["result"], item["url"]))
    counts = {key: sum(item["result"] == key for item in checked) for key in ("ok", "broken", "review", "unverified")}
    return {
        "generatedAt": date.today().isoformat(),
        "method": "GET requests with redirects; 401/403/405/406/409/418/429/451 and 5xx are unverified, not broken.",
        "hosts": sorted(hosts),
        "summary": {"checked": len(checked), **counts},
        "links": checked,
    }


def markdown(result: dict) -> str:
    summary = result["summary"]
    lines = [
        "# External Link Audit",
        "",
        f"Generated: {result['generatedAt']}",
        "",
        f"- URLs checked: {summary['checked']}",
        f"- Reachable: {summary['ok']}",
        f"- Clearly broken (404/410): {summary['broken']}",
        f"- Needs review: {summary['review']}",
        f"- Unverified due to blocking, server errors, or network failure: {summary['unverified']}",
        "",
        "Automated checks are evidence for review, not proof that blocked links are unavailable to visitors.",
        "",
        "## Non-success results",
        "",
        "| Result | HTTP | URL | First source | Detail |",
        "|---|---:|---|---|---|",
    ]
    exceptions = [item for item in result["links"] if item["result"] != "ok"]
    if not exceptions:
        lines.append("| None | - | - | - | All checked URLs returned 2xx or 3xx |")
    else:
        for item in exceptions:
            status = "-" if item["status"] is None else str(item["status"])
            detail = item["detail"].replace("|", "\\|")
            lines.append(
                f"| {item['result']} | {status} | {item['url']} | `{item['sources'][0]}` | {detail} |"
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", action="append", default=[], help="Only audit this exact host; repeatable.")
    parser.add_argument("--timeout", type=float, default=12.0)
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--fail-on-broken", action="store_true")
    args = parser.parse_args()

    result = audit(set(args.host), args.timeout, args.workers)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.report_output.write_text(markdown(result), encoding="utf-8")
    summary = result["summary"]
    print(
        f"Checked {summary['checked']} external URLs: {summary['ok']} reachable, "
        f"{summary['broken']} broken, {summary['review']} review, {summary['unverified']} unverified."
    )
    return 1 if args.fail_on_broken and summary["broken"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
