#!/usr/bin/env python3
"""Append new rental listings (CSV/JSON) into the preview JSON used by the map page.

Usage:
  python append_listings.py new_batch.csv --json zhangjiang_listings_15km.json
  python append_listings.py new_batch.json --json zhangjiang_listings_15km.json --work-lon 121.606222 --work-lat 31.180732

Behaviour:
  - Reads the existing preview JSON (listings + amenities + buildYears).
  - Reads new rows from the input CSV/JSON (same schema as normalize_listings.py output).
  - Deduplicates by url (case-insensitive). Existing listings are NOT overwritten —
    their hand-annotated fields (amenity_verified, nearest_metro, buildYears, etc.) are
    preserved. Only missing base fields are filled from the new row.
  - For genuinely new listings: inserts with rich fields defaulted to "待核验"/false,
    computes `work` km from work coordinates if provided, and assigns the next rank.
  - Re-sorts by score desc and renumbers rank.
  - Writes the merged JSON back in place.

Input field aliases: the script reuses normalize_listings.py's alias map when the
input is CSV with English/Chinese headers. Longitude/latitude columns are required.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

# Field aliases (subset relevant to the map) — keep in sync with normalize_listings.py.
ALIASES = {
    "score": ["score", "分数"],
    "action": ["action", "contact/watch/skip"],
    "platform": ["platform", "来源", "平台"],
    "source_id": ["source_id", "listing_id", "id", "编号"],
    "title": ["title", "标题", "名称"],
    "rent": ["rent", "price", "租金", "价格"],
    "layout": ["layout", "户型", "房型"],
    "area_m2": ["area_m2", "area", "面积", "建面"],
    "district": ["district", "区", "城区"],
    "business_area": ["business_area", "商圈", "板块"],
    "community": ["community", "小区", "楼盘"],
    "address": ["address", "地址", "位置"],
    "subway": ["subway", "地铁", "metro"],
    "commute": ["commute", "通勤"],
    "longitude": ["longitude", "lng", "lon", "经度"],
    "latitude": ["latitude", "lat", "纬度"],
    "floor": ["floor", "楼层"],
    "orientation": ["orientation", "朝向"],
    "tags": ["tags", "标签"],
    "risks": ["risks", "风险"],
    "url": ["url", "link", "链接"],
}

# Rich fields that come from manual annotation, not from normalize_listings.py.
# For NEW listings we default these; for EXISTING listings we never touch them.
RICH_FIELDS = {
    "work": "",
    "amenity_verified": False,
    "amenity_status": "配套待核验",
    "nearest_metro": "地铁待核验",
    "nearest_mall": "商场待核验",
    "nearest_market": "",
    "residential_priority": "normal",
}

# Base fields that get filled into a new listing entry (in this order).
BASE_FIELDS = [
    "rank", "score", "action", "platform", "source_id", "title",
    "rent", "layout", "area_m2", "district", "business_area",
    "community", "address", "subway", "commute",
    "longitude", "latitude", "tags", "risks", "url",
]


def read_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            for key in ("listings", "items", "data", "rows"):
                if isinstance(data.get(key), list):
                    data = data[key]
                    break
        if not isinstance(data, list):
            raise ValueError("JSON input must be a list or contain listings/items/data/rows")
        return [dict(item) for item in data]
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def first_value(row: dict[str, Any], aliases: list[str]) -> str:
    norm = {str(k).strip().lower(): k for k in row.keys()}
    for alias in aliases:
        k = norm.get(alias.lower())
        if k is not None and str(row.get(k, "")).strip() != "":
            return str(row[k]).strip()
    return ""


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def to_float(v: str) -> float | None:
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def haversine_km(lng1: float, lat1: float, lng2: float, lat2: float) -> float:
    r = 6371.0
    p = math.pi / 180.0
    dlat = (lat2 - lat1) * p
    dlng = (lng2 - lng1) * p
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin(dlng / 2) ** 2
    return round(2 * r * math.asin(math.sqrt(a)), 2)


def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for field, aliases in ALIASES.items():
        out[field] = clean(first_value(row, aliases))
    # type coercion for numerics
    rent = to_float(out.get("rent"))
    if rent is not None:
        out["rent"] = int(rent)
    area = to_float(out.get("area_m2"))
    if area is not None:
        out["area_m2"] = str(area)
    lng = to_float(out.get("longitude"))
    lat = to_float(out.get("latitude"))
    if lng is not None:
        out["longitude"] = lng
    if lat is not None:
        out["latitude"] = lat
    score = to_float(out.get("score"))
    if score is not None:
        out["score"] = int(score)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path, help="CSV or JSON file with new listings")
    parser.add_argument("--json", type=Path, default=Path("zhangjiang_listings_15km.json"),
                        help="Existing preview JSON to merge into (default: zhangjiang_listings_15km.json)")
    parser.add_argument("--work-lon", type=float, default=121.606222, help="Workplace longitude (default: 张江昆仑芯)")
    parser.add_argument("--work-lat", type=float, default=31.180732, help="Workplace latitude (default: 张江昆仑芯)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would change, don't write")
    args = parser.parse_args()

    # Load existing JSON
    if args.json.exists():
        data = json.loads(args.json.read_text(encoding="utf-8"))
        data.setdefault("listings", [])
        data.setdefault("amenities", [])
        data.setdefault("buildYears", {})
    else:
        data = {"listings": [], "amenities": [], "buildYears": {}}

    existing_by_url: dict[str, dict[str, Any]] = {}
    for item in data["listings"]:
        u = str(item.get("url", "")).strip().lower()
        if u:
            existing_by_url["url:" + u] = item
        else:
            comm = str(item.get("community", "")).strip().lower()
            fp = f"fp:{comm}|{item.get('rent','')}|{item.get('area_m2','')}"
            existing_by_url[fp] = item

    new_rows = read_rows(args.input)
    added = 0
    updated = 0
    skipped = 0

    for raw in new_rows:
        row = normalize_row(raw)
        url = str(row.get("url", "")).strip()
        lng = row.get("longitude")
        lat = row.get("latitude")
        if not isinstance(lng, (int, float)) or not isinstance(lat, (int, float)):
            print(f"  SKIP (no coords): {url or row.get('community','')}", file=sys.stderr)
            skipped += 1
            continue

        # Dedupe key: URL if present, else community+rent+area (case-insensitive)
        if url:
            dedupe = "url:" + url.lower()
        else:
            comm = str(row.get("community", "")).strip().lower()
            dedupe = f"fp:{comm}|{row.get('rent','')}|{row.get('area_m2','')}"

        if dedupe in existing_by_url:
            # Existing listing: only fill base fields that are empty.
            ex = existing_by_url[dedupe]
            changed = False
            for field in BASE_FIELDS:
                if field in ("rank",):
                    continue
                cur = ex.get(field)
                new_val = row.get(field)
                if (cur in (None, "", 0) or cur == "0") and new_val not in (None, ""):
                    ex[field] = new_val
                    changed = True
            if changed:
                updated += 1
                print(f"  UPDATE: {url or row.get('community','')}")
            continue

        # Genuinely new listing
        work_km = haversine_km(float(lng), float(lat), args.work_lon, args.work_lat)
        entry: dict[str, Any] = {}
        for field in BASE_FIELDS:
            entry[field] = row.get(field, "")
        # Ensure numerics
        entry["longitude"] = lng
        entry["latitude"] = lat
        if isinstance(row.get("rent"), int):
            entry["rent"] = row["rent"]
        if not entry.get("score"):
            entry["score"] = 0
        if not entry.get("action"):
            entry["action"] = "watch"
        entry["work"] = f"{work_km:.2f}km"
        if not entry.get("commute"):
            entry["commute"] = f"距工作地约{work_km:.2f}km"
        for rf, rv in RICH_FIELDS.items():
            entry[rf] = rv
        data["listings"].append(entry)
        existing_by_url[dedupe] = entry
        added += 1
        print(f"  ADD #{entry.get('score')} {entry.get('title','')[:40]} ({url})")

    # Re-sort by score desc, renumber rank
    data["listings"].sort(key=lambda x: int(x.get("score") or 0), reverse=True)
    for i, item in enumerate(data["listings"], start=1):
        item["rank"] = i

    print(f"\nSummary: +{added} added, ~{updated} updated, {skipped} skipped (no url/coords).")
    print(f"Total listings now: {len(data['listings'])}")

    if args.dry_run:
        print("(dry-run — JSON not written)")
        return

    args.json.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.json} ({args.json.stat().st_size} bytes)")
    print(f"Refresh http://127.0.0.1:8766/zhangjiang_shortlist_15km_preview.html to see them.")


if __name__ == "__main__":
    main()
