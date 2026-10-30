import copy
import csv
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

from scripts.compare_search_console_exports import build_report, comparison_table, metric, read_archive, render_markdown

ROOT = Path(__file__).parents[1]
SNAPSHOT = ROOT / "reports/search-console/2026-10-29-official-comparison.json"
AS_OF = date(2026, 10, 30)


def headers(dimension="热门查询", days=7):
    return [dimension] + [f"{period} {days} 天 {name}" for name in ("点击次数", "展示", "点击率", "排名") for period in ("过去", "先前")]


def rows(value="谷歌代投"):
    return [headers(), [value, "1", "0", "13", "0", "7.69%", "0%", "3.54", "0"]]


class ExportComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = build_report(SNAPSHOT, AS_OF)

    def temporary_snapshot(self, change):
        source = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        change(source)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "snapshot.json"
        path.write_text(json.dumps(source), encoding="utf-8")
        return path

    def test_actual_archives_counts_and_ui_precision_remain_separate(self):
        weekly = self.report["windows"]["weekly"]
        monthly = self.report["windows"]["monthly"]
        self.assertEqual([weekly["propertyUi"][p]["impressions"] for p in ("current", "previous")], [48, 32])
        self.assertEqual([monthly["propertyUi"][p]["impressions"] for p in ("current", "previous")], [264, 3])
        self.assertEqual(weekly["propertyUi"]["current"]["reportedCtrPercent"], 2.1)
        self.assertAlmostEqual(weekly["propertyUi"]["current"]["ctrFromCountsPercent"], 100 / 48)
        target = weekly["exactSeeds"][0]["metrics"]["current"]
        self.assertEqual(target["reportedCtrPercent"], 7.69)
        self.assertEqual(target["averagePosition"], 3.54)
        self.assertAlmostEqual(target["ctrFromCountsPercent"], 100 / 13)
        self.assertFalse(self.report["performsAccountRead"])
        self.assertFalse(self.report["windowsCombined"])

    def test_zero_impression_export_placeholders_are_not_rank_zero(self):
        seed = self.report["windows"]["weekly"]["exactSeeds"][0]
        self.assertTrue(seed["rowPresent"])
        self.assertEqual(seed["metrics"]["previous"]["impressions"], 0)
        self.assertEqual(seed["metrics"]["previous"]["reportedAveragePosition"], 0)
        self.assertIsNone(seed["metrics"]["previous"]["averagePosition"])
        self.assertIsNone(seed["metrics"]["previous"]["ctrFromCountsPercent"])
        self.assertIsNone(seed["metrics"]["changeCurrentMinusPrevious"]["averagePosition"])

    def test_missing_seed_rows_do_not_become_zero_demand(self):
        for window in self.report["windows"].values():
            for seed in window["exactSeeds"][1:]:
                self.assertFalse(seed["rowPresent"])
                self.assertIsNone(seed["metrics"])
                self.assertIsNone(seed["marketSearchVolume"])
            self.assertIsNone(window["exactSeeds"][0]["jointPageCountryDevice"])
        self.assertFalse(self.report["tablesJoined"])

    def test_country_is_all_query_scope_not_language_inference(self):
        countries = self.report["windows"]["weekly"]["targetMarketsAllQueries"]
        self.assertEqual(countries["US"]["current"]["impressions"], 10)
        self.assertEqual(countries["HK"]["current"]["impressions"], 19)
        self.assertEqual(countries["US"]["previous"]["impressions"], 15)
        self.assertIsNone(self.report["windows"]["weekly"]["exactSeeds"][0]["jointPageCountryDevice"])

    def test_reported_row_totals_do_not_replace_property_counts(self):
        monthly = self.report["windows"]["monthly"]
        self.assertEqual(monthly["tables"]["query"]["reportedRowTotalsNotPropertyTotals"]["previous"]["clicks"], 0)
        self.assertEqual(monthly["propertyUi"]["previous"]["clicks"], 1)
        self.assertEqual(monthly["propertyUi"]["previous"]["impressions"], 3)
        self.assertEqual(monthly["otherTables"][0]["status"], "outside_comparison_scope_not_zero")

    def test_dates_and_csv_relative_labels_must_agree(self):
        for change in [lambda s: s["weekly"]["dates"].__setitem__(2, "2026-10-15"),
                       lambda s: s["weekly"].__setitem__("dates", ["2026-10-20", "2026-10-26", "2026-10-14", "2026-10-20"]),
                       lambda s: s["weekly"].__setitem__("dates", [])]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                build_report(self.temporary_snapshot(change), AS_OF)
        with self.assertRaises(ValueError):
            comparison_table(rows(), 28)
        with self.assertRaises(ValueError):
            build_report(SNAPSHOT, date(2026, 10, 26))

    def test_hash_property_and_recorded_csv_mismatch_stop_processing(self):
        for change in [lambda s: s.__setitem__("property", "sc-domain:other.example"),
                       lambda s: s["weekly"].__setitem__("sha256", "0" * 64),
                       lambda s: s["weekly"]["files"].clear(),
                       lambda s: s["weekly"].__setitem__("archive", "../outside.zip")]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                build_report(self.temporary_snapshot(change), AS_OF)

    def test_invalid_counts_percent_units_and_positions_are_rejected(self):
        cases = [("", "13", "0%", "3"), ("1", "NaN", "0%", "3"),
                 ("0.5", "13", "0%", "3"), ("2", "1", "100%", "3"),
                 ("1", "13", "7.69", "3"), ("1", "13", "99%", "3"),
                 ("1", "13", "7.69%", "0"), ("0", "0", "2%", "0"),
                 (True, "13", "0%", "3"), ("0", "-1", "0%", "3")]
        for values in cases:
            with self.subTest(values=values), self.assertRaises(ValueError):
                metric(*values)
        self.assertEqual(metric("1,000", "2,000", "50%", "3.5")["clicks"], 1000)

    def test_duplicate_dimensions_and_row_width_are_rejected(self):
        duplicated = rows() + [rows()[1]]
        with self.assertRaises(ValueError):
            comparison_table(duplicated, 7)
        malformed = rows()
        malformed[1].append("extra")
        with self.assertRaises(ValueError):
            comparison_table(malformed, 7)
        mixed = rows()
        mixed[0].append("国家/地区")
        mixed[1].append("美国")
        with self.assertRaises(ValueError):
            comparison_table(mixed, 7)

    def test_zip_members_are_never_extracted_and_unsafe_archives_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            for names in [["../query.csv"], ["folder/query.csv"], ["C:query.csv"], ["q.csv", "Q.csv"], ["data.html"]]:
                path = Path(directory) / "input.zip"
                with warnings.catch_warnings(), zipfile.ZipFile(path, "w") as archive:
                    warnings.simplefilter("ignore", UserWarning)
                    for name in names:
                        archive.writestr(name, "header\n")
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                with self.subTest(names=names), self.assertRaises(ValueError):
                    read_archive(path, digest, 7)
                self.assertEqual(list(Path(directory).iterdir()), [path])
            with patch("scripts.compare_search_console_exports.MAX_BYTES", 1), self.assertRaises(ValueError):
                read_archive(path, digest, 7)

    def archive_fixture(self, transform):
        tables = json.loads(SNAPSHOT.read_text(encoding="utf-8"))["weekly"]["files"]
        transform(tables)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "input.zip"
        with zipfile.ZipFile(path, "w") as archive:
            for name, table in tables.items():
                text = io.StringIO(newline="")
                csv.writer(text).writerows(table)
                archive.writestr(name, text.getvalue().encode("utf-8"))
        return path, hashlib.sha256(path.read_bytes()).hexdigest()

    def test_filtered_or_missing_dimension_exports_are_not_joined_or_guessed(self):
        for transform in [lambda t: t["过滤器.csv"].append(["查询", "谷歌代投"]),
                          lambda t: t.pop("设备.csv"),
                          lambda t: t.__setitem__("queries-again.csv", t["查询数.csv"]),
                          lambda t: t["过滤器.csv"].__setitem__(2, ["日期", "过去 28 天"])]:
            path, digest = self.archive_fixture(transform)
            with self.subTest(transform=transform), self.assertRaises(ValueError):
                read_archive(path, digest, 7)

    def test_each_member_has_a_limit_independent_of_total_archive_size(self):
        path, digest = self.archive_fixture(lambda t: None)
        with patch("scripts.compare_search_console_exports.MAX_MEMBER_BYTES", 100), self.assertRaises(ValueError):
            read_archive(path, digest, 7)

    def test_query_raw_whitespace_is_not_relabelled_as_an_exact_seed(self):
        path, digest = self.archive_fixture(lambda t: t["查询数.csv"][1].__setitem__(0, "谷歌代投 "))
        table = read_archive(path, digest, 7)["tables"]["query"]["rows"]
        self.assertEqual(table[0]["value"], "谷歌代投 ")
        self.assertFalse(any(row["value"] == "谷歌代投" for row in table))

    def test_freshness_and_repeat_fingerprint_do_not_create_new_data(self):
        repeated = build_report(SNAPSHOT, AS_OF, baseline=self.report)
        self.assertFalse(repeated["inputEvidenceChangedSinceBaseline"])
        self.assertEqual(repeated["editorialGate"]["action"], "no_new_input_evidence")
        later = build_report(SNAPSHOT, date(2026, 11, 2), baseline=self.report)
        self.assertEqual(later["windows"]["weekly"]["freshness"]["dataThrough"], "2026-10-27")
        self.assertEqual(later["windows"]["weekly"]["freshness"]["status"], "older_than_lag_policy")
        self.assertEqual(later["editorialGate"]["action"], "verify_newer_window_first")
        self.assertFalse(later["windows"]["weekly"]["freshness"]["isApiFinalnessProof"])
        edge = build_report(SNAPSHOT, date(2026, 10, 28))
        self.assertEqual(edge["windows"]["weekly"]["freshness"]["status"], "recent_edge_not_assumed_final")

    def test_baseline_scope_and_editorial_guard_are_not_publication_permission(self):
        invalid = copy.deepcopy(self.report)
        invalid["property"] = "sc-domain:other.example"
        with self.assertRaises(ValueError):
            build_report(SNAPSHOT, AS_OF, baseline=invalid)
        different = copy.deepcopy(self.report)
        different["inputEvidenceFingerprint"] = "0" * 64
        self.assertTrue(build_report(SNAPSHOT, AS_OF, baseline=different)["inputEvidenceChangedSinceBaseline"])
        gate = self.report["editorialGate"]
        self.assertEqual(gate["candidateSeedsForInvestigationNotAutomaticEdits"], [])
        self.assertFalse(gate["automaticContentEditsAuthorized"])
        self.assertFalse(gate["isStatisticalSignificanceThreshold"])

    def test_multiline_and_markup_labels_are_preserved_but_safe_in_markdown(self):
        raw = "<script>sample</script>\nquery | value"
        parsed = comparison_table(rows(raw), 7)[1]["rows"][0]
        self.assertEqual(parsed["value"], raw)
        report = copy.deepcopy(self.report)
        report["windows"]["weekly"]["tables"]["query"]["rows"] = [parsed]
        rendered = render_markdown(report)
        self.assertIn("&lt;script&gt;sample&lt;/script&gt; query \\| value", rendered)
        self.assertNotIn("<script>", rendered)
        actual_rows = self.report["windows"]["monthly"]["tables"]["query"]["rows"]
        self.assertTrue(any("\n" in row["value"] for row in actual_rows))

    def test_cli_failure_does_not_overwrite_previous_outputs(self):
        invalid = self.temporary_snapshot(lambda s: s["weekly"].__setitem__("sha256", "0" * 64))
        json_path, markdown_path = invalid.parent / "old.json", invalid.parent / "old.md"
        json_path.write_text("previous", encoding="utf-8")
        markdown_path.write_text("previous", encoding="utf-8")
        result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/compare_search_console_exports.py"),
                                 "--snapshot", str(invalid), "--as-of-date", "2026-10-30", "--json-output", str(json_path), "--report-output", str(markdown_path)], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json_path.read_text(encoding="utf-8"), "previous")
        self.assertEqual(markdown_path.read_text(encoding="utf-8"), "previous")


if __name__ == "__main__":
    unittest.main()
