#!/usr/bin/env python3
"""Post-process new_batch_fang.csv: normalize title, geocode via AMap, output new_batch_geocoded.csv."""
import csv
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(r'C:\Users\27493\Downloads\China-rent-skills')
INPUT_CSV = REPO / 'new_batch_fang.csv'
OUTPUT_CSV = REPO / 'new_batch_geocoded.csv'
KEY_FILE = REPO / 'amap_key.txt'
WORK_LON, WORK_LAT = 121.606222, 31.180732

def read_key():
    if KEY_FILE.exists():
        k = KEY_FILE.read_text(encoding='utf-8').strip()
        if k and not k.startswith('('):
            return k
    import os
    return os.getenv('AMAP_WEB_SERVICE_KEY', '')

def amap_geocode(query, city, key, timeout=12):
    params = {'key': key, 'address': query, 'city': city, 'output': 'JSON'}
    url = 'https://restapi.amap.com/v3/geocode/geo?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': 'china-rental-research/1.0'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    if data.get('status') != '1' or not data.get('geocodes'):
        return None
    return data['geocodes'][0]

def haversine_km(lng1, lat1, lng2, lat2):
    import math
    r = 6371.0
    p = math.pi / 180.0
    dlat = (lat2 - lat1) * p
    dlng = (lng2 - lng1) * p
    a = math.sin(dlat/2)**2 + math.cos(lat1*p)*math.cos(lat2*p)*math.sin(dlng/2)**2
    return round(2 * r * math.asin(math.sqrt(a)), 2)

def main():
    key = read_key()
    print(f"AMap key: {'found' if key else 'MISSING'}")

    with INPUT_CSV.open('r', encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    print(f"Input rows: {len(rows)}")

    # Normalize title: use "community layout" instead of marketing blurb
    for r in rows:
        comm = r.get('community', '').strip()
        layout = r.get('layout', '').strip()
        r['title'] = f"{comm} {layout}" if comm else r.get('title', '')

    # Geocode
    geo_ok = geo_fail = 0
    for i, r in enumerate(rows):
        comm = r.get('community', '').strip()
        district = r.get('district', '浦东').strip()
        query = f"上海{district}{comm}"
        r['geocode_query'] = query
        r['geocode_precision'] = 'community'
        if not key:
            r['longitude'] = ''
            r['latitude'] = ''
            r['geocode_precision'] = 'geocode_pending'
            geo_fail += 1
            continue
        try:
            result = amap_geocode(query, '上海', key)
            if not result or not result.get('location'):
                r['longitude'] = ''
                r['latitude'] = ''
                r['geocode_precision'] = 'geocode_failed'
                geo_fail += 1
                print(f"  [{i+1}] FAIL: {comm} -> {query}")
            else:
                lng, lat = result['location'].split(',', 1)
                r['longitude'] = float(lng)
                r['latitude'] = float(lat)
                r['geocode_level'] = result.get('level', '')
                # Compute work distance
                km = haversine_km(float(lng), float(lat), WORK_LON, WORK_LAT)
                r['work'] = f"{km:.2f}km"
                r['commute'] = f"距张江昆仑芯约{km:.2f}km"
                geo_ok += 1
                print(f"  [{i+1}] OK: {comm} -> ({lng}, {lat}) {km}km")
            time.sleep(0.25)
        except Exception as e:
            r['longitude'] = ''
            r['latitude'] = ''
            r['geocode_precision'] = 'geocode_error'
            r['geocode_error'] = str(e)
            geo_fail += 1
            print(f"  [{i+1}] ERROR: {comm} -> {e}")

    # Write output
    fields = ['title','community','business_area','layout','area_m2','rent','orientation',
              'subway','url','platform','district','longitude','latitude','geocode_query',
              'geocode_precision','geocode_level','work','commute','geocode_error']
    with OUTPUT_CSV.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nGeocode: {geo_ok} ok, {geo_fail} fail")
    print(f"Wrote {OUTPUT_CSV}")

    # Within 15km check
    in_range = [r for r in rows if r.get('work') and float(r['work'].replace('km','')) <= 15]
    print(f"Within 15km: {len(in_range)} / {len(rows)}")

if __name__ == '__main__':
    main()
