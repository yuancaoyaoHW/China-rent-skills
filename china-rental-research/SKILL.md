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

## Quality Checks

Before finalizing:

- Confirm every high-ranked listing has a source or raw evidence.
- Flag listings with missing address, vague photos/text, "价格面议", extremely low rent, or unclear fee structure.
- Flag approximate geocoding, especially when the coordinate came from a subway station, business area, or vague community name.
- Separate platform facts from inferred judgments.
- State when data may be stale because rental listings move quickly.
