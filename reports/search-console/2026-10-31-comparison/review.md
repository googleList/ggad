# 2026-10-31 Search Console Evidence Review

## Acquisition And Periods

Fresh authorized visible UI access succeeded through the native app surface. Earlier DOM timeouts are historical, not evidence that the account remains unreadable. Downloaded two official CSV ZIPs and verified their SHA256 values against the snapshot. This is new acquisition; `comparison.json` is the subsequent offline calculation, whose `performsAccountRead: false` accurately describes the script only.

The applied absolute date fields were reopened and checked: October 22-28 versus October 15-21, and October 1-28 versus September 3-30. The local acquisition date was October 31 while PT was October 30. Through October 28 is `recent_edge_not_assumed_final` under the unchanged three-day lag. Later settled exports should confirm it; no API finalness flag was read.

| Property total | Current | Previous |
|---|---:|---:|
| Seven-day impressions | 64 | 28 |
| Seven-day clicks | 1 | 0 |
| Seven-day displayed average position | 19.7 | 33 |
| 28-day impressions | 279 | 6 |
| 28-day clicks | 1 | 1 |
| 28-day displayed average position | 50.6 | 12.7 |

These rolling windows overlap the prior snapshot by six and 27 days. They are not independent experiment results. The monthly prior baseline is tiny and partly predates this work: neither its CTR nor mixed-query average position establishes a collapse or causal success. Clicks are not visits or qualified enquiries.

## Language And Geography

Exact `谷歌代投` appears with 20 impressions, one click, 5% CTR and observed average position 3.2 in both overlapping current exports. An explicit exact-query UI filter independently showed all 20 impressions on existing `google-ads.html`; the query-filtered country table showed CN 8/1, HK 7/0, SG 3/0 and US 2/0 impressions/clicks. These are conditional query-country and query-page observations, not a simultaneous three-way/device join. No country is inferred from the Simplified script. Preserve the accepted service title and scope; sparse observations do not justify another rewrite or duplicate US-Chinese page.

All-query weekly country totals are US 13 versus 11 impressions and HK 28 versus 9, both with zero clicks. Monthly they are US 123 versus 4 and HK 83 versus 1; the current click is outside those two target markets. Independent country totals must not be attributed to the four seeds.

New watch term `谷歌广告开户` has one impression, zero clicks and reported position 102. It is not the exact seed `谷歌开户`. Its query-page-country association is **unknown**, so map it provisionally to the existing accepted setup tutorial for future investigation, not an observed landing-page winner. Exact `谷歌开户`, `谷歌排名` and `谷歌广告` are absent from these query tables, not proven zero demand. Search volume and SEO difficulty remain unknown.

## Ranked Next Actions

| Priority | Action | Evidence / Impact / Effort / Risk |
|---|---|---|
| 1 | Confirm the new window with a later settled export and inspect the setup long-tail's actual page/country if retained | One new observation; protects measurement decisions; small read-only effort; low risk. Do not repeatedly poll the same report. |
| 2 | Keep primary service and approved setup tutorial stable; keep `谷歌排名` mapped to the organic SEO pillar | One directly observed service mapping, owner-confirmed organic intent; avoids confusing paid AdRank with organic ranking. No new thin page or title test. |
| 3 | Resolve the already documented scoped HTTP/www HTTPS consolidation when owner access is available | HTTP homepage still appears in independent page export; impact conditional, no new causal claim or repeated unchanged edge probe. Do not change DNS/TLS/WAF wholesale. |
| 4 | Obtain correct GA4/qualified-enquiry evidence and independent pending article feedback when available | Visits, leads and 1,000/day goal cannot be assessed from GSC clicks; no fabricated zero, account creation or repeat approval request. |

The US audit page's 83 monthly impressions and zero clicks are mostly distant mixed queries; no immediate accepted-guide rewrite from tiny or country-unjoined data. Preserve US/HK localizations and existing Simplified cluster. llms.txt approval already recorded separately remains accepted; SEO-learning and other pending reviews do not inherit it.

## Change Scope And Limits

Only acquired data, analysis and program records change this batch. No public HTML, titles, dates, images, layout, structured data, sitemap, feed, tracking, account settings, indexing requests, edge policy or outreach changed. No new browser layout matrix is claimed for unchanged frontend. Existing quality/link/public-artifact gates and deployment checks will be recorded in `release.md`.

Raw source: `../2026-10-31-official-comparison.json`; calculation: `comparison.json`; exact query evidence: `query-scope.json`. GA4 organic sessions, enquiries, market search volume, finalness and field Core Web Vitals are unavailable, not zero. The 1,000 organic-visits/day objective remains unverified and active.
