---
name: china-rental-research
description: Collect, normalize, compare, geocode, map, and rank rental listings from Chinese rental platforms and user-provided app/web sources. Use when the user wants help finding a rental in mainland China, gathering listings from Beike/Lianjia, Ziroom, Anjuke/58, Douban groups, Xiaohongshu, Xianyu, WeChat-shared pages, screenshots, exported HTML, CSV, or copied listing text; deduplicating listings; extracting rent, location, room type, area, floor, subway, fees, contact notes, risks, commute, and AMap/Gaode coordinates; generating a map visualization; and producing a shortlist or spreadsheet. The skill must respect platform rules and must not bypass login, CAPTCHA, anti-bot systems, private APIs, paywalls, or access controls.
---

# China Rental Research

## Core Rules

Use compliant sources only:

- Public web pages, official share links, user-provided screenshots, copied listing text, exported HTML, CSV, or manually saved pages.
- User-authorized logged-in browsing only when the user operates the session or explicitly provides the page content.
- Do not reverse engineer mobile app APIs, bypass CAPTCHA, evade anti-bot controls, scrape private messages, harvest phone numbers at scale, or automate actions that violate platform rules.
- Prefer small, targeted collection over broad crawling. Keep requests slow and bounded when using browser/search tools.

If a target platform blocks access, ask the user for share links, screenshots, saved pages, or copied listing text.

## Workflow

1. Clarify the search brief if missing:
   - City and target districts/商圈.
   - Budget range and acceptable 押付.
   - Whole rental vs shared rental, room count, commute destination, subway preference.
   - Hard filters: pets, elevator, floor, orientation, renovation, move-in date, gender restriction, cooking, noise.

2. Collect listings from available sources:
   - Public search results or platform share pages.
   - User-supplied app screenshots or copied text.
   - CSV/JSON/HTML exports.
   - Read `references/platforms.md` when deciding per-platform tactics.

3. Extract each listing into the canonical schema:
   - Use `references/schema.md` for fields and normalization rules.
   - Preserve source URL and raw evidence whenever possible.
   - Mark uncertain values as empty and add notes rather than inventing details.

4. Normalize, deduplicate, and score:
   - Use `scripts/normalize_listings.py` for CSV/JSON inputs when a file is available.
   - Deduplicate by source URL first, then by title + district/address + rent + area.
   - Score against user priorities. Explain major penalties such as high agency fee, fake-looking listing, long commute, poor lighting, or suspiciously low price.

5. Geocode and visualize when location comparison matters:
   - Use `scripts/geocode_visualize.py` for structured CSV/JSON shortlists.
   - Read `references/amap.md` before using AMap/Gaode APIs.
   - Prefer exact address or community; if only subway/business area is known, mark the result as approximate in `geocode_precision` and `risks`.
   - Do not expose API keys in shared artifacts unless the user explicitly accepts that tradeoff.

6. Deliver a decision-oriented result:
   - A ranked shortlist with 5-15 candidates.
   - A compact comparison table.
   - A local map HTML when coordinates are available or geocoding succeeds.
   - A "contact/watch/skip" recommendation for each candidate.
   - Clear follow-up questions for the agent/landlord.

## Output Table

Prefer this column order:

| rank | action | score | platform | title | rent | deposit_payment | layout | area_m2 | district | address | subway | commute | longitude | latitude | floor | orientation | tags | risks | url |
|---|---|---:|---|---|---:|---|---|---:|---|---|---|---|---:|---:|---|---|---|---|---|

Actions:

- `contact`: worth contacting now.
- `watch`: keep as backup or verify missing info.
- `skip`: likely poor fit or high risk.

## Script Usage

For structured files:

```bash
python scripts/normalize_listings.py input.csv --output shortlist.csv --format csv --budget-max 6500 --commute-max-min 45
python scripts/normalize_listings.py input.json --output shortlist.json --format json --budget-max 6500
```

The script accepts common Chinese/English field aliases and emits normalized columns plus a basic score. Use it as a first pass; adjust scoring in the final answer based on the user's actual priorities.

For AMap/Gaode geocoding and map visualization:

```bash
export AMAP_WEB_SERVICE_KEY="your-web-service-key"
python scripts/geocode_visualize.py shortlist.csv --city 上海 --output geocoded.csv --map-html rental-map.html

export AMAP_JS_KEY="your-js-api-key"
python scripts/geocode_visualize.py shortlist.csv --city 上海 --output geocoded.csv --map-html rental-map.html --embed-js-key
```

If `AMAP_JS_KEY` is not embedded, the generated HTML will ask for a JS API key when opened. Prefer this for shareable artifacts because embedded browser keys are visible in the file.

## Incremental Listings: Data-View Separation (Preview Page)

The `zhangjiang_shortlist_15km_preview.html` page separates data from view: listings, amenities, and build-year notes live in a sibling `zhangjiang_listings_15km.json` file, and the page fetches it at runtime via `fetch('zhangjiang_listings_15km.json', {cache:'no-store'})`. The same `rental_pref_service.py` serves the JSON as a static file — no backend change needed.

**Why this matters:** adding a new batch of listings no longer requires editing HTML or regenerating the page. You append to the JSON and refresh the browser — the map and cards update immediately.

### Adding a batch of incremental listings

```bash
# 1. Normalize + geocode the new batch (produces CSV/JSON with longitude/latitude)
python scripts/normalize_listings.py new_batch.csv --output new_batch_normalized.csv --format csv --budget-max 4000
python scripts/geocode_visualize.py new_batch_normalized.csv --city 上海 --output new_batch_geocoded.csv --skip-geocode  # if coords already present

# 2. Merge into the preview JSON (dedupes by URL; preserves hand-annotated rich fields on existing entries)
python scripts/append_listings.py new_batch_geocoded.csv --json zhangjiang_listings_15km.json

# 3. Refresh the browser — no service restart needed
#    http://127.0.0.1:8766/zhangjiang_shortlist_15km_preview.html
```

`append_listings.py` behaviour:
- **Existing listing (same URL, case-insensitive):** only fills base fields that are empty in the JSON entry. Never overwrites hand-annotated fields (`amenity_verified`, `nearest_metro`, `nearest_mall`, `buildYears`, `work`, `residential_priority`).
- **New listing:** inserts with rich fields defaulted to `配套待核验` / `地铁待核验` / `amenity_verified: false`, computes `work` km from `--work-lon`/`--work-lat` (default: 张江昆仑芯 121.606222, 31.180732), assigns the next rank.
- Re-sorts all listings by score desc and renumbers rank.
- `--dry-run` prints the plan without writing.

### Hand-annotated rich fields

These fields are NOT produced by `normalize_listings.py` or `geocode_visualize.py` — they come from manual research (POI verification, build-year lookup, amenity confirmation). The merge script preserves them on existing entries and defaults them on new entries for later annotation:

| Field | Source | Default for new |
|---|---|---|
| `amenity_verified`, `amenity_status` | manual POI check | `false` / `配套待核验` |
| `nearest_metro`, `nearest_mall`, `nearest_market` | manual POI check | `地铁待核验` / `商场待核验` / `""` |
| `residential_priority` | manual judgment | `normal` |
| `buildYears` (separate JSON object) | manual lookup | key added on demand |

When you annotate a new listing, edit `zhangjiang_listings_15km.json` directly (the `listings` array entry and, for build year, the `buildYears` object keyed by `community`). The page picks up changes on next refresh.

## Quality Checks

Before finalizing:

- Confirm every high-ranked listing has a source or raw evidence.
- Flag listings with missing address, vague photos/text, "价格面议", extremely low rent, or unclear fee structure.
- Flag approximate geocoding, especially when the coordinate came from a subway station, business area, or vague community name.
- Separate platform facts from inferred judgments.
- State when data may be stale because rental listings move quickly.
