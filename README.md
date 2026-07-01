# China Rent Skills

国内租房房源研究工作区：采集、清洗、去重、地理编码、可视化、打分排名国内各大租房平台的房源数据。

本仓库以上海张江板块为样本，演示从安居客、贝壳/链家、自如、房天下、58 等平台合规采集房源 → 规范化 → 地理编码 → 地图可视化 → 候选清单排名的完整流程。

## 目录结构

```
.
├── china-rental-research/        # Hermes Agent Skill（可复用工作流）
│   ├── SKILL.md                  # 技能定义：工作流、合规规则、输出规范
│   ├── agents/openai.yaml        # 技能接入配置
│   ├── references/
│   │   ├── platforms.md          # 各平台采集策略与风险点
│   │   ├── schema.md             # 房源规范字段与风险标签
│   │   └── amap.md               # 高德/AMap 地理编码与地图可视化
│   └── scripts/
│       ├── normalize_listings.py # CSV/JSON 规范化 + 基础打分
│       └── geocode_visualize.py  # 高德地理编码 + HTML 地图生成
│
├── *_pw.html                     # 平台原始页面快照（采集证据）
├── anjuke_*.json / *.csv         # 安居客采集 → 清洗 → 打分数据链
├── beike_*.json                  # 贝壳采集数据
├── fang_*.json / fang_*_zr.html  # 房天下采集数据
├── zhangjiang_*.csv              # 张江板块候选/地理编码清单
└── zhangjiang_*.html             # 地图可视化与候选预览页
```

## 数据流水线

```
平台页面快照 (*_pw.html)
        │
        ▼
原始 JSON (anjuke_raw_page1.json / beike_raw.json)
        │
        ▼ 规范化 (normalize_listings.py)
规范 JSON (anjuke_all_target_v3.json / anjuke_merged.json)
        │
        ▼ 半径筛选 + 打分
候选清单 (anjuke_final_scored_v4.json / anjuke_shortlist_15km.csv)
        │
        ▼ 地理编码 (geocode_visualize.py)
坐标 + 地图 (zhangjiang_shortlist_15km_geocoded.csv / zhangjiang_rental_map_15km.html)
        │
        ▼ 排名预览
最终候选 (zhangjiang_shortlist_15km_preview.html)
```

## Skill 使用

`china-rental-research` 是一个 Hermes Agent Skill，封装了国内租房研究的完整工作流。

### 安装到 Hermes

将 `china-rental-research/` 目录复制到 Hermes 的 skills 目录：

```bash
# Windows
cp -r china-rental-research/ ~/AppData/Local/hermes/skills/

# Linux / macOS
cp -r china-rental-research/ ~/.hermes/skills/
```

### 脚本独立使用

两个脚本不依赖 Skill 运行时，可单独使用：

```bash
# 规范化 CSV/JSON 房源数据 + 基础打分
python china-rental-research/scripts/normalize_listings.py input.csv \
    --output shortlist.csv --format csv --budget-max 4000

# 高德地理编码 + 生成地图 HTML
export AMAP_WEB_SERVICE_KEY="your-web-service-key"
python china-rental-research/scripts/geocode_visualize.py shortlist.csv \
    --city 上海 --output geocoded.csv --map-html rental-map.html
```

脚本接受中英文字段别名（`租金`/`rent`、`面积`/`area_m2` 等），详情见 `references/schema.md`。

## 样本数据说明

本仓库包含上海张江板块的一次完整采集样本（2026-06）：

| 阶段 | 关键文件 | 说明 |
|------|----------|------|
| 采集 | `anjuke_zhangjiang_pw.html`、`beike_zhangjiang_pw.html`、`fang_zhangjiang_zr.html` | 原始页面快照 |
| 清洗 | `anjuke_candidates_clean.csv`、`anjuke_merged.json` | 规范化后的候选池 |
| 打分 | `anjuke_final_scored_v4.json` | 含分数与 action 的排名清单 |
| 地理编码 | `zhangjiang_shortlist_15km_geocoded.csv` | 15km 通勤圈内带坐标的候选 |
| 可视化 | `zhangjiang_rental_map_15km.html` | 高德地图标记页（需 JS API key） |
| 预览 | `zhangjiang_shortlist_15km_preview.html` | 最终候选对比预览页 |

## 合规声明

- 仅使用公开网页、官方分享链接、用户提供的截图/复制文本/导出页面。
- 不逆向移动 App API、不绕过验证码、不规避反爬控制、不批量抓取联系方式。
- 平台拦截时改用用户提供的分享链接、截图或复制文本作为数据源。
- 地理编码使用高德/AMap 公开 Web Service API，坐标为 GCJ-02。
- 不在共享产物中嵌入 API key；地图 HTML 默认以非嵌入模式生成。

## 技术栈

- **采集**：人工 + 浏览器快照（合规优先）
- **处理**：Python 3.11（标准库 + 无第三方依赖脚本）
- **地理编码**：高德地图 Web Service API + JS API
- **可视化**：原生 HTML + 高德地图 JS SDK

## License

MIT
