#!/usr/bin/env python3
"""Build an internal-link graph and flag indexable pages with weak discovery paths."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict, deque
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from seo_quality_check import EXCLUDED_DIRS, ROOT, PageParser, html_files


DEFAULT_JSON = ROOT / "data" / "internal-link-graph.json"
DEFAULT_REPORT = ROOT / "reports" / "internal-link-audit.md"


def page_key(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    return "/" if relative == "index.html" else f"/{relative}"


def href_key(source: Path, href: str) -> str | None:
    if href.startswith(("#", "mailto:", "tel:", "data:", "javascript:")):
        return None
    parsed = urlparse(href)
    if parsed.scheme or parsed.netloc:
        if parsed.netloc not in {"shumaojs.com", "www.shumaojs.com"}:
            return None
        clean = parsed.path or "/"
    else:
        clean = parsed.path
        if not clean:
            return None
        candidate = (ROOT / clean.lstrip("/")) if clean.startswith("/") else (source.parent / clean)
        try:
            clean = "/" + candidate.resolve().relative_to(ROOT.resolve()).as_posix()
        except ValueError:
            return None
    if clean in {"/index.html", ""}:
        return "/"
    if clean.endswith("/"):
        clean += "index.html"
    return clean


def collect_graph() -> tuple[dict[str, set[str]], dict[str, dict]]:
    graph: dict[str, set[str]] = defaultdict(set)
    metadata: dict[str, dict] = {}
    for path in html_files():
        key = page_key(path)
        parser = PageParser()
        parser.feed(path.read_text(encoding="utf-8"))
        indexable = "noindex" not in parser.robots and key != "/404.html"
        metadata[key] = {
            "title": parser.title,
            "canonical": parser.canonical,
            "indexable": indexable,
        }
        for target in parser.local_targets:
            resolved = href_key(path, target)
            if resolved and resolved != key:
                graph[key].add(resolved)
    return graph, metadata


def distances(graph: dict[str, set[str]], start: str = "/") -> dict[str, int]:
    result = {start: 0}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for target in graph.get(current, set()):
            if target not in result:
                result[target] = result[current] + 1
                queue.append(target)
    return result


def analyze() -> dict:
    graph, metadata = collect_graph()
    inbound: dict[str, set[str]] = defaultdict(set)
    for source, targets in graph.items():
        for target in targets:
            if target in metadata:
                inbound[target].add(source)
    depth = distances(graph)

    pages = []
    for key, values in metadata.items():
        if not values["indexable"]:
            continue
        sources = sorted(inbound.get(key, set()))
        pages.append(
            {
                "path": key,
                "title": values["title"],
                "inlinks": len(sources),
                "inlinkSources": sources,
                "outlinks": len([target for target in graph.get(key, set()) if target in metadata]),
                "clickDepth": depth.get(key),
                "orphan": key != "/" and not sources,
            }
        )
    pages.sort(key=lambda item: (item["orphan"] is False, item["inlinks"], item["path"]))
    return {
        "generatedAt": date.today().isoformat(),
        "method": "Static HTML link graph; navigation, body, and footer links are counted once per source page.",
        "summary": {
            "indexablePages": len(pages),
            "orphans": sum(1 for page in pages if page["orphan"]),
            "singleInlinkPages": sum(1 for page in pages if page["path"] != "/" and page["inlinks"] == 1),
            "unreachableFromHome": sum(1 for page in pages if page["clickDepth"] is None),
            "maxClickDepth": max((page["clickDepth"] or 0 for page in pages), default=0),
        },
        "pages": pages,
    }


def markdown(result: dict) -> str:
    summary = result["summary"]
    lines = [
        "# Internal Link Audit",
        "",
        f"Generated: {result['generatedAt']}",
        "",
        f"- Indexable pages: {summary['indexablePages']}",
        f"- Orphan pages: {summary['orphans']}",
        f"- Pages with one internal source: {summary['singleInlinkPages']}",
        f"- Pages unreachable from home: {summary['unreachableFromHome']}",
        f"- Maximum click depth: {summary['maxClickDepth']}",
        "",
        "## Pages needing attention",
        "",
        "| Page | Inlinks | Outlinks | Depth | Status |",
        "|---|---:|---:|---:|---|",
    ]
    weak = [page for page in result["pages"] if page["orphan"] or page["inlinks"] <= 1 or page["clickDepth"] is None]
    if not weak:
        lines.append("| None | - | - | - | No orphan or single-inlink pages |")
    else:
        for page in weak:
            status = "orphan" if page["orphan"] else "single source"
            if page["clickDepth"] is None:
                status += "; unreachable"
            depth = "-" if page["clickDepth"] is None else str(page["clickDepth"])
            lines.append(f"| `{page['path']}` | {page['inlinks']} | {page['outlinks']} | {depth} | {status} |")
    lines.extend(["", "## Notes", "", "This report measures crawl paths, not link equity. Repeated links from one page count as one source."])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--fail-on-orphans", action="store_true")
    args = parser.parse_args()

    result = analyze()
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.report_output.write_text(markdown(result), encoding="utf-8")
    summary = result["summary"]
    print(
        f"Audited {summary['indexablePages']} pages: {summary['orphans']} orphan(s), "
        f"{summary['singleInlinkPages']} single-inlink page(s), max depth {summary['maxClickDepth']}."
    )
    return 1 if args.fail_on_orphans and summary["orphans"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
