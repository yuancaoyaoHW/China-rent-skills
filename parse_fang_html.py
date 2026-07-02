#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
parse_fang_html.py — 解析房天下(fang.com)整租搜索结果页 HTML,提取房源并输出/合并 CSV。

字段: title, community, business_area, layout, area_m2, rent, orientation,
      subway, url, platform(房天下), district(浦东)

用法:
    # 解析单个 HTML, 覆盖写出到 csv
    python parse_fang_html.py <input.html> --output new_batch_fang.csv --mode write

    # 解析多个 HTML, 合并追加到同一个 csv (自动去重)
    python parse_fang_html.py a.html b.html --output new_batch_fang.csv --mode merge

    # 默认: 解析两个已有 HTML
    python parse_fang_html.py

合规: 只解析本地已保存的公开搜索页, 不联网, 不绕反爬。
"""
import csv
import html
import os
import re
import sys
import urllib.parse

# ---------- 路径 ----------
BASE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INPUTS = [
    os.path.join(BASE, 'fang_sanlin_zr.html'),
    os.path.join(BASE, 'fang_jinqiao_zr.html'),
]
DEFAULT_OUTPUT = os.path.join(BASE, 'new_batch_fang.csv')

CSV_FIELDS = [
    'title', 'community', 'business_area', 'layout', 'area_m2',
    'rent', 'orientation', 'subway', 'url', 'platform', 'district',
]

# 保留的户型 (1室1厅 / 2室1厅 / 2室2厅)
ALLOWED_LAYOUTS = re.compile(r'^(1室1厅|2室1厅|2室2厅)$')
RENT_MIN, RENT_MAX = 2000, 4000
FANG_BASE_URL = 'https://sh.zu.fang.com/'


# ---------- 单页解析 ----------
def parse_html(html_text: str, source_tag: str = ''):
    """返回 list[dict]。用 split-by-title 切块, 避免大正则回溯爆炸。"""
    parts = html_text.split('<p class="title"')
    # 第 0 段是 <head> 等, 跳过
    results = []
    for chunk in parts[1:]:
        end = chunk.find('元/月</p>')
        if end == -1:
            end = chunk.find('元/月')
        if end == -1:
            # 没有价格标记, 取到下一个 <dl 边界
            nxt = chunk.find('<dl class="list')
            if nxt == -1:
                continue
            end = nxt
        block = '<p class="title"' + chunk[:end + 10]

        rec = _parse_block(block)
        if rec is not None:
            rec['_source'] = source_tag
            results.append(rec)
    return results


def _parse_block(block: str):
    """对单个 listing 块做 anchored 解析。失败返回 None。"""
    # title
    tm = re.search(r'title="([^"]+)"', block)
    if not tm:
        return None
    title = tm.group(1).strip()

    hm = re.search(r'<a\b[^>]*href="([^"]+)"', block)
    if not hm:
        return None
    url = urllib.parse.urljoin(FANG_BASE_URL, html.unescape(hm.group(1)).strip())

    # layout: 整租<span...>|</span>2室1厅  -> 取 整租 后到第一个 < 之间
    lm = re.search(r'整租(?:<span[^>]*>\|</span>)?([^<\|]*)', block)
    layout = lm.group(1).strip() if lm else ''
    # 规范化: 有的写 "2室1厅1卫", 取前面的 "2室1厅"
    m2 = re.match(r'(\d+室\d+厅)', layout)
    if m2:
        layout = m2.group(1)

    # area
    am = re.search(r'(\d+\.?\d*)\s*㎡', block)
    area = am.group(1) if am else ''

    # orientation: 朝南 / 朝南北 / 朝东南 ...
    om = re.search(r'(朝[东南西北]+)', block)
    orient = om.group(1) if om else ''

    # business_area + community. 两种格式:
    #   A) 浦东-<a><span>BIZ</span></a>-<a><span>COMMUNITY</span></a>
    #   B) <a><span>浦东</span></a>-张江-<a><span>COMMUNITY</span></a>  (biz 为纯文本)
    biz = ''
    community = ''
    # 先试 A
    bm = re.search(
        r'浦东-<a[^>]*><span>([^<]+)</span></a>-<a[^>]*><span>([^<]+)</span></a>',
        block)
    if bm:
        biz = bm.group(1).strip()
        community = bm.group(2).strip()
    else:
        # 试 B: <a...>浦东</a>-XXX-<a...>COMMUNITY</a>
        bm = re.search(
            r'<a[^>]*><span>浦东</span></a>-([^<>-]+)-<a[^>]*><span>([^<]+)</span></a>',
            block)
        if bm:
            biz = bm.group(1).strip()
            community = bm.group(2).strip()
        else:
            # 兜底: 任意 浦东-XXX-YYY 模式(文本)
            bm = re.search(r'浦东-([^-<>]+)-([^-<>]+)', block)
            if bm:
                biz = bm.group(1).strip()
                community = bm.group(2).strip()

    if not community:
        return None

    # subway: 距14号线昌邑路站约298米
    sm = re.search(r'距([^。]+米)', block)
    subway = sm.group(1).strip() if sm else ''

    # rent
    rm = re.search(r'<span class="price">(\d+)</span>', block)
    if not rm:
        # 兜底: title 里可能带价格
        rm2 = re.search(r'(\d{3,6})\s*元/月', title)
        if not rm2:
            return None
        rent = int(rm2.group(1))
    else:
        rent = int(rm.group(1))

    return {
        'title': title,
        'community': community,
        'business_area': biz,
        'layout': layout,
        'area_m2': area,
        'rent': rent,
        'orientation': orient,
        'subway': subway,
        'url': url,
        'platform': '房天下',
        'district': '浦东',
    }


# ---------- 过滤 / 去重 / 写 CSV ----------
def passes_filter(rec):
    if not (RENT_MIN <= rec['rent'] <= RENT_MAX):
        return False
    if not ALLOWED_LAYOUTS.match(rec['layout']):
        return False
    return True


def dedup_key(rec):
    return f"{rec['title']}|{rec['community']}|{rec['rent']}"


def merge_and_write(all_records, out_path):
    seen = set()
    rows = []
    for rec in all_records:
        k = dedup_key(rec)
        if k in seen:
            continue
        seen.add(k)
        rows.append({f: rec.get(f, '') for f in CSV_FIELDS})
    with open(out_path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(rows)
    return rows


def main():
    args = sys.argv[1:]
    # 简单参数解析
    inputs = []
    output = DEFAULT_OUTPUT
    mode = 'merge'  # 默认合并模式
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--output':
            output = args[i + 1]; i += 2
        elif a == '--mode':
            mode = args[i + 1]; i += 2
        elif a in ('-h', '--help'):
            print(__doc__); return
        else:
            inputs.append(a); i += 1
    if not inputs:
        inputs = DEFAULT_INPUTS

    all_records = []
    per_file_stats = []
    for inp in inputs:
        if not os.path.exists(inp):
            print(f'[SKIP] 文件不存在: {inp}')
            per_file_stats.append((inp, 0, 0, 0))
            continue
        with open(inp, 'r', encoding='utf-8', errors='replace') as f:
            html = f.read()
        recs = parse_html(html, source_tag=os.path.basename(inp))
        kept = [r for r in recs if passes_filter(r)]
        all_records.extend(kept)
        per_file_stats.append((os.path.basename(inp), len(recs), len(kept), len(html)))

    rows = merge_and_write(all_records, output)
    print('===== 解析统计 =====')
    for name, total, kept, hlen in per_file_stats:
        print(f'  {name}: HTML {hlen}B, 解析 {total} 条, 过滤后(2k-4k&户型) {kept} 条')
    print(f'\n输出 CSV: {output}')
    print(f'总行数(去重后): {len(rows)}')

    # 区域分布
    from collections import Counter
    biz_c = Counter(r['business_area'] for r in rows if r['business_area'])
    print('\n各商圈(business_area)分布:')
    for k, v in biz_c.most_common():
        print(f'  {k}: {v}')
    # 户型分布
    lay_c = Counter(r['layout'] for r in rows)
    print('\n户型分布:')
    for k, v in lay_c.most_common():
        print(f'  {k}: {v}')


if __name__ == '__main__':
    main()
