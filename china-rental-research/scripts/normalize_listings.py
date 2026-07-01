#!/usr/bin/env python3
"""Normalize rental listing CSV/JSON files into a comparable shortlist."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any


FIELD_ALIASES = {
    "platform": ["platform", "source", "来源", "平台"],
    "source_id": ["source_id", "listing_id", "id", "编号", "房源编号"],
    "url": ["url", "link", "链接", "房源链接"],
    "title": ["title", "标题", "名称", "房源标题"],
    "rent": ["rent", "price", "租金", "价格", "月租", "monthly_rent"],
    "deposit_payment": ["deposit_payment", "押付", "付款方式", "押金", "费用", "fee"],
    "layout": ["layout", "户型", "房型", "room_type"],
    "area_m2": ["area_m2", "area", "面积", "建面", "size"],
    "district": ["district", "区", "城区", "行政区"],
    "business_area": ["business_area", "商圈", "板块"],
    "community": ["community", "小区", "楼盘"],
    "address": ["address", "地址", "位置", "location"],
    "subway": ["subway", "地铁", "metro", "station"],
    "commute": ["commute", "通勤", "commute_min", "通勤时间"],
    "floor": ["floor", "楼层"],
    "elevator": ["elevator", "电梯"],
    "orientation": ["orientation", "朝向"],
    "renovation": ["renovation", "装修", "配置"],
    "move_in_date": ["move_in_date", "入住时间", "可入住"],
    "lease_term": ["lease_term", "租期"],
    "landlord_type": ["landlord_type", "房东类型", "发布者", "出租方"],
    "contact": ["contact", "联系人", "联系方式"],
    "tags": ["tags", "标签", "优点"],
    "risks": ["risks", "风险", "缺点"],
    "raw_text": ["raw_text", "原文", "描述", "详情"],
}

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


def first_value(row: dict[str, Any], aliases: list[str]) -> Any:
    normalized_keys = {str(k).strip().lower(): k for k in row.keys()}
    for alias in aliases:
        key = normalized_keys.get(alias.lower())
        if key is not None:
            value = row.get(key)
            if value not in (None, ""):
                return value
    return ""


def parse_money(value: Any) -> int | None:
    text = str(value or "").strip().lower().replace(",", "")
    if not text:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*(万|w)", text)
    if match:
        return int(float(match.group(1)) * 10000)
    match = re.search(r"(\d+(?:\.\d+)?)\s*k", text)
    if match:
        return int(float(match.group(1)) * 1000)
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if match:
        return int(float(match.group(1)))
    return None


def parse_area(value: Any) -> float | None:
    text = str(value or "").strip().replace(",", "")
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    return float(match.group(1)) if match else None


def parse_minutes(value: Any) -> int | None:
    text = str(value or "").strip()
    match = re.search(r"(\d+)\s*(分钟|min|mins?)", text, flags=re.I)
    if match:
        return int(match.group(1))
    if re.fullmatch(r"\d+", text):
        return int(text)
    return None


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for field, aliases in FIELD_ALIASES.items():
        out[field] = clean_text(first_value(row, aliases))

    rent = parse_money(out.get("rent"))
    area = parse_area(out.get("area_m2"))
    if rent is not None:
        out["rent"] = rent
    if area is not None:
        out["area_m2"] = area

    return out


def dedupe_key(row: dict[str, Any]) -> str:
    if row.get("url"):
        return "url:" + str(row["url"]).strip()
    parts = [
        str(row.get("title", "")),
        str(row.get("district", "")),
        str(row.get("community", "")),
        str(row.get("address", "")),
        str(row.get("rent", "")),
        str(row.get("area_m2", "")),
    ]
    digest = hashlib.sha1("|".join(parts).lower().encode("utf-8")).hexdigest()
    return "fp:" + digest


def score_row(row: dict[str, Any], budget_max: int | None, commute_max_min: int | None) -> tuple[int, str]:
    score = 70
    risks = str(row.get("risks", ""))

    rent = row.get("rent")
    if isinstance(rent, int) and budget_max:
        if rent <= budget_max:
            score += 10
        else:
            score -= min(30, int((rent - budget_max) / max(budget_max, 1) * 100))

    commute = parse_minutes(row.get("commute"))
    if commute is not None and commute_max_min:
        if commute <= commute_max_min:
            score += 8
        else:
            score -= min(25, commute - commute_max_min)

    if row.get("subway"):
        score += 5
    if row.get("address") or row.get("community"):
        score += 5
    else:
        risks = append_risk(risks, "address_vague")
        score -= 8
    if not row.get("deposit_payment"):
        risks = append_risk(risks, "fee_unclear")
        score -= 5

    bad_markers = ["骗子", "付定金", "不看房", "虚假", "中介费不明"]
    raw = " ".join(str(row.get(k, "")) for k in ("title", "raw_text", "risks"))
    if any(marker in raw for marker in bad_markers):
        score -= 25

    score = max(0, min(100, score))
    if score >= 78:
        action = "contact"
    elif score >= 58:
        action = "watch"
    else:
        action = "skip"

    row["risks"] = risks
    return score, action


def append_risk(risks: str, risk: str) -> str:
    items = [item.strip() for item in re.split(r"[,，;；]", risks) if item.strip()]
    if risk not in items:
        items.append(risk)
    return ", ".join(items)


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
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("normalized_listings.csv"))
    parser.add_argument("--format", choices=["csv", "json"], default="csv")
    parser.add_argument("--budget-max", type=int)
    parser.add_argument("--commute-max-min", type=int)
    args = parser.parse_args()

    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for raw in read_rows(args.input):
        row = normalize_row(raw)
        key = dedupe_key(row)
        if key in seen:
            continue
        seen.add(key)
        score, action = score_row(row, args.budget_max, args.commute_max_min)
        row["score"] = score
        row["action"] = action
        rows.append({field: row.get(field, "") for field in OUTPUT_FIELDS})

    rows.sort(key=lambda item: int(item.get("score") or 0), reverse=True)
    write_rows(rows, args.output, args.format)
    print(f"Wrote {len(rows)} normalized listings to {args.output}")


if __name__ == "__main__":
    main()
