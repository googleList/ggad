# Simplified Google Ads Fee Comparison Utility

## Selection And Evidence

Previous turn was progress: US/HK handover guides deployed asdad666e with both independent owner questions pending. Do not rewrite those pages or repeat the questions. Latest main/live baseline43d52f3 fetched and observed before this batch. No new GSC read or repeated same-window export.

Reviewed both existing US/HK pricing guides and the Simplified cost guide. They explain fee types; the existing budget pacing calculator allocates media over days and cannot compare service proposals. Select an embedded fee comparison in the existing Simplified cost guide, rather than duplicating an article or rewriting accepted service/setup content. Current priority language remains Simplified; USD/HKD arithmetic supports users planning US/HK campaigns without inferring their location from language.

Public October31 topic searches returned management-fee/proposal comparison question types and official transparency/budget guidance. This verifies a task shape, not localized Google top-ten positions or demand scale. No competitor figures, prose, screenshots or rates adopted. Latest historical GSC throughOctober28 still does not establish exact tool-query volume or conversion opportunity. Search volume, SEO difficulty, tool usage and enquiries unknown.

Priority rationale: impact is usable scope-comparison support for prospective service buyers; evidence is a concrete functional gap; effort is one isolated script/style and existing-page section; risk is arithmetic-only with explicit exclusions, no quote submission or new business promise. More primary-title churn on sparse queries has weaker evidence.

## Marketing Headlines And Outline

Candidates: (1) Google 搜索广告费用怎么算？预算、点击和服务费说明 (retain existing title/H1); (2) 谷歌代投报价怎么比？月费、比例与设置费核对; (3) 谷歌广告服务费怎么算？两份假设方案的同口径比较.

These are editorial alternatives, not tested winners. Preserve URL, SEM category, September11 publication, existing cover and previous October24 explanations/examples/service CTA. Only append a native linked section, align descriptions/card/actual modification/sitemap/feed and add a regular-tools directory link.

Outline: distinguish quoted fee base from media forecast; same media amount/currency/whole-month assumption; two hypothetical offers and three fee models; minimum monthly fee versus percentage/base-plus-percentage; setup once; first-month versus term/service totals; exact rounding and exclusions; manual example when JS unavailable; transparent fees and appropriate next steps.

## Facts, Arithmetic And Boundaries

Official source actually read October31: https://support.google.com/adspolicy/answer/6086450?hl=zh-Hans . Google third-party policy calls for management-fee disclosure and separating Google advertising cost from third-party fees. Original summarized policy sentence only, not a compliance certificate, fixed-price promise, legal determination or actual invoice audit. Other source searches at https://support.google.com/google-ads/answer/2375454?hl=zh-Hans confirm budget is not necessarily actual spend; existing daily-limit discussion remains unchanged. Did not adopt the outdated average-position glossary from the advertiser guide or competitor benchmark/tax statements.

Formula implemented in integer cents with BigInt: percentage component rounded half-up once each month, fee=max(base+percentage,minimum) for applicable models; fixed mode ignores percentage/minimum, percentage mode ignores base. Term total=(same entered media + monthly fee)*whole months + setup once. Currency changes relabel all amounts, not FX. Unknown/empty is invalid, explicit zero valid. Limits are tool input bounds, not Google policies or service terms.

Default independent hand calculation: media3000/month,3months; A fixed500/setup0 => monthly500, first3500, services1500, term10500. B10%/minimum400/setup300 => monthly400, first3700, services1500, term10500. Hybrid200+5%/minimum400/setup100 => monthly400, services1300, term10300. Half-cent case:0.05media *10%=0.005 rounds to0.01 monthly;3months service0.03 and media+service0.18. Values hypothetical, not market rates or this company's quotes.

Excludes taxes, FX, surcharges, subscriptions, tiers, fee caps, proration, termination fees and refunds. Actual fee base and terms must be confirmed in writing. Cheaper amount is not better service or guaranteed outcomes. No ROI/ranking/lead prediction, payment, account connection, form submission or new tracking. Script does not send/persist quote inputs; this limited code claim is not a universal claim that hosting has no network telemetry.

## Thumbnail And Human Review

Retain previously generated original `assets/articles/ads-budget-qualified-leads-v1.jpg` and480x270WebP thumbnail with current alt/share metadata. No new image generated or invented illustration provenance this batch; stable existing image remains appropriate to fee/lead-budget guide. No repeated new-image cost or visual churn.

AI-assisted factual, calculation, boundary and accessibility checks documented in tests. Prior cost-article question remains its own pending scope. New independent owner question should review only this appended comparison/formula/example/exclusion scope after verified production; no inherited human approval, published actual pricing, credentials, cases or service commitment. Source and test validation are not owner acceptance.

## Verification Plan

Four focused Python tests invoke actual Node arithmetic assertions and validate honest inert source state, no input transmission/persistence API, scope/date/feed/discovery. Browser desktop/tablet/mobile, default/hybrid, invalid/zero/fractional months, currency/reset/Enter, JS-off and script-blocked fallback. Existing full cost, hub and tools navigation checks plus site/link/performance/public-artifact gates. Commit/push, verify actual CI/live marker/production utility, then record results and deliver own review question. No 1,000 visits/day achievement or causal traffic claim.
