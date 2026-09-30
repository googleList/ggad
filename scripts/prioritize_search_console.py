#!/usr/bin/env python3
"""Build a transparent US/HK SEO priority report from Search Console CSV exports."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = ROOT / "data" / "search-console"
DEFAULT_JSON = ROOT / "data" / "search-console-priorities.json"
DEFAULT_REPORT = ROOT / "reports" / "search-console-priorities.md"

ALIASES = {
    "query": {"query", "queries", "top queries", "search query", "查询", "查詢", "搜索查询", "搜尋查詢", "关键字", "關鍵字"},
    "page": {"page", "pages", "top pages", "landing page", "页面", "網頁", "网页", "到达网页", "到達網頁"},
    "country": {"country", "countries", "country/region", "国家/地区", "國家/地區", "地区", "地區"},
    "clicks": {"clicks", "click", "点击次数", "點擊次數", "点击", "點擊"},
    "impressions": {"impressions", "impression", "展示次数", "曝光次数", "曝光次數", "展示"},
    "ctr": {"ctr", "average ctr", "平均点击率", "平均點閱率", "点击率", "點閱率"},
    "position": {"position", "average position", "平均排名", "平均位置", "排名"},
}

COUNTRY_MARKETS = {
    "united states": "US",
    "united states of america": "US",
    "usa": "US",
    "us": "US",
    "美国": "US",
    "美國": "US",
    "hong kong": "HK",
    "hong kong sar china": "HK",
    "hong kong sar": "HK",
    "hk": "HK",
    "香港": "HK",
}


def normalize_header(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower().replace("_", " "))


def header_map(fieldnames: Iterable[str] | None) -> dict[str, str]:
    mapped: dict[str, str] = {}
    for raw in fieldnames or []:
        normalized = normalize_header(raw)
        for canonical, aliases in ALIASES.items():
            if normalized in aliases:
                mapped[canonical] = raw
                break
    return mapped


def number(value: str | None) -> float:
    if not value:
        return 0.0
    cleaned = value.strip().replace(",", "").replace("，", "")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def ratio(value: str | None) -> float:
    if not value:
        return 0.0
    cleaned = value.strip().replace("%", "")
    result = number(cleaned)
    return result / 100 if "%" in value or result > 1 else result


def infer_market(country: str, filename: str) -> str:
    normalized = normalize_header(country)
    if normalized in COUNTRY_MARKETS:
        return COUNTRY_MARKETS[normalized]
    name = filename.lower().replace("_", "-")
    if re.search(r"(^|[- ])(us|usa|united-states)([- .]|$)", name):
        return "US"
    if re.search(r"(^|[- ])(hk|hong-kong)([- .]|$)", name):
        return "HK"
    return "UNASSIGNED"


def position_weight(position: float) -> float:
    if position <= 0:
        return 0.2
    if position <= 3:
        return 0.25
    if position <= 10:
        return 1.0
    if position <= 20:
        return 1.25
    if position <= 50:
        return 0.65
    return 0.25


def action_for(position: float, ctr: float, page: str) -> str:
    if not page:
        return "Map the query to one canonical target page before editing content."
    if 0 < position <= 3 and ctr < 0.03:
        return "Test title and description alignment; preserve the ranking page."
    if 3 < position <= 10:
        return "Improve intent coverage, snippet clarity, and contextual internal links."
    if 10 < position <= 20:
        return "Expand the relevant section and add contextual internal links from stronger cluster pages."
    if position > 20:
        return "Recheck intent-to-page fit before deciding whether to strengthen or create content."
    return "Validate indexing and measurement before assigning content work."


def read_rows(paths: list[Path]) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    notes: list[str] = []
    for path in paths:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = header_map(reader.fieldnames)
            required = {"clicks", "impressions", "ctr", "position"}
            missing = sorted(required - fields.keys())
            if missing:
                notes.append(f"Skipped {path.name}: missing {', '.join(missing)} columns.")
                continue
            if "query" not in fields and "page" not in fields:
                notes.append(f"Skipped {path.name}: no query or page dimension.")
                continue

            accepted = 0
            for raw in reader:
                query = (raw.get(fields.get("query", ""), "") or "").strip()
                page = (raw.get(fields.get("page", ""), "") or "").strip()
                country = (raw.get(fields.get("country", ""), "") or "").strip()
                impressions = number(raw.get(fields["impressions"]))
                if impressions <= 0:
                    continue
                rows.append(
                    {
                        "query": query,
                        "page": page,
                        "country": country,
                        "market": infer_market(country, path.name),
                        "clicks": number(raw.get(fields["clicks"])),
                        "impressions": impressions,
                        "ctr": ratio(raw.get(fields["ctr"])),
                        "position": number(raw.get(fields["position"])),
                        "source": path.name,
                    }
                )
                accepted += 1
            notes.append(f"Read {accepted} rows from {path.name}.")
    return rows, notes


def aggregate(rows: list[dict]) -> list[dict]:
    groups: dict[tuple[str, str, str], dict] = defaultdict(
        lambda: {"clicks": 0.0, "impressions": 0.0, "weighted_position": 0.0, "sources": set()}
    )
    for row in rows:
        key = (row["market"], row["query"], row["page"])
        group = groups[key]
        group["clicks"] += row["clicks"]
        group["impressions"] += row["impressions"]
        group["weighted_position"] += row["position"] * row["impressions"]
        group["sources"].add(row["source"])

    priorities: list[dict] = []
    for (market, query, page), group in groups.items():
        impressions = group["impressions"]
        clicks = group["clicks"]
        ctr = clicks / impressions if impressions else 0.0
        position = group["weighted_position"] / impressions if impressions else 0.0
        # This is a prioritization heuristic, not a traffic forecast.
        opportunity_score = math.log1p(impressions) * position_weight(position) * (1.0 - min(ctr, 0.25))
        priorities.append(
            {
                "market": market,
                "query": query or "(page aggregate)",
                "page": page or "(not supplied)",
                "clicks": round(clicks, 2),
                "impressions": round(impressions, 2),
                "ctr": round(ctr, 6),
                "position": round(position, 2),
                "opportunityScore": round(opportunity_score, 4),
                "recommendedAction": action_for(position, ctr, page),
                "sources": sorted(group["sources"]),
            }
        )
    return sorted(priorities, key=lambda item: (-item["opportunityScore"], -item["impressions"]))


def render_markdown(result: dict) -> str:
    lines = [
        "# Search Console Priority Report",
        "",
        f"Generated: {result['generatedAt']}",
        "",
        "The opportunity score is a transparent prioritization heuristic based on observed impressions, CTR, and average position. It is not a traffic or ranking forecast.",
        "",
        "## Data notes",
        "",
    ]
    lines.extend(f"- {note}" for note in result["notes"])
    lines.extend(["", "## US and Hong Kong priorities", ""])
    targeted = [item for item in result["priorities"] if item["market"] in {"US", "HK"}]
    if not targeted:
        lines.append("No rows could be assigned to the US or Hong Kong. Export the Country dimension or include `us`, `usa`, `hk`, or `hong-kong` in filenames.")
    else:
        lines.append("| # | Market | Query | Page | Clicks | Impressions | CTR | Position | Score | Recommended action |")
        lines.append("|---:|:---:|---|---|---:|---:|---:|---:|---:|---|")
        for index, item in enumerate(targeted[:50], start=1):
            query = item["query"].replace("|", "\\|")
            page = item["page"].replace("|", "\\|")
            action = item["recommendedAction"].replace("|", "\\|")
            lines.append(
                f"| {index} | {item['market']} | {query} | {page} | {item['clicks']:g} | "
                f"{item['impressions']:g} | {item['ctr']:.2%} | {item['position']:.2f} | "
                f"{item['opportunityScore']:.4f} | {action} |"
            )

    unassigned = sum(1 for item in result["priorities"] if item["market"] == "UNASSIGNED")
    lines.extend(["", "## Validation", "", f"- Target-market rows: {len(targeted)}", f"- Unassigned rows: {unassigned}"])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="*", type=Path, help="Search Console CSV files. Defaults to data/search-console/*.csv")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = args.inputs or sorted(DEFAULT_INPUT_DIR.glob("*.csv"))
    paths = [path.resolve() for path in paths if path.exists() and path.suffix.lower() == ".csv"]
    if not paths:
        print(f"No Search Console CSV files found in {DEFAULT_INPUT_DIR}.")
        print("Add an export with clicks, impressions, CTR, position, and a query or page column.")
        return 0

    rows, notes = read_rows(paths)
    priorities = aggregate(rows)
    result = {
        "generatedAt": date.today().isoformat(),
        "sourceFiles": [path.name for path in paths],
        "notes": notes,
        "method": "log1p(impressions) * position-band weight * (1 - min(CTR, 25%))",
        "priorities": priorities,
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.report_output.write_text(render_markdown(result), encoding="utf-8")
    print(f"Analyzed {len(rows)} rows into {len(priorities)} priorities.")
    print(f"Wrote {args.json_output} and {args.report_output}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
