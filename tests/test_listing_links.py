import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
LISTINGS_JSON = REPO_ROOT / "zhangjiang_listings_15km.json"


class ListingLinkTests(unittest.TestCase):
    def test_fang_listings_use_beike_search_urls(self):
        data = json.loads(LISTINGS_JSON.read_text(encoding="utf-8-sig"))

        bad_urls = [
            item["url"]
            for item in data["listings"]
            if item.get("platform") == "\u623f\u5929\u4e0b"
            and "sh.zu.ke.com/zufang/rs" not in item["url"]
        ]

        self.assertEqual(bad_urls, [])


if __name__ == "__main__":
    unittest.main()
