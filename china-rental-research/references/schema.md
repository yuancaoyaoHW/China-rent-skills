# Canonical Rental Listing Schema

Use this schema for extracted listings. Leave unknown fields blank.

## Fields

| field | meaning |
|---|---|
| platform | Source platform, e.g. 贝壳, 链家, 自如, 安居客, 豆瓣, 小红书 |
| source_id | Listing ID if visible |
| url | Source URL or share link |
| title | Listing title |
| rent | Monthly rent as number in RMB |
| deposit_payment | 押付, service fee, agency fee notes |
| layout | 户型, e.g. 1室1厅, 主卧, 次卧 |
| area_m2 | Area in square meters |
| district | 区 |
| business_area | 商圈 |
| community | 小区 |
| address | Address or approximate location |
| subway | Subway station, line, walking distance |
| commute | Commute estimate and route notes |
| longitude | AMap/Gaode longitude in GCJ-02 |
| latitude | AMap/Gaode latitude in GCJ-02 |
| geocode_query | Address query sent to geocoding provider |
| geocode_precision | exact, community, subway_only, business_area, vague, or existing |
| geocode_level | Provider-returned match level when available |
| floor | Floor and total floors |
| elevator | yes/no/unknown |
| orientation | 朝向 |
| renovation | 装修/家具/家电 |
| move_in_date | Earliest move-in date |
| lease_term | Lease period |
| landlord_type | landlord, agent, sublet, platform, unknown |
| contact | Contact note, not bulk-harvested phone data |
| tags | Positive fit tags |
| risks | Risk notes |
| raw_text | Short raw evidence excerpt |

## Normalization

- Convert `租金`, `价格`, `月租`, `rent_monthly` to `rent`.
- Convert `面积`, `建面`, `area`, `size` to `area_m2`.
- Convert Chinese rent text:
  - `6500元/月` -> `6500`
  - `6.5k` -> `6500`
  - `0.8万` -> `8000`
- Preserve `押一付三`, `押一付一`, `服务费10%`, `中介费` in `deposit_payment`.
- Do not turn rough locations like "静安寺附近" into exact addresses.
- Store AMap/Gaode coordinates as GCJ-02 `longitude`/`latitude`; do not mix with WGS-84 coordinates without labeling conversion.

## Risk Labels

Use short labels in `risks`:

- `fee_unclear`: fee or deposit unclear.
- `address_vague`: exact community/address absent.
- `too_cheap`: price far below nearby market.
- `stale`: old post or unknown availability.
- `agent_unclear`: landlord/agent identity unclear.
- `photo_mismatch`: photos may not match the unit.
- `no_viewing_before_payment`: asks for payment before viewing.
- `short_lease`: lease term may not fit user.
- `geocode_approx`: coordinate is based on a rough area, subway station, or low-precision match.
- `geocode_failed`: address could not be geocoded.
