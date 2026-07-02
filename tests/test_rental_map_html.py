import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MAP_HTML = REPO_ROOT / "zhangjiang_shortlist_15km_preview.html"
LISTINGS_JSON = REPO_ROOT / "zhangjiang_listings_15km.json"


def load_listings():
    html = MAP_HTML.read_text(encoding="utf-8")
    match = re.search(r"const listings = (\[.*?\]);\s*const buildYears", html, re.S)
    if match:
        return html, json.loads(match.group(1))
    data = json.loads(LISTINGS_JSON.read_text(encoding="utf-8-sig"))
    return html, data["listings"]


class RentalMapHtmlTests(unittest.TestCase):
    def test_main_map_embeds_only_requirement_matching_listings(self):
        html, listings = load_listings()
        allowed_layouts = {"1\u5ba41\u5385", "2\u5ba41\u5385", "2\u5ba42\u5385"}

        self.assertEqual(len(listings), 107)
        self.assertNotIn("supplemental_area_candidates.html", html)
        self.assertNotIn("zhangjiang_requirement_matches_15km.html", html)
        self.assertNotIn("???", html[:2000])
        self.assertIn("\u5f20\u6c5f\u6606\u4ed1\u82af\u79df\u623f\u5730\u56fe 15km \u7cbe\u7b5b", html)
        self.assertIn("3km", html)

        for listing in listings:
            self.assertIn(listing["layout"], allowed_layouts)
            self.assertGreaterEqual(int(listing["rent"]), 2000)
            self.assertLessEqual(int(listing["rent"]), 4000)
            self.assertLessEqual(float(str(listing["work"]).replace("km", "")), 15.0)

    def test_separate_candidate_pages_are_removed(self):
        self.assertFalse((REPO_ROOT / "supplemental_area_candidates.html").exists())
        self.assertFalse((REPO_ROOT / "supplemental_area_candidates.csv").exists())
        self.assertFalse((REPO_ROOT / "supplemental_area_coverage.md").exists())
        self.assertFalse((REPO_ROOT / "zhangjiang_requirement_matches_15km.html").exists())
        self.assertFalse((REPO_ROOT / "zhangjiang_requirement_matches_15km.csv").exists())
