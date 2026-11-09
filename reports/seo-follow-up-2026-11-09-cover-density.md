# Priority article cover density maintenance

## Evidence and decision

Baseline revision: 39077c0873fcb186f96e610c77cd6115d95bb2f8. Fresh fetch found no divergence before edits. Latest GSC evidence remains the November9 partial UI read through November7, not a complete query/country/page or28day export. GA4 Google organic visits and field CWV remain unknown. Do not infer keyword volume, rank changes or the1000dailyvisit target from this maintenance.

Following the previously verified setup-guide defect, checked five existing Simplified guides: keyword grouping, conversion tracking, landing-page checks, paid AdRank and SEO titles. Live baseline390CSSpx/DPR2 loaded480pixel artwork for340CSSpx covers, requiring680pixels; coverage0.706 for all five. Actual image bytes decoded with Sharp, not density-corrected naturalWidth. Baseline acquired2026-11-09T08:26:32.869Z, source reports/performance/2026-11-09-cover-density/baseline/browser.json.

Retained480w mobile artwork and added the already-existing1200w image as a candidate with sizes. Only five source srcset/sizes lines changed; no image creation/edit, new content, article title/body/alt/date/schema/canonical/listing/RSS/sitemap change. Existing human approvals stay scoped and unchanged. This technical repair needs no new business claim approval. Organic 谷歌排名 remains separate from paid placement; no service/localization deletion.

Browser selection reference: [MDN picture/srcset/sizes](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/picture#the_sizes_attribute). This is a verified pixel-coverage repair, not evidence of faster loading or better rankings. At390/DPR2, existing large image bodies are71109-97305bytes rather than9070-16030byte small versions; ordinary390/DPR1 keeps the original small files. There is no claim of page-wide byte savings or improved field LCP/INP/CLS.

## Verification

Local25cases finished2026-11-09T08:27:02.323Z: each page1440/DPR1,390/DPR1,390/DPR2,320/DPR2 and390/DPR2/noJS. Image decoded,16:9, CSS ready, canonical correct, no pageerrors/overflow;1200px now covers340CSSpx/DPR2 and276CSSpx/DPR2. Five semantic HTML hashes match public baseline after excluding only picture source srcset/sizes, whitespace-only nodes and the precisely identified Cloudflare edge beacon. The first hash comparison caught that public beacon, which is not repository source; no other scripts/content ignored. Representative desktop/mobile screenshots visually inspected, framing/text correct. Delayed stylesheet noJS case retains load/CSS-readiness gating.

Initial system Chrome launch exited before a page opened; tests succeeded with installed clean Playwright Chromium1243, without private browser profiles or account access. This is not a site failure or a GSC recovery attempt.

237local tests pass with one Windows permission skip;68HTML/66sitemap zeroSEOerrors/warnings; structured data, content policy, performance budgets, discovery coverage, current48article RSS and JS syntax pass. Scoped links66pages/0orphans/1historicalsingle-inlink/maxdepth3.180publicfiles staged before release marker; research/reports excluded. CI and public verification must be recorded only after release succeeds.

## Next priorities

1. Obtain already-requested official7/28daycomparison ZIPs and current query/page/country detail; no repeated password/export request or partial data passed as complete. Keep72/66impressions and0/1clicks as sparse weekly aggregates only.
2. Obtain exclusion example URLs before diagnosing current intended pages; do not restore old storefront/account pages, bulk301home, or request validation without evidence.
3. Retain reviewed content and dates, wait independent pending human replies. No further responsive-image expansion without a measured defect; no new similar thin pages or title churn from small aggregate counts.

## Release result

Source27c8873fa94ba80063965d27ee64d2027a36600f pushed non-force to main. Pages42586220471/job129056586476 success: all237Ubuntu testsOK, validation gates passed,181publicfiles including marker. Full live40character marker matched2026-11-09T08:30:07.6241297Z; repository report URL returned404 as intended.

Production25cases finished2026-11-09T08:30:03.527Z, reports/performance/2026-11-09-cover-density/production/browser.json: zeroerrors/overflow, correct16:9/decodedcoverage/CSS/canonical, five protected semanticHTML hashes match baseline in all cases. Ordinary390/DPR1 keeps480px,390/DPR2 selects1200px. These checks establish deployed image behavior only, not fresh search/GA4/fieldCWV evidence. Final records-only followup can be verified externally without a recursive evidence-commit loop. Local helper server stopped; no running test sessions remain.

No Ads/GA4/Cloudflare setting, form submission, index request, outbound message, directory profile or link purchase occurred.
