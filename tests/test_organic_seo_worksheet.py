import codecs
import csv
import io
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_public_site import build_public_site

ASSET = "assets/resources/organic-seo-audit-worksheet-v1.csv"
IDS = ["access", "indexability", "canonical", "intent", "content", "snippet", "links", "experience"]


class DownloadParser(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.downloads = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and "data-seo-worksheet-download" in attrs:
            self.downloads.append(attrs)


class OrganicSeoWorksheetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (ROOT / ASSET).read_bytes()
        cls.reader = csv.DictReader(io.StringIO(cls.raw.decode("utf-8-sig"), newline=""))
        cls.rows = list(cls.reader)

    def test_csv_shape_bom_and_eight_existing_checks(self):
        self.assertTrue(self.raw.startswith(codecs.BOM_UTF8))
        self.assertEqual(self.raw.count(b"\r\n"), 9)
        self.assertIn(ASSET + " -text", (ROOT / ".gitattributes").read_text(encoding="utf-8"))
        self.assertEqual(len(self.reader.fieldnames), 15)
        self.assertEqual(len(set(self.reader.fieldnames)), 15)
        self.assertEqual([row["检查项代码"] for row in self.rows], IDS)
        self.assertTrue(all(None not in row and None not in row.values() for row in self.rows))
        article = (ROOT / "articles/google-seo-ranking-guide.html").read_text(encoding="utf-8")
        for code in IDS:
            self.assertIn(f'data-seo-diagnosis="{code}"', article)

    def test_inputs_unfilled_unknown_not_zero_and_no_formula_payloads(self):
        for row in self.rows:
            self.assertEqual(row["判断状态"], "未检查")
            self.assertEqual(row["复盘结果"], "未知")
            for key in ["目标网址", "检查时间与时区", "证据记录", "负责人", "版本与上线时间", "复盘口径与日期", "下次触发条件"]:
                self.assertEqual(row[key], "")
            for value in row.values():
                self.assertFalse(value.lstrip().startswith(("=", "+", "-", "@")))

    def test_primary_sources_and_important_boundaries(self):
        for row in self.rows:
            source = urlparse(row["官方说明"])
            self.assertEqual(source.scheme, "https")
            self.assertEqual(source.hostname, "developers.google.com")
            self.assertTrue(source.path.startswith("/search/docs/"))
            self.assertTrue(row["条件式动作"])
        text = self.raw.decode("utf-8-sig")
        for phrase in ["CDN 可能改写", "不等于收录", "canonical 不是强制指令", "查询语言不等于国家", "缺失查询行不等于零需求", "下载和按钮点击不等于询盘"]:
            self.assertIn(phrase, text)

    def test_native_download_reuses_existing_article_and_public_artifact(self):
        source = (ROOT / "articles/google-seo-ranking-guide.html").read_text(encoding="utf-8")
        links = DownloadParser(source).downloads
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["href"], "../" + ASSET)
        self.assertEqual(links[0]["download"], Path(ASSET).name)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "public"
            copied = build_public_site(ROOT, output)
            self.assertIn(ASSET, copied)
            self.assertEqual((output / ASSET).read_bytes(), self.raw)
            self.assertFalse((output / "reports").exists())


if __name__ == "__main__":
    unittest.main()
