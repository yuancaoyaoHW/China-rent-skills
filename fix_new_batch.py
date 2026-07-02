#!/usr/bin/env python3
"""Fix the 19 new fang.com listings: add work field, Beike search URL, and buildYears.

- work: extract from commute string (e.g. "距张江昆仑芯约3.76km" -> "3.76km")
- url: build a Beike community search URL by community name
- buildYears: query AMap POI text search for each community, extract build year
  from the address or name if available; fall back to '待查' with low confidence
"""
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent
JSON_FILE = REPO / 'zhangjiang_listings_15km.json'
KEY_FILE = REPO / 'amap_key.txt'

def read_key():
    if KEY_FILE.exists():
        k = KEY_FILE.read_text(encoding='utf-8').strip()
        if k and not k.startswith('('):
            return k
    import os
    return os.getenv('AMAP_WEB_SERVICE_KEY', '')

def amap_place_text(keywords, city, key, types='', timeout=12):
    """AMap Place API text search. Returns list of POIs."""
    params = {
        'key': key, 'keywords': keywords, 'city': city,
        'citylimit': 'true', 'output': 'JSON', 'offset': 5, 'page': 1,
    }
    if types:
        params['types'] = types
    url = 'https://restapi.amap.com/v3/place/text?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': 'china-rental-research/1.0'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    if data.get('status') != '1':
        return []
    return data.get('pois') or []

def extract_year_from_poi(poi):
    """Try to extract build year from POI address or name."""
    text = str(poi.get('address', '')) + ' ' + str(poi.get('name', ''))
    # Match patterns like "2005年建", "2005年", "2005", "建于2005"
    m = re.search(r'(19[89]\d|20[0-2]\d)\s*年?\s*(?:建|建成|年)', text)
    if m:
        return m.group(1) + '年', 'high'
    m = re.search(r'建于\s*(19[89]\d|20[0-2]\d)', text)
    if m:
        return m.group(1) + '年', 'high'
    # Some POIs have "2005" in the name
    m = re.search(r'(19[89]\d|20[0-2]\d)', text)
    if m:
        year = int(m.group(1))
        if 1980 <= year <= 2025:
            return m.group(1) + '年', 'medium'
    return None, None

def main():
    key = read_key()
    print(f"AMap key: {'found' if key else 'MISSING'}")

    data = json.loads(JSON_FILE.read_text(encoding='utf-8'))
    listings = data['listings']
    build_years = data.get('buildYears', {})

    targets = [x for x in listings if x.get('platform') == '房天下']
    print(f"Fang listings to fix: {len(targets)}")

    fixed_work = 0
    fixed_url = 0
    fixed_year = 0

    for i, item in enumerate(targets):
        comm = item.get('community', '').strip()

        # 1. Fix work field from commute
        commute = str(item.get('commute', ''))
        if not item.get('work') and commute:
            m = re.search(r'约([\d.]+)km', commute)
            if m:
                item['work'] = m.group(1) + 'km'
                fixed_work += 1

        search_url = f"https://sh.zu.ke.com/zufang/rs{urllib.parse.quote(comm)}/"
        if item.get('url') != search_url:
            item['url'] = search_url
            fixed_url += 1

        # 3. Fix buildYears
        if comm not in build_years and key:
            try:
                pois = amap_place_text(comm, '上海', key, types='120000')  # 住宅区
                year, conf = None, None
                for poi in pois[:3]:
                    y, c = extract_year_from_poi(poi)
                    if y:
                        year, conf = y, c
                        break
                if not year:
                    # Try broader search (no type filter)
                    pois2 = amap_place_text(comm, '上海', key)
                    for poi in pois2[:3]:
                        y, c = extract_year_from_poi(poi)
                        if y:
                            year, conf = y, c
                            break
                if year:
                    build_years[comm] = {'year': year, 'confidence': conf}
                    fixed_year += 1
                    print(f"  [{i+1}] {comm}: {year} ({conf})")
                else:
                    build_years[comm] = {'year': '待查', 'confidence': 'low'}
                    print(f"  [{i+1}] {comm}: 待查 (no year in POI)")
                time.sleep(0.3)
            except Exception as e:
                build_years[comm] = {'year': '待查', 'confidence': 'low'}
                print(f"  [{i+1}] {comm}: 待查 (error: {e})")
        elif comm not in build_years:
            build_years[comm] = {'year': '待查', 'confidence': 'low'}

    data['buildYears'] = build_years

    JSON_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"\nFixed: work={fixed_work}, url={fixed_url}, buildYears={fixed_year}")
    print(f"buildYears total: {len(build_years)} communities")
    print(f"Wrote {JSON_FILE}")

if __name__ == '__main__':
    main()
