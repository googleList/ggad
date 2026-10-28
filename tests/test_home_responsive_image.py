import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from scripts.performance_budget_check import ImageParser


ROOT = Path(__file__).parents[1]
PHOTO = "photo-1460925895917-afdab827c52f"


class HomeResponsiveImageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        parser = ImageParser()
        parser.feed((ROOT / "index.html").read_text(encoding="utf-8"))
        cls.image = next(image for image in parser.images if PHOTO in image.get("src", ""))

    def test_sizes_match_narrow_phone_tablet_and_bounded_desktop(self):
        self.assertEqual(self.image["sizes"], "(max-width: 378px) calc(100vw - 38px), (max-width: 700px) 338px, (max-width: 980px) calc(100vw - 38px), (max-width: 1236px) calc(46.3vw - 20px), 554px")
        self.assertNotIn("50vw", self.image["sizes"])

    def test_retina_tablets_have_real_matching_width_candidates(self):
        candidates = []
        for source in self.image["srcset"].split(","):
            url, descriptor = source.strip().rsplit(None, 1)
            width = int(descriptor.removesuffix("w"))
            self.assertEqual(parse_qs(urlparse(url).query)["w"], [str(width)])
            self.assertIn(PHOTO, url)
            candidates.append(width)
        self.assertEqual(candidates, [480, 640, 800, 1200, 1600, 2000])

    def test_photo_identity_and_noncritical_loading_are_preserved(self):
        self.assertEqual(self.image["src"], "https://images.unsplash.com/" + PHOTO + "?auto=format&fit=crop&w=1200&q=82")
        self.assertEqual(self.image["alt"], "广告数据分析与合规检查工作台")
        self.assertEqual((self.image["width"], self.image["height"]), ("1200", "800"))
        self.assertEqual(self.image["loading"], "lazy")
        self.assertEqual(self.image["decoding"], "async")


if __name__ == "__main__":
    unittest.main()
