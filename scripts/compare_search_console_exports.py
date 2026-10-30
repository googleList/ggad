#!/usr/bin/env python3
"""Reproduce separate 7/28-day comparisons from verified Chinese GSC UI exports."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import re
import zipfile
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

try:
    from prioritize_search_console import ALIASES, COUNTRY_MARKETS, MIN_CONTENT_REVIEW_IMPRESSIONS, header_map, markdown_cell, normalize_header
except ModuleNotFoundError:
    from scripts.prioritize_search_console import ALIASES, COUNTRY_MARKETS, MIN_CONTENT_REVIEW_IMPRESSIONS, header_map, markdown_cell, normalize_header

ROOT = Path(__file__).resolve().parents[1]
PROPERTY = "sc-domain:shumaojs.com"
SEEDS = ("谷歌代投", "谷歌开户", "谷歌排名", "谷歌广告")
MAX_BYTES = 10_000_000
MAX_MEMBER_BYTES = 2_000_000
DIMENSIONS = {key: ALIASES[key] for key in ("query", "page", "country")}
DIMENSIONS["device"] = {"device", "devices", "设备", "裝置", "裝置類型"}
SOURCES = [
    "https://support.google.com/webmasters/answer/7576553?hl=en",
    "https://support.google.com/webmasters/answer/17010575",
    "https://support.google.com/webmasters/answer/17011259",
]


def decimal(value, name: str) -> Decimal:
    if isinstance(value, bool) or value is None or not str(value).strip():
        raise ValueError(f"Missing or invalid {name}")
    text = str(value).strip()
    if not re.fullmatch(r"(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?", text):
        raise ValueError(f"Invalid {name}")
    try:
        parsed = Decimal(text.replace(",", ""))
    except InvalidOperation as error:
        raise ValueError(f"Invalid {name}") from error
    if not parsed.is_finite():
        raise ValueError(f"Non-finite {name}")
    return parsed


def metric(clicks, impressions, ctr, position) -> dict:
    counts = [decimal(value, name) for value, name in [(clicks, "clicks"), (impressions, "impressions")]]
    if any(value != value.to_integral_value() for value in counts):
        raise ValueError("Counts must be non-negative integers")
    clicks, impressions = map(int, counts)
    if clicks > impressions:
        raise ValueError("Clicks exceed impressions")
    if not isinstance(ctr, str) or not ctr.strip().endswith("%"):
        raise ValueError("CTR must explicitly use percent units")
    exported_ctr = decimal(ctr.strip()[:-1], "CTR")
    if exported_ctr > 100:
        raise ValueError("CTR exceeds 100 percent")
    ratio = Decimal(clicks) * 100 / impressions if impressions else None
    tolerance = Decimal(1).scaleb(exported_ctr.as_tuple().exponent) / 2
    if ratio is not None and abs(exported_ctr - ratio) > tolerance + Decimal("0.0000000001"):
        raise ValueError("CTR does not match counts within exported rounding")
    if not impressions and exported_ctr:
        raise ValueError("Nonzero CTR without impressions")
    exported_position = decimal(position, "position") if position not in (None, "") else None
    if impressions and (exported_position is None or exported_position < 1):
        raise ValueError("Observed impressions need a valid average position")
    return {
        "clicks": clicks, "impressions": impressions,
        "reportedCtrPercent": float(exported_ctr),
        "ctrFromCountsPercent": float(ratio) if ratio is not None else None,
        "averagePosition": float(exported_position) if impressions else None,
        "reportedAveragePosition": float(exported_position) if exported_position is not None else None,
    }


def changes(current: dict, previous: dict) -> dict:
    result = {}
    for key in ("clicks", "impressions", "ctrFromCountsPercent", "averagePosition"):
        if current[key] is None or previous[key] is None:
            result[key] = None
        elif key in {"clicks", "impressions"}:
            result[key] = current[key] - previous[key]
        else:
            result[key] = float(Decimal(str(current[key])) - Decimal(str(previous[key])))
    return result


def comparison_table(rows: list[list[str]], days: int) -> tuple[str, dict]:
    fields = rows[0]
    dimensions = [(key, field) for field in fields for key, aliases in DIMENSIONS.items() if normalize_header(field) in aliases]
    if len(dimensions) != 1:
        raise ValueError("Expected one independent query/page/country/device dimension")
    dimension, label = dimensions[0]
    lengths = {int(m.group(1)) for field in fields if (m := re.match(r"^(?:过去|先前)\s+(\d+)\s+天\s+", field.strip()))}
    if lengths != {days}:
        raise ValueError("CSV period labels do not match verified absolute dates")
    maps = {period: header_map(fields, period) for period in ("current", "previous")}
    if any(not {"clicks", "impressions", "ctr", "position"} <= mapping.keys() for mapping in maps.values()):
        raise ValueError("Both comparison periods and all four metrics are required")
    if len(set(fields)) != len(fields):
        raise ValueError("Duplicate CSV headers")
    parsed, seen = [], set()
    for row in rows[1:]:
        if len(row) != len(fields):
            raise ValueError("CSV row width does not match headers")
        raw = dict(zip(fields, row))
        value = raw[label]
        if not value.strip() or value in seen:
            raise ValueError("Empty or duplicate dimension value")
        seen.add(value)
        item = {"value": value}
        for period, mapping in maps.items():
            item[period] = metric(*(raw[mapping[key]] for key in ("clicks", "impressions", "ctr", "position")))
        item["changeCurrentMinusPrevious"] = changes(item["current"], item["previous"])
        parsed.append(item)
    totals = {}
    for period in maps:
        clicks = sum(item[period]["clicks"] for item in parsed)
        impressions = sum(item[period]["impressions"] for item in parsed)
        totals[period] = {"clicks": clicks, "impressions": impressions,
                          "ctrFromCountsPercent": clicks / impressions * 100 if impressions else None}
    return dimension, {"rows": parsed, "reportedRowTotalsNotPropertyTotals": totals,
                       "scope": "Independent table; no query/page/country/device join is available."}


def read_archive(path: Path, expected_hash: str, days: int, recorded_tables: dict | None = None) -> dict:
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("Archive exceeds size limit")
    actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual_hash != expected_hash:
        raise ValueError("Archive SHA256 does not match observed source record")
    raw_tables, tables, filters, other = {}, {}, None, []
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        if len(members) > 16 or sum(member.file_size for member in members) > MAX_BYTES:
            raise ValueError("Archive expansion exceeds limits")
        names = set()
        for member in members:
            name = member.filename
            if any(char in name for char in "/\\:") or not name.lower().endswith(".csv") or name.casefold() in names:
                raise ValueError("Only unique flat CSV archive members are supported")
            names.add(name.casefold())
            if member.file_size > MAX_MEMBER_BYTES or member.flag_bits & 1:
                raise ValueError("Oversized or encrypted CSV member")
            rows = list(csv.reader(io.StringIO(archive.read(member).decode("utf-8-sig"), newline="")))
            if not rows or not rows[0]:
                raise ValueError("Empty CSV member")
            raw_tables[name] = rows
            if rows[0] == ["过滤器", "值"]:
                if filters is not None or any(len(row) != 2 for row in rows[1:]):
                    raise ValueError("Ambiguous export filters")
                filters = dict(rows[1:])
                if len(filters) != len(rows) - 1:
                    raise ValueError("Duplicate export filter")
            elif rows[0][0] == "搜索结果呈现":
                other.append({"file": name, "rowCount": len(rows) - 1, "status": "outside_comparison_scope_not_zero"})
            else:
                dimension, table = comparison_table(rows, days)
                if dimension in tables:
                    raise ValueError("Duplicate dimension tables")
                tables[dimension] = {"sourceFile": name, **table}
    if set(tables) != set(DIMENSIONS):
        raise ValueError("Query, page, country and device tables are all required")
    if not filters or set(filters) != {"搜索类型", "日期"} or not filters["搜索类型"].strip():
        raise ValueError("Only unfiltered property comparison exports are supported")
    if not re.fullmatch(rf"过去\s+{days}\s+天", filters["日期"]):
        raise ValueError("Export date filter differs from verified date range")
    if recorded_tables is not None and recorded_tables != raw_tables:
        raise ValueError("Archive CSV rows differ from preserved observation")
    return {"sha256": actual_hash, "filters": filters, "tables": tables, "otherTables": other}


def property_metrics(source: dict) -> dict:
    required = ("clicks", "impressions", "ctrPercent", "averagePosition")
    if any(not isinstance(source.get(key), list) or len(source[key]) != 2 for key in required):
        raise ValueError("Visible property metrics need both periods")
    result = {period: metric(source["clicks"][i], source["impressions"][i],
                             str(source["ctrPercent"][i]) + "%", source["averagePosition"][i])
              for i, period in enumerate(("current", "previous"))}
    result["changeCurrentMinusPrevious"] = changes(result["current"], result["previous"])
    result["source"] = "Previously observed visible UI cards; average position and exported CTR can be rounded. Not table sums."
    return result


def build_report(snapshot_path: Path, as_of: date, archive_root: Path = ROOT,
                 expected_property: str = PROPERTY, baseline: dict | None = None, lag_days: int = 3) -> dict:
    if lag_days < 0:
        raise ValueError("Lag policy cannot be negative")
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if snapshot.get("property") != expected_property:
        raise ValueError("Source property differs from the intended site")
    observed = date.fromisoformat(snapshot["observedDate"])
    windows = {}
    for name, days in (("weekly", 7), ("monthly", 28)):
        source = snapshot[name]
        if not isinstance(source.get("dates"), list) or len(source["dates"]) != 4:
            raise ValueError("Four verified absolute date fields are required")
        start, end, prior_start, prior_end = [date.fromisoformat(value) for value in source["dates"]]
        if (end - start).days + 1 != days or (prior_end - prior_start).days + 1 != days or prior_end + timedelta(days=1) != start:
            raise ValueError("Comparison dates must be adjacent equal-length non-overlapping periods")
        if end > as_of or end > observed:
            raise ValueError("Data extends beyond the stated observation or as-of date")
        root = archive_root.resolve()
        path = (root / source["archive"].replace("\\", "/")).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Archive path escapes the chosen archive root")
        parsed = read_archive(path, source["sha256"], days, source.get("files"))
        expected_end = as_of - timedelta(days=lag_days)
        freshness = "matches_lag_policy" if end == expected_end else "older_than_lag_policy" if end < expected_end else "recent_edge_not_assumed_final"
        queries = {row["value"]: row for row in parsed["tables"]["query"]["rows"]}
        markets = {}
        for row in parsed["tables"]["country"]["rows"]:
            market = COUNTRY_MARKETS.get(normalize_header(row["value"]))
            if market in {"US", "HK"}:
                if market in markets:
                    raise ValueError("Ambiguous target-market country rows")
                markets[market] = row
        windows[name] = {
            "dates": {"current": [start.isoformat(), end.isoformat()], "previous": [prior_start.isoformat(), prior_end.isoformat()]},
            "freshness": {"dataThrough": end.isoformat(), "dataAgeDays": (as_of - end).days,
                          "expectedThroughByPolicy": expected_end.isoformat(), "status": freshness, "isApiFinalnessProof": False},
            "archive": source["archive"].replace("\\", "/"), **parsed,
            "propertyUi": property_metrics(source["propertyMetricsFromVisibleUI"]),
            "exactSeeds": [{"query": seed, "rowPresent": seed in queries, "metrics": queries.get(seed),
                            "jointPageCountryDevice": None, "marketSearchVolume": None} for seed in SEEDS],
            "targetMarketsAllQueries": {market: markets.get(market) for market in ("US", "HK")},
        }
    identity = {name: {key: data[key] for key in ("dates", "sha256", "filters", "propertyUi")} for name, data in windows.items()}
    fingerprint = hashlib.sha256(json.dumps({"property": expected_property, "windows": identity}, sort_keys=True, ensure_ascii=True).encode()).hexdigest()
    changed = None
    if baseline is not None:
        if baseline.get("schemaVersion") != 1 or baseline.get("property") != expected_property or not re.fullmatch(r"[0-9a-f]{64}", baseline.get("inputEvidenceFingerprint", "")):
            raise ValueError("Baseline is not a compatible report for this property")
        changed = baseline["inputEvidenceFingerprint"] != fingerprint
    eligible = [seed["query"] for data in windows.values() for seed in data["exactSeeds"]
                if seed["rowPresent"] and seed["metrics"]["current"]["impressions"] >= MIN_CONTENT_REVIEW_IMPRESSIONS]
    return {
        "schemaVersion": 1, "property": expected_property, "asOfDatePT": as_of.isoformat(),
        "sourceSnapshot": snapshot_path.name, "sourceObservedDateAsRecorded": observed.isoformat(),
        "inputEvidenceFingerprint": fingerprint, "inputEvidenceChangedSinceBaseline": changed,
        "performsAccountRead": False, "windowsCombined": False, "tablesJoined": False, "windows": windows,
        "editorialGate": {
            "minimumRowImpressionsForInvestigation": MIN_CONTENT_REVIEW_IMPRESSIONS,
            "isStatisticalSignificanceThreshold": False,
            "candidateSeedsForInvestigationNotAutomaticEdits": sorted(set(eligible)),
            "action": "verify_newer_window_first" if any(w["freshness"]["status"] != "matches_lag_policy" for w in windows.values()) else "no_new_input_evidence" if changed is False else "investigate_with_joint_scope" if eligible else "observe_only_small_or_missing_seed_rows",
            "automaticContentEditsAuthorized": False,
        },
        "unknownOutcomes": {key: None for key in ("keywordSearchVolume", "seoDifficulty", "organicVisits", "qualifiedEnquiries", "fieldCoreWebVitals", "releaseAttributedGrowth")},
        "limits": [
            "Existing exports are reprocessed, not a new Google account read. A new report timestamp does not advance the data period.",
            "Separate weekly and monthly windows overlap; never add them together or join the independent dimension tables.",
            "Missing rows remain absent/null, not zero demand. Exported zeros can also represent unavailable UI values; zero-impression CTR/position are undefined, not rank zero.",
            "Property/UI totals differ from reported-row sums through aggregation, privacy and truncation; no forced reconciliation or query-country attribution.",
            "As-of date and lag policy use the PT report calendar, not the machine's timezone. Lag matching does not prove complete/final API data.",
            "Clicks are not sessions, customers or enquiries; small samples, mixed queries and a tiny prior baseline do not establish causal growth or a title-test winner.",
        ],
        "methodSources": SOURCES,
    }


def render_markdown(report: dict) -> str:
    def cell(value):
        return markdown_cell(html.escape(str(value)))

    def show(value):
        return "unknown" if value is None else f"{value:.2f}" if isinstance(value, float) else str(value)

    lines = ["# Reproducible Search Console Export Comparison", "", f"Property: `{report['property']}`",
             f"As-of PT calendar: {report['asOfDatePT']}; source observed date: {report['sourceObservedDateAsRecorded']}.",
             "No account read was performed. Reprocessed exports are not new performance observations.", ""]
    for name, window in report["windows"].items():
        lines += [f"## {name.title()}", "", f"Current: {' through '.join(window['dates']['current'])}; previous: {' through '.join(window['dates']['previous'])} (PT).",
                  f"Archive SHA256: `{window['sha256']}`; freshness: {window['freshness']['status']}.", "",
                  "Previously observed UI cards; CTR below is recalculated from matching counts, not averaged across rows. CTR values are percentages; changes are percentage points. Average position is not a fixed keyword rank.",
                  "| Metric | Current | Previous | Current minus previous |", "|---|---:|---:|---:|"]
        for metric_name in ("clicks", "impressions", "ctrFromCountsPercent", "averagePosition"):
            lines.append(f"| {metric_name} | {show(window['propertyUi']['current'][metric_name])} | {show(window['propertyUi']['previous'][metric_name])} | {show(window['propertyUi']['changeCurrentMinusPrevious'][metric_name])} |")
        lines += ["", "Exact seeds, independent query table only. Missing rows are not filled with zeros. Exported zeros can also represent unavailable UI values; 0 / 0 is not proof of zero market demand.",
                  "| Query | Row present | Current clicks / impressions | Previous clicks / impressions | Current / previous position |", "|---|---|---:|---:|---:|"]
        for seed in window["exactSeeds"]:
            metrics = seed["metrics"]
            if metrics:
                current, previous = metrics["current"], metrics["previous"]
                values = [f"{current['clicks']} / {current['impressions']}", f"{previous['clicks']} / {previous['impressions']}", f"{show(current['averagePosition'])} / {show(previous['averagePosition'])}"]
            else:
                values = ["unknown"] * 3
            lines.append(f"| {cell(seed['query'])} | {seed['rowPresent']} | {' | '.join(values)} |")
        lines += ["", "Country rows cover all queries, not these seeds; device and page tables remain separate in JSON.",
                  "| Country | Current clicks / impressions | Previous clicks / impressions |", "|---|---:|---:|"]
        for market, row in window["targetMarketsAllQueries"].items():
            values = [f"{row[p]['clicks']} / {row[p]['impressions']}" for p in ("current", "previous")] if row else ["unknown", "unknown"]
            lines.append(f"| {market} | {' | '.join(values)} |")
        for dimension in ("query", "page"):
            lines += ["", f"Reported {dimension} rows with largest absolute impression changes, not causal wins/losses.",
                      "| Value | Current impressions | Previous impressions | Click change |", "|---|---:|---:|---:|"]
            rows = sorted(window["tables"][dimension]["rows"], key=lambda row: (-abs(row["changeCurrentMinusPrevious"]["impressions"]), row["value"]))[:5]
            for row in rows:
                lines.append(f"| {cell(row['value'])} | {row['current']['impressions']} | {row['previous']['impressions']} | {row['changeCurrentMinusPrevious']['clicks']} |")
        lines.append("")
    lines += ["## Editorial Gate", "", f"Action: `{report['editorialGate']['action']}`. Input evidence changed since supplied baseline: {report['inputEvidenceChangedSinceBaseline']}.",
              "The impression guard is editorial triage, not statistical significance or automatic editing permission.", "", "## Limits", ""]
    lines.extend("- " + value for value in report["limits"])
    lines += ["", "Method sources: " + ", ".join(f"[Google documentation {i}]({url})" for i, url in enumerate(SOURCES, 1)), ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--snapshot", type=Path, required=True)
    cli.add_argument("--as-of-date", type=date.fromisoformat, required=True, help="Explicit PT calendar date, not a new measurement date")
    cli.add_argument("--archive-root", type=Path, default=ROOT)
    cli.add_argument("--property", default=PROPERTY)
    cli.add_argument("--expected-lag-days", type=int, default=3)
    cli.add_argument("--prior-report", type=Path)
    cli.add_argument("--json-output", type=Path, required=True)
    cli.add_argument("--report-output", type=Path, required=True)
    args = cli.parse_args(argv)
    try:
        outputs = [args.json_output.resolve(), args.report_output.resolve()]
        protected = [args.snapshot.resolve()] + ([args.prior_report.resolve()] if args.prior_report else [])
        if len(set(outputs)) != 2 or any(path in protected for path in outputs):
            raise ValueError("Outputs must be distinct and cannot overwrite source or baseline")
        baseline = json.loads(args.prior_report.read_text(encoding="utf-8")) if args.prior_report else None
        result = build_report(args.snapshot, args.as_of_date, args.archive_root, args.property, baseline, args.expected_lag_days)
        archives = [(args.archive_root / window["archive"]).resolve() for window in result["windows"].values()]
        if any(path in archives for path in outputs):
            raise ValueError("Outputs cannot overwrite source archives")
        for path in outputs:
            path.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        args.report_output.write_text(render_markdown(result), encoding="utf-8")
    except (ValueError, KeyError, TypeError, OSError, zipfile.BadZipFile) as error:
        cli.exit(2, f"Comparison rejected: {error}\n")
    print("Validated two separate comparison windows; no account read, cross-table join or automatic content edit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
