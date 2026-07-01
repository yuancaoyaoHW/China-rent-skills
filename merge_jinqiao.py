#!/usr/bin/env python3
"""Geocode and merge fang_jinqiao_parsed.csv into the main JSON."""
import csv
import json
import math
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(r'C:\Users\27493\Downloads\China-rent-skills')
INPUT_CSV = REPO / 'fang_jinqiao_parsed.csv'
JSON_FILE = REPO / 'zhangjiang_listings_15km.json'
KEY_FILE = REPO / 'amap_key.txt'
WORK_LON, WORK_LAT = 121.606222, 31.180732

def read_key():
    if KEY_FILE.exists():
        k = KEY_FILE.read_text(encoding='utf-8').strip()
        if k and not k.startswith('('):
            return k
    return ''

def amap_geocode(query, city, key, timeout=12):
    params = {'key': key, 'address': query, 'city': city, 'output': 'JSON'}
    url = 'https://restapi.amap.com/v3/geocode/geo?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': 'china-rental-research/1.0'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    if data.get('status') != '1' or not data.get('geocodes'):
        return None
    return data['geocodes'][0]

def amap_regeo(lng, lat, key, timeout=12):
    params = {'key': key, 'location': f'{lng},{lat}', 'extensions': 'base', 'output': 'JSON'}
    url = 'https://restapi.amap.com/v3/geocode/regeo?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': 'china-rental-research/1.0'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    if data.get('status') != '1' or not data.get('regeocode'):
        return None
    return data['regeocode']

def haversine_km(lng1, lat1, lng2, lat2):
    r = 6371.0; p = math.pi / 180
    dlat = (lat2 - lat1) * p; dlng = (lng2 - lng1) * p
    a = math.sin(dlat/2)**2 + math.cos(lat1*p)*math.cos(lat2*p)*math.sin(dlng/2)**2
    return round(2 * r * math.asin(math.sqrt(a)), 2)

def main():
    key = read_key()
    print(f'AMap key: {"found" if key else "MISSING"}')

    with INPUT_CSV.open('r', encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    print(f'Input: {len(rows)} rows')

    # Normalize title
    for r in rows:
        comm = r.get('community', '').strip()
        layout = r.get('layout', '').strip()
        r['title'] = f'{comm} {layout}' if comm else r.get('title', '')
        # business_area: convert 'jinqiao' to '金桥'
        biz = r.get('business_area', '')
        biz_map = {'jinqiao': '金桥', 'jinyang': '金杨', 'heqing': '合庆'}
        r['business_area'] = biz_map.get(biz, biz if biz else '金桥')

    # Geocode
    geo_ok = 0
    for i, r in enumerate(rows):
        comm = r.get('community', '').strip()
        query = f'上海浦东{comm}'
        if not key:
            r['longitude'] = ''; r['latitude'] = ''
            continue
        try:
            result = amap_geocode(query, '上海', key)
            if not result or not result.get('location'):
                print(f'  [{i+1}] GEO FAIL: {comm}')
                r['longitude'] = ''; r['latitude'] = ''
                continue
            lng, lat = result['location'].split(',', 1)
            lng, lat = float(lng), float(lat)
            r['longitude'] = lng; r['latitude'] = lat
            km = haversine_km(lng, lat, WORK_LON, WORK_LAT)
            r['work'] = f'{km:.2f}km'
            r['commute'] = f'距张江昆仑芯约{km:.2f}km'
            # Reverse geocode for address
            regeo = amap_regeo(lng, lat, key)
            if regeo:
                addr = regeo.get('formatted_address', '')
                for prefix in ['上海市浦东新区', '上海市浦东', '上海市']:
                    if addr.startswith(prefix):
                        addr = addr[len(prefix):]
                        break
                r['address'] = addr
            else:
                r['address'] = ''
            # Score
            rent = int(r.get('rent', 0))
            score = 70
            if 2000 <= rent <= 3500: score += 15
            elif rent < 2000: score += 20
            if km <= 5: score += 15
            elif km <= 10: score += 8
            elif km > 15: score -= 10
            if r.get('subway'): score += 8
            score = max(0, min(100, score))
            r['score'] = score
            r['action'] = 'contact' if score >= 75 else ('watch' if score >= 55 else 'skip')
            geo_ok += 1
            print(f'  [{i+1}] OK: {comm:25s} ({lng},{lat}) {km}km score={score}')
            time.sleep(0.3)
        except Exception as e:
            print(f'  [{i+1}] ERROR: {comm} -> {e}')
            r['longitude'] = ''; r['latitude'] = ''

    print(f'\nGeocode: {geo_ok}/{len(rows)} ok')

    # Merge into JSON
    data = json.loads(JSON_FILE.read_text(encoding='utf-8'))
    existing_keys = set()
    for item in data['listings']:
        u = str(item.get('url', '')).strip().lower()
        if u:
            existing_keys.add('url:' + u)
        else:
            comm = str(item.get('community', '')).strip().lower()
            existing_keys.add(f'fp:{comm}|{item.get("rent","")}|{item.get("area_m2","")}')

    added = 0
    for r in rows:
        if not isinstance(r.get('longitude'), (int, float)):
            continue
        # Build url (lianjia search)
        r['url'] = f'https://sh.zu.ke.com/zufang/rs{urllib.parse.quote(r["community"])}/'
        dedupe = f'fp:{r["community"].lower()}|{r["rent"]}|{r["area_m2"]}'
        if dedupe in existing_keys:
            continue
        entry = {
            'rank': 0, 'score': r.get('score', 0), 'action': r.get('action', 'watch'),
            'platform': '房天下', 'source_id': '', 'title': r['title'],
            'rent': int(r['rent']), 'layout': r['layout'], 'area_m2': r['area_m2'],
            'district': '浦东', 'business_area': r['business_area'],
            'community': r['community'], 'address': r.get('address', ''),
            'subway': r.get('subway', ''), 'commute': r.get('commute', ''),
            'longitude': r['longitude'], 'latitude': r['latitude'],
            'tags': '', 'risks': '', 'url': r['url'],
            'work': r.get('work', ''),
            'amenity_verified': False, 'amenity_status': '配套待核验',
            'nearest_metro': '地铁待核验', 'nearest_mall': '商场待核验',
            'nearest_market': '', 'residential_priority': 'normal',
        }
        # Add buildYear if not present
        by = data.get('buildYears', {})
        if r['community'] not in by:
            by[r['community']] = {'year': '待查', 'confidence': 'low'}
            data['buildYears'] = by
        data['listings'].append(entry)
        existing_keys.add(dedupe)
        added += 1
        print(f'  ADD: {r["community"]} {r["rent"]}元')

    # Re-sort and renumber
    data['listings'].sort(key=lambda x: int(x.get('score', 0) or 0), reverse=True)
    for i, item in enumerate(data['listings'], 1):
        item['rank'] = i

    JSON_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'\nAdded: {added} new listings')
    print(f'Total listings now: {len(data["listings"])}')
    print(f'Wrote {JSON_FILE}')

if __name__ == '__main__':
    main()
