# Platform Tactics

Use this file when deciding how to collect rental data from Chinese platforms.

## Beike / Lianjia / 贝壳 / 链家

- Prefer public web listing pages and share links.
- Useful fields: rent, title, district, business area, community, layout, area, floor, orientation, subway distance, maintenance status, listing ID.
- Watch for: agency fees, duplicate listings across agents, "近地铁" without walking time, photos reused from similar units.

## Ziroom / 自如

- Prefer official share pages and copied listing details.
- Useful fields: product type, room type, rent, service fee, deposit/payment, subway, floor, elevator, move-in date, shared roommates if shared rental.
- Watch for: service fee, cleaning/repair terms, shared-apartment roommate constraints, short lease premium.

## Anjuke / 58 / 安居客 / 58同城

- Prefer public listing pages and user-provided links or text.
- Useful fields: rent, landlord/agent marker, layout, area, address/community, payment terms, contact notes.
- Watch for: bait listings, duplicate posts, vague address, "个人房源" credibility, photos that do not match title.

## Douban Groups / 豆瓣租房小组

- Prefer user-provided posts, public pages, screenshots, or copied text.
- Useful fields: poster identity, sublet vs landlord vs agent, move-in date, lease end date, roommate requirements, contact method, photos.
- Watch for: stale posts, missing exact location, scams requiring deposits before viewing, gender/occupation restrictions.

## Xiaohongshu / 小红书

- Prefer user-provided note links, screenshots, or copied text.
- Useful fields: rough area, commute route, rent, photo evidence, poster comments, warnings.
- Watch for: content marketing, soft ads, incomplete addresses, outdated comment info.

## Xianyu / 闲鱼

- Prefer user-provided item links/screenshots.
- Useful fields: sublet reason, lease transfer terms, deposit transfer, landlord approval, remaining lease, utilities.
- Watch for: deposit scams, unverifiable identity, refusal to view in person, pressure to pay quickly.

## WeChat / Mini Programs / 微信 / 小程序

- Use only user-provided screenshots, exported pages, copied text, or links the user can access.
- Do not scrape private chats or group member data.
- Useful fields: post time, poster role, address, rent, lease dates, contact constraints.

## App-Only Content

If content is visible only inside a mobile app:

1. Ask the user to share the listing link if the app supports sharing.
2. If no link exists, ask for screenshots or copied text.
3. Extract from the provided evidence.
4. Do not attempt private API capture, packet inspection, device fingerprint bypass, or emulator-based scraping.
