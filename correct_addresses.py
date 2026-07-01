#!/usr/bin/env python3
"""Correct address field for all non-dislike listings using AMap reverse geocode.

For each listing with longitude/latitude, call AMap regeo API to get the formatted
address. This corrects existing addresses and fills empty ones.
"""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(r'C:\Users\27493\Downloads\China-rent-skills')
JSON_FILE = REPO / 'zhangjiang_listings_15km.json'
KEY_FILE = REPO / 'amap_key.txt'

def read_key():
    if KEY_FILE.exists():
        k = KEY_FILE.read_text(encoding='utf-8').strip()
        if k and not k.startswith('('):
            return k
    import os
    return os.getenv('AMAP_WEB_SERVICE_KEY', '')

def amap_regeo(lng, lat, key, timeout=12):
    """AMap reverse geocoding. Returns dict with formatted_address etc."""
    params = {
        'key': key,
        'location': f'{lng},{lat}',
        'extensions': 'base',
        'output': 'JSON',
    }
    url = 'https://restapi.amap.com/v3/geocode/regeo?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': 'china-rental-research/1.0'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    if data.get('status') != '1' or not data.get('regeocode'):
        return None
    return data['regeocode']

def extract_address(regeo_result):
    """Extract the most precise address from regeo result."""
    addr = regeo_result.get('formatted_address', '')
    comp = regeo_result.get('addressComponent', {})
    # Try to build from township + street + number for more precision
    township = comp.get('township', '')
    street = comp.get('streetNumber', {}).get('street', '') if isinstance(comp.get('streetNumber'), dict) else str(comp.get('streetNumber', ''))
    number = comp.get('streetNumber', {}).get('number', '') if isinstance(comp.get('streetNumber'), dict) else ''
    # Prefer formatted_address but strip the long prefix
    # formatted_address looks like "上海市浦东新区张江镇广兰路XXX弄"
    # We want to keep from the town/district level down
    return addr, township, street, number

def main():
    key = read_key()
    if not key:
        print('ERROR: no AMap key')
        return
    print(f'AMap key: found')

    data = json.loads(JSON_FILE.read_text(encoding='utf-8'))
    listings = data['listings']

    # Load preferences to find dislike URLs
    prefs_file = REPO / 'rental_preferences.json'
    dislike_urls = set()
    if prefs_file.exists():
        prefs = json.loads(prefs_file.read_text(encoding='utf-8')).get('preferences', {})
        dislike_urls = set(u for u, p in prefs.items() if p.get('pref') == 'dislike')

    # Target: non-dislike listings
    targets = [x for x in listings if x.get('url') not in dislike_urls]
    print(f'Total listings: {len(listings)}, dislike: {len(dislike_urls)}, to correct: {len(targets)}')

    fixed = 0
    for i, item in enumerate(targets):
        lng = item.get('longitude')
        lat = item.get('latitude')
        if not isinstance(lng, (int, float)) or not isinstance(lat, (int, float)):
            print(f'  [{i+1}] SKIP (no coords): {item.get("community","")}')
            continue

        try:
            result = amap_regeo(lng, lat, key)
            if not result:
                print(f'  [{i+1}] FAIL: {item.get("community","")}')
                continue
            addr, township, street, number = extract_address(result)
            # Use formatted_address, strip "上海市" prefix for compactness
            clean_addr = addr
            for prefix in ['上海市', '上海', '上海市浦东新区', '上海市浦东']:
                if clean_addr.startswith(prefix):
                    clean_addr = clean_addr[len(prefix):]
                    break
            # If we have street+number, prefer that for precision
            if street and number:
                street_addr = f'{street}{number}'
                if len(street_addr) > 2:
                    clean_addr = street_addr

            old_addr = item.get('address', '')
            if clean_addr and clean_addr != old_addr:
                item['address'] = clean_addr
                fixed += 1
                tag = 'FIXED' if not old_addr else 'UPDATED'
                print(f'  [{i+1}] {tag}: {item.get("community",""):20s} -> {clean_addr[:40]}')
            time.sleep(0.25)
        except Exception as e:
            print(f'  [{i+1}] ERROR: {item.get("community","")} -> {e}')

    JSON_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'\nCorrected: {fixed}/{len(targets)}')
    print(f'Wrote {JSON_FILE}')

if __name__ == '__main__':
    main()
