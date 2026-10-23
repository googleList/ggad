# Simplified Chinese Cost Guide: Editorial Brief

## Scope and Intent

- Existing URL: `https://shumaojs.com/articles/google-search-ads-cost-guide.html`.
- Category: SEM. Business context is an independent advertising consultancy, not an ecommerce storefront. Product/category optimization therefore maps to service pages and editorial categories unless the owner confirms actual products.
- Primary topic: search-ad media costs versus management fees, with qualified-lead budget arithmetic. Candidate phrases: 谷歌广告费用、谷歌代投费用、谷歌广告预算、有效询盘成本.
- Evidence: the October 23 GSC snapshot has Traditional Chinese cost queries, but no reportable Simplified target matches. Public searches on October 24 local time for 谷歌广告费用/谷歌广告代投费用 return cost explanations and service pages. This supports topic/intent, not US/HK-specific search volume or a traffic forecast. No competitor wording, images, rate card or numerical performance claims were copied.
- Reason for prioritization: a directly observed arithmetic/definition defect and visible/schema update-date mismatch on an existing Simplified guide. Fixing those is useful without Cloudflare or GA4 access; the separate account-dependent tasks remain unresolved.

## Title Candidates

1. **Selected, retained:** Google 搜索广告费用怎么算？预算、点击和服务费说明.
2. Draft only: 谷歌广告预算怎么算？从点击到有效询盘的费用拆分.
3. Draft only: 谷歌代投费用怎么比较？媒体消耗、服务费与交付清单.

The title/H1/canonical/URL are unchanged in this release. Other titles are editorial candidates, not additional near-duplicate pages.

## Revised Outline

1. Direct answer: separate media, management and one-time work; hypothetical values are not quotes or benchmarks.
2. Actual CPC and auction context; distinguish diagnostic Quality Score from auction-time quality.
3. Define raw enquiry, qualified lead and sale separately.
4. Work backwards from 20 qualified leads with 3% raw conversion and three hypothetical qualification rates; show rounding and exclusions.
5. Explain average daily budgets and the qualified scope of the 30.4/2x rules.
6. Explain delivery-based fee comparisons, implementation versus advice, account/data access and exit terms.
7. Discuss test stages, search-term review, qualified outcomes and when not to increase spend.
8. Relevant FAQs and contextual links to setup, Ad Rank, keywords, conversion tracking, budget pacing and the service page.

## Fact and Arithmetic Review

- Old text treated 20 raw enquiries at 3% as 20 qualified leads without a qualification assumption. Corrected: planned clicks = ceil(qualified target / raw conversion rate / qualification rate).
- For hypothetical CPC USD 2 and raw conversion 3%: qualification 100% requires 667 clicks / USD 1,334; 50% requires 1,334 / USD 2,668; 25% requires 2,667 / USD 5,334. No results are promised, and these are media-only scenario budgets.
- Removed an unsupported general claim that mature Western markets necessarily have higher clicks; require actual market/language/currency inputs.
- Quality Score is diagnostic, not an auction input. Do not imply a fixed cost discount per score point or that every bidding target is a hard CPC cap.
- Preserved publication day September 11. This substantive edit records the observed editorial working timestamp `2026-10-24T00:20:55+08:00`, not an exact deployment time. Display/schema, card date and the changed article/hub sitemap dates are aligned; no other article dates refreshed.

Primary sources checked:
- [Actual CPC](https://support.google.com/google-ads/answer/6297?hl=en)
- [Maximum CPC](https://support.google.com/google-ads/answer/6326?hl=en)
- [Quality Score](https://support.google.com/google-ads/answer/6167118?hl=en)
- [Budget concepts](https://support.google.com/google-ads/answer/10486536)

## Review Status

- AI-assisted factual, arithmetic, clarity, terminology, unsupported-claim and link review: completed for this correction; browser/automated evidence is stored alongside this brief.
- **Human editorial review: pending.** No person has approved this revision in the thread. Do not label it human-reviewed or use a fictional reviewer.
- Human checklist: confirm that the raw/qualified/sales definitions fit the business; identify any actual delivery/fee boundary to add; confirm that hypothetical numbers cannot be read as the company's quote; inspect thumbnail and phone layout.
- Until owner-confirmed facts are provided, keep the article general and do not add package prices, guarantees, client results, platform credentials or office claims. Factual corrections can be published without pretending the separate human step happened.

## Thumbnail and Asset Provenance

Original concept illustration made with the built-in image generation tool, not a competitor image, interface screenshot or client case. It depicts a blue calculator and staged lead sorting in teal/green/coral, with no brand badge or performance claim. The calculator's decorative glyphs are not data and must not be interpreted as an actual budget result.

Final workspace assets:
- `assets/articles/ads-budget-qualified-leads-v1.jpg`: 1200 x 675, 124,983 bytes; article/social cover.
- `assets/articles/ads-budget-qualified-leads-thumb-v1.webp`: 480 x 270, 22,366 bytes; listing/phone image.

The generated original remains under the tool's generated-images directory. Workspace assets are encoding/size-optimized derivatives with the same illustrated content. Consumer references use the workspace files, with dimensions and contextual alt text.

Generation prompt:

> Create one original 16:9 landscape editorial thumbnail for a Simplified Chinese Google Ads budgeting article about the difference between raw enquiries and qualified leads. Premium, clear, tactile editorial illustration on a pure white studio surface: a cobalt-blue desktop calculator next to a neat budget worksheet with unlabeled rows, and a transparent three-stage sorting tray/funnel containing many small blue tiles at the top, fewer teal tiles in the middle and a few green check-mark tiles at the bottom. A small coral-red rejection tray to the side makes lead qualification visually understandable. Restrained cobalt blue, teal, lime green and coral accents; realistic soft shadows and crisp physical material detail. Close, balanced composition filling the image so it remains legible as a small blog card. No people, no office photograph, no marketing claims, no text, no letters, no numbers, no brand logos, no Google interface, no charts claiming real results, no gradients, no decorative orbs, no border, no watermark. This is an illustrative concept, not a screenshot or client case study.

## Next Topic Candidates, Not Yet Published

| Intent | Existing Destination | Next Research / Human Input |
| --- | --- | --- |
| 谷歌代投 / 谷歌广告代投 | `/google-ads.html` | Audit actual service deliverables against the owner-approved scope before changing commercial claims; do not invent fees or guarantees |
| 谷歌开户 / 谷歌广告开户 | `/articles/google-ads-basics.html` | Observe a newer crawl after October 20; review actual customer setup questions before expanding |
| 谷歌排名 / 谷歌广告排名 | `/articles/google-search-ads-guide.html` | Distinguish natural-search and paid-ad intent using real query evidence; do not promise first place |
| SEM article category | `/articles.html` | Preserve the three-column card/category/pagination experience and all English/HK articles; only update the relevant image/date/description in this batch |

All volumes and conversion outcomes remain unknown. No paid planner, third-party outreach or profile submission was performed.
