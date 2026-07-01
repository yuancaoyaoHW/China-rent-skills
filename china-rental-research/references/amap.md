# AMap / Gaode Integration

Use this file when adding location coordinates or map visualization.

## Keys

- Use a Web Service API key for server-side geocoding: `AMAP_WEB_SERVICE_KEY`.
- Use a JS API key for browser map rendering: `AMAP_JS_KEY`.
- Do not hard-code keys into scripts or skill files.
- Embedded JS keys are visible to anyone who opens the HTML. Prefer non-embedded mode for shareable files.

## Geocoding

Use AMap Web Service geocoding:

- Endpoint: `https://restapi.amap.com/v3/geocode/geo`
- Required parameters: `key`, `address`
- Recommended parameter: `city`
- Output: JSON

Build the address query from the most precise available parts:

1. `city + district + community + address`
2. `city + district + community`
3. `city + district + address`
4. `city + subway`
5. `city + business_area`

Mark precision:

- `exact`: exact community/address or street address exists.
- `community`: community is present but exact building is unknown.
- `subway_only`: only subway station/line is known.
- `business_area`: only business area or district center is known.
- `vague`: weak query; use only for rough visualization.
- `existing`: coordinates were already present in input.

## Coordinates

AMap uses GCJ-02 coordinates in mainland China. Keep the fields named `longitude` and `latitude`, and avoid mixing with WGS-84 unless the output clearly states the coordinate system.

## Visualization

Generate a local HTML file with AMap JS API markers:

- Marker title: rank/title/rent.
- Marker color by action: contact, watch, skip.
- Info window: platform, rent, layout, address/community, subway, risks, source URL.
- Sidebar: ranked list with click-to-focus.

If exact locations are sensitive, round coordinates or only visualize at community/subway level.
