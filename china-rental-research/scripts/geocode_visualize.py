#!/usr/bin/env python3
"""Geocode China rental listings with AMap and generate an HTML map."""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


LAT_ALIASES = ["latitude", "lat", "纬度"]
LNG_ALIASES = ["longitude", "lng", "lon", "经度"]
OUTPUT_FIELDS = [
    "score",
    "action",
    "platform",
    "source_id",
    "title",
    "rent",
    "deposit_payment",
    "layout",
    "area_m2",
    "district",
    "business_area",
    "community",
    "address",
    "subway",
    "commute",
    "longitude",
    "latitude",
    "geocode_query",
    "geocode_precision",
    "geocode_level",
    "floor",
    "elevator",
    "orientation",
    "renovation",
    "move_in_date",
    "lease_term",
    "landlord_type",
    "tags",
    "risks",
    "url",
    "raw_text",
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


def write_rows(rows: list[dict[str, Any]], path: Path, fmt: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "json":
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        return
    fields = list(OUTPUT_FIELDS)
    for row in rows:
        for key in row.keys():
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def get_first(row: dict[str, Any], names: list[str]) -> str:
    keys = {str(k).strip().lower(): k for k in row.keys()}
    for name in names:
        key = keys.get(name.lower())
        if key is not None and str(row.get(key, "")).strip():
            return str(row[key]).strip()
    return ""


def set_coord(row: dict[str, Any], lng: str, lat: str) -> None:
    row["longitude"] = lng
    row["latitude"] = lat


def has_coord(row: dict[str, Any]) -> bool:
    lng = get_first(row, LNG_ALIASES)
    lat = get_first(row, LAT_ALIASES)
    if not lng or not lat:
        return False
    try:
        float(lng)
        float(lat)
    except ValueError:
        return False
    set_coord(row, lng, lat)
    row.setdefault("geocode_precision", "existing")
    return True


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def append_risk(row: dict[str, Any], risk: str) -> None:
    risks = clean(row.get("risks"))
    items = [item.strip() for item in re.split(r"[,，;；]", risks) if item.strip()]
    if risk not in items:
        items.append(risk)
    row["risks"] = ", ".join(items)


def build_query(row: dict[str, Any], city: str) -> tuple[str, str]:
    district = clean(row.get("district"))
    community = clean(row.get("community"))
    address = clean(row.get("address"))
    subway = clean(row.get("subway"))
    business_area = clean(row.get("business_area"))

    prefix = city + district
    if community and address:
        return prefix + community + address, "exact"
    if community:
        return prefix + community, "community"
    if address:
        return prefix + address, "exact"
    if subway:
        station = re.sub(r"(步行|距离|约).*$", "", subway).strip()
        return city + station, "subway_only"
    if business_area:
        return prefix + business_area, "business_area"
    if district:
        return city + district, "vague"
    return city + clean(row.get("title")), "vague"


def amap_geocode(query: str, city: str, key: str, timeout: int = 12) -> dict[str, Any] | None:
    params = {
        "key": key,
        "address": query,
        "city": city,
        "output": "JSON",
    }
    url = "https://restapi.amap.com/v3/geocode/geo?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "china-rental-research/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if data.get("status") != "1" or not data.get("geocodes"):
        return None
    return data["geocodes"][0]


def geocode_rows(rows: list[dict[str, Any]], city: str, key: str | None, delay: float) -> list[dict[str, Any]]:
    for row in rows:
        if has_coord(row):
            continue
        query, precision = build_query(row, city)
        row["geocode_query"] = query
        row["geocode_precision"] = precision
        if precision != "exact":
            append_risk(row, "geocode_approx")
        if not key:
            append_risk(row, "geocode_failed")
            continue
        try:
            result = amap_geocode(query, city, key)
        except Exception as exc:
            row["geocode_error"] = str(exc)
            append_risk(row, "geocode_failed")
            continue
        if not result or not result.get("location"):
            append_risk(row, "geocode_failed")
            continue
        lng, lat = result["location"].split(",", 1)
        set_coord(row, lng, lat)
        row["geocode_level"] = result.get("level", "")
        if delay > 0:
            time.sleep(delay)
    return rows


def marker_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    markers = []
    for idx, row in enumerate(rows, start=1):
        try:
            lng = float(clean(row.get("longitude")))
            lat = float(clean(row.get("latitude")))
        except ValueError:
            continue
        markers.append(
            {
                "rank": idx,
                "lng": lng,
                "lat": lat,
                "score": clean(row.get("score")),
                "action": clean(row.get("action")) or "watch",
                "platform": clean(row.get("platform")),
                "title": clean(row.get("title")),
                "rent": clean(row.get("rent")),
                "layout": clean(row.get("layout")),
                "area_m2": clean(row.get("area_m2")),
                "district": clean(row.get("district")),
                "community": clean(row.get("community")),
                "address": clean(row.get("address")),
                "subway": clean(row.get("subway")),
                "commute": clean(row.get("commute")),
                "precision": clean(row.get("geocode_precision")),
                "risks": clean(row.get("risks")),
                "url": clean(row.get("url")),
            }
        )
    return markers


def generate_html(rows: list[dict[str, Any]], path: Path, city: str, js_key: str | None) -> None:
    markers = marker_rows(rows)
    center = [116.397428, 39.90923]
    if markers:
        center = [markers[0]["lng"], markers[0]["lat"]]
    data_json = json.dumps(markers, ensure_ascii=False)
    key_json = json.dumps(js_key or "")
    html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(city)}租房候选地图</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #172033; }}
    #app {{ display: grid; grid-template-columns: 360px 1fr; height: 100vh; }}
    aside {{ overflow: auto; border-right: 1px solid #e5e7eb; background: #fafafa; padding: 14px; }}
    #map {{ min-width: 0; }}
    h1 {{ font-size: 18px; margin: 0 0 8px; }}
    .hint {{ font-size: 12px; color: #64748b; margin-bottom: 12px; line-height: 1.45; }}
    .keybox {{ display: none; margin: 10px 0 14px; padding: 10px; border: 1px solid #f59e0b; background: #fffbeb; border-radius: 8px; }}
    .keybox input {{ width: 100%; padding: 8px; margin-top: 8px; border: 1px solid #d1d5db; border-radius: 6px; }}
    .item {{ border: 1px solid #e5e7eb; background: white; border-radius: 8px; padding: 10px; margin-bottom: 10px; cursor: pointer; }}
    .item:hover {{ border-color: #2563eb; }}
    .top {{ display: flex; justify-content: space-between; gap: 8px; align-items: baseline; }}
    .title {{ font-weight: 700; line-height: 1.25; }}
    .rent {{ color: #dc2626; font-weight: 700; white-space: nowrap; }}
    .meta, .risk {{ font-size: 12px; color: #475569; margin-top: 6px; line-height: 1.45; }}
    .risk {{ color: #b45309; }}
    .badge {{ display: inline-block; border-radius: 999px; padding: 2px 8px; font-size: 12px; margin-right: 4px; color: white; }}
    .contact {{ background: #16a34a; }}
    .watch {{ background: #2563eb; }}
    .skip {{ background: #64748b; }}
    @media (max-width: 760px) {{ #app {{ grid-template-columns: 1fr; grid-template-rows: 45vh 55vh; }} aside {{ order: 2; border-right: 0; border-top: 1px solid #e5e7eb; }} #map {{ order: 1; }} }}
  </style>
</head>
<body>
<div id="app">
  <aside>
    <h1>{html.escape(city)}租房候选地图</h1>
    <div class="hint">坐标来自高德 GCJ-02。subway_only / business_area / vague 表示位置只是近似点，联系前要核实小区和门牌。</div>
    <div id="keybox" class="keybox">
      需要高德 JS API key 才能渲染地图。输入后只在当前浏览器地址栏使用。
      <input id="keyInput" placeholder="AMAP_JS_KEY">
    </div>
    <div id="list"></div>
  </aside>
  <div id="map"></div>
</div>
<script>
const RENTAL_MARKERS = {data_json};
const EMBEDDED_AMAP_KEY = {key_json};
const COLORS = {{ contact: "#16a34a", watch: "#2563eb", skip: "#64748b" }};
function esc(s) {{ return String(s || "").replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c])); }}
function keyFromUrl() {{ return new URLSearchParams(location.search).get("key") || ""; }}
function renderList(focus) {{
  const list = document.getElementById("list");
  list.innerHTML = RENTAL_MARKERS.map((m, i) => `
    <div class="item" onclick="window.focusMarker && window.focusMarker(${{i}})">
      <div class="top"><div class="title">#${{m.rank}} ${{esc(m.title || m.community || "未命名房源")}}</div><div class="rent">${{esc(m.rent)}} 元/月</div></div>
      <div class="meta"><span class="badge ${{esc(m.action)}}">${{esc(m.action)}}</span> 分数 ${{esc(m.score)}} · ${{esc(m.platform)}} · ${{esc(m.layout)}} · ${{esc(m.area_m2)}}㎡</div>
      <div class="meta">${{esc([m.district, m.community, m.address].filter(Boolean).join(" · "))}}</div>
      <div class="meta">${{esc([m.subway, m.commute, m.precision].filter(Boolean).join(" · "))}}</div>
      ${{m.risks ? `<div class="risk">风险：${{esc(m.risks)}}</div>` : ""}}
    </div>`).join("");
}}
function loadAmap(key) {{
  if (!key) {{
    document.getElementById("keybox").style.display = "block";
    document.getElementById("keyInput").addEventListener("change", e => {{
      const url = new URL(location.href);
      url.searchParams.set("key", e.target.value.trim());
      location.href = url.toString();
    }});
    renderList();
    return;
  }}
  const script = document.createElement("script");
  script.src = "https://webapi.amap.com/maps?v=2.0&key=" + encodeURIComponent(key);
  script.onload = initMap;
  document.head.appendChild(script);
}}
function initMap() {{
  renderList();
  const center = RENTAL_MARKERS.length ? [RENTAL_MARKERS[0].lng, RENTAL_MARKERS[0].lat] : {json.dumps(center)};
  const map = new AMap.Map("map", {{ zoom: 12, center }});
  const info = new AMap.InfoWindow({{ offset: new AMap.Pixel(0, -28) }});
  const markers = RENTAL_MARKERS.map((m, i) => {{
    const marker = new AMap.Marker({{
      position: [m.lng, m.lat],
      title: m.title,
      label: {{ content: String(m.rank), direction: "top" }}
    }});
    marker.setMap(map);
    marker.on("click", () => {{
      const link = m.url ? `<p><a href="${{esc(m.url)}}" target="_blank">打开来源</a></p>` : "";
      info.setContent(`<strong>#${{m.rank}} ${{esc(m.title || m.community)}}</strong>
        <p>${{esc(m.platform)}} · ${{esc(m.rent)}} 元/月 · ${{esc(m.layout)}} · ${{esc(m.area_m2)}}㎡</p>
        <p>${{esc([m.district, m.community, m.address].filter(Boolean).join(" · "))}}</p>
        <p>${{esc([m.subway, m.commute, m.precision].filter(Boolean).join(" · "))}}</p>
        <p>${{esc(m.risks ? "风险：" + m.risks : "")}}</p>${{link}}`);
      info.open(map, marker.getPosition());
    }});
    return marker;
  }});
  if (markers.length > 1) map.setFitView(markers);
  window.focusMarker = i => {{
    const marker = markers[i];
    if (!marker) return;
    map.setZoomAndCenter(15, marker.getPosition());
    marker.emit("click", {{ target: marker }});
  }};
}}
loadAmap(EMBEDDED_AMAP_KEY || keyFromUrl());
</script>
</body>
</html>
"""
    path.write_text(html_text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--city", required=True, help="City name, e.g. 上海 or 北京")
    parser.add_argument("--output", type=Path, default=Path("geocoded_listings.csv"))
    parser.add_argument("--format", choices=["csv", "json"], default="csv")
    parser.add_argument("--map-html", type=Path, default=Path("rental_map.html"))
    parser.add_argument("--web-service-key", default=os.getenv("AMAP_WEB_SERVICE_KEY"))
    parser.add_argument("--js-key", default=os.getenv("AMAP_JS_KEY"))
    parser.add_argument("--embed-js-key", action="store_true", help="Embed AMAP_JS_KEY into HTML; convenient but visible in the file")
    parser.add_argument("--skip-geocode", action="store_true", help="Only visualize rows that already have longitude/latitude")
    parser.add_argument("--delay", type=float, default=0.15, help="Delay between geocoding calls")
    args = parser.parse_args()

    rows = read_rows(args.input)
    key = None if args.skip_geocode else args.web_service_key
    rows = geocode_rows(rows, args.city, key, args.delay)
    write_rows(rows, args.output, args.format)
    generate_html(rows, args.map_html, args.city, args.js_key if args.embed_js_key else None)
    markers = len(marker_rows(rows))
    print(f"Wrote {len(rows)} rows to {args.output}")
    print(f"Wrote map with {markers} markers to {args.map_html}")
    if not args.embed_js_key:
        print("Open the HTML and enter an AMap JS API key, or pass --embed-js-key with AMAP_JS_KEY set.")


if __name__ == "__main__":
    main()
