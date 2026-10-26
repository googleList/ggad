import json
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).parents[1]


class RankExampleParser(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.examples = {}
        self.current = None
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        key = dict(attrs).get("data-rank-math")
        if key:
            self.current = (tag, key, [])

    def handle_data(self, data):
        if self.current:
            self.current[2].append(data)

    def handle_endtag(self, tag):
        if self.current and tag == self.current[0]:
            self.examples[self.current[1]] = "".join(self.current[2])
            self.current = None


class AdRankGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "articles/google-search-ads-guide.html").read_text(encoding="utf-8")

    def test_teaching_denominators_and_arithmetic(self):
        examples = RankExampleParser(self.source).examples
        self.assertEqual(set(examples), {"top-rate", "absolute-rate", "top-share"})
        for key, numerator, denominator, percent in [
            ("top-rate", 40, 100, 40), ("absolute-rate", 10, 100, 10), ("top-share", 40, 200, 20)
        ]:
            with self.subTest(key=key):
                self.assertEqual(numerator / denominator * 100, percent)
                self.assertIn(f"{numerator} ÷ {denominator} = {percent}%", examples[key])

    def test_example_and_metric_boundaries_are_present(self):
        for phrase in ["只有单次展示、口径一致", "教学假设", "分母为零时比例无定义",
                       "缺失或未提供的份额应保留未知", "不是竞价输入", "该旧指标已停止提供",
                       "某些查询也可能位于其下方", "不等于真实收到询盘"]:
            self.assertIn(phrase, self.source)
        for key in ["eligibility", "budget", "rank", "lead-quality"]:
            self.assertEqual(self.source.count(f'data-rank-decision="{key}"'), 1)

    def test_existing_article_identity_and_actual_revision(self):
        start = self.source.index('<script type="application/ld+json">')
        body = self.source[start:].split(">", 1)[1].split("</script>", 1)[0]
        article = json.loads(body)
        self.assertEqual(article["datePublished"], "2026-09-11")
        self.assertEqual(article["dateModified"], "2026-10-26T16:27:18+08:00")
        self.assertIn(f'datetime="{article["dateModified"]}"', self.source)
        self.assertEqual(article["mainEntityOfPage"], "https://shumaojs.com/articles/google-search-ads-guide.html")
        self.assertEqual(article["headline"], "谷歌广告排名怎么提升？Ad Rank影响因素与优化方法")


if __name__ == "__main__":
    unittest.main()
