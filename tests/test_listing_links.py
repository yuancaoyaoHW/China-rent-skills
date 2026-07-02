import json
import shutil
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
LISTINGS_JSON = REPO_ROOT / "zhangjiang_listings_15km.json"
PREVIEW_HTML = REPO_ROOT / "zhangjiang_shortlist_15km_preview.html"


class ListingLinkTests(unittest.TestCase):
    def test_fang_listings_use_beike_urls(self):
        data = json.loads(LISTINGS_JSON.read_text(encoding="utf-8-sig"))

        bad_urls = [
            item["url"]
            for item in data["listings"]
            if item.get("platform") == "\u623f\u5929\u4e0b"
            and item.get("url")
            and not item["url"].startswith("https://sh.zu.ke.com/zufang/")
        ]

        self.assertEqual(bad_urls, [])

    @unittest.skipIf(not shutil.which("node"), "node is required to execute preview JavaScript")
    def test_preview_labels_beike_search_links_as_search(self):
        html = PREVIEW_HTML.read_text(encoding="utf-8-sig")
        esc_js = html[html.index("function esc(value)") : html.index("function buildYearText")]
        source_link_js = html[
            html.index("function isBeikeSearchUrl")
            : html.index("function getUserPref")
        ]
        script = (
            esc_js
            + source_link_js
            + """
const outputs = [
  sourceLinkHtml({ url: "" }),
  sourceLinkHtml({ url: "https://sh.zu.ke.com/zufang/rs%E7%8E%89%E5%85%B0%E9%A6%99%E8%8B%91/" }),
  sourceLinkHtml({ url: "https://sh.zu.ke.com/zufang/SH2179860674669182976.html" })
];
console.log(JSON.stringify(outputs));
"""
        )

        result = subprocess.run(
            ["node", "-e", script],
            check=True,
            capture_output=True,
            encoding="utf-8",
            text=True,
            cwd=REPO_ROOT,
        )
        missing, search, detail = json.loads(result.stdout)

        self.assertIn("\u623f\u6e90\u94fe\u63a5\u5f85\u6838\u9a8c", missing)
        self.assertIn("\u6253\u5f00\u8d1d\u58f3\u641c\u7d22", search)
        self.assertNotIn("\u6253\u5f00\u623f\u6e90", search)
        self.assertIn("\u6253\u5f00\u623f\u6e90", detail)


if __name__ == "__main__":
    unittest.main()
