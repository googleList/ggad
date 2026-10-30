# Reproducible Official Export Comparison

This is a data-processing improvement, not a new Search Console read. Source: ../2026-10-29-official-comparison.json and the unchanged official weekly/monthly ZIP archives in ../2026-10-29-exports/. Four absolute date fields were verified in the visible UI on October29; relative CSV labels alone cannot supply those dates. Existing llms release3b0189ae9d6f856604ebd562a1081c1dabda9143 was the previous verified progress; its article, directory, date and image remain unchanged in this batch.

## Run
From repository root:

```powershell
python -B scripts/compare_search_console_exports.py --snapshot reports/search-console/2026-10-29-official-comparison.json --as-of-date 2026-10-30 --json-output reports/search-console/2026-10-30-reproducible-comparison/comparison.json --report-output reports/search-console/2026-10-30-reproducible-comparison/comparison.md
```

The as-of date is explicitly a PT calendar reference for freshness, not a new data-through date. Default expected lag is three days, a conservative reporting policy, not API-finalness proof. October27 matches this policy on October30. If a later as-of date makes the same archive older, its actual dates still remain October27 and the gate asks for a newer verified window; it never refreshes observations by changing a timestamp.

For the next actual export, save a source record with property, observedDate, weekly/monthly four verified absolute dates, archive paths/SHA256 and the separately read visible property cards. The existing snapshot documents this shape; its optional files arrays are checked byte-decoded/CSV-row-equivalent against the archives. Do not invent dates or card metrics. This version intentionally supports UTF-8 Simplified Chinese unfiltered comparison exports with query/page/country/device tables, not arbitrary filtered/API/English export formats. Unsupported/ambiguous data fails rather than guesses. `--archive-root` can point at another controlled source directory; paths cannot escape it. `--property` must explicitly match the intended property.

## Duplicate-evidence Guard
An optional `--prior-report` supplies the previous output from this tool for the same property. The fingerprint covers actual archive hashes, verified periods, filters and observed UI metrics, not report-generation date or machine paths. Same evidence gives inputEvidenceChangedSinceBaseline=false. An absent baseline remains null, not evidence of a new account read. Changed input only supports investigation, not automatic content publishing.

Example replay into a different output location:

```powershell
python -B scripts/compare_search_console_exports.py --snapshot reports/search-console/2026-10-29-official-comparison.json --as-of-date 2026-10-30 --prior-report reports/search-console/2026-10-30-reproducible-comparison/comparison.json --json-output C:/Users/Administrator/AppData/Local/Temp/shumao-gsc-replay-20261030/comparison.json --report-output C:/Users/Administrator/AppData/Local/Temp/shumao-gsc-replay-20261030/comparison.md
```

## Correctness Boundaries
- Weekly and monthly windows overlap each other and are never added. Within each comparison, periods must be equal-length, adjacent and non-overlapping, and relative labels must agree with the verified dates.
- ZIP hashes, member paths/size, row widths, duplicate tables/labels, required metrics, percent units and counts are validated before output. Files are read in memory, never extracted. Wrong site, ambiguous periods and mismatched observations stop the operation; validation failure leaves previous outputs intact.
- Zero-impression exported position0 stays in reportedAveragePosition but analytical averagePosition and CTR become null. Google notes that unavailable UI values can export as zeros. A present zero-valued row is different from a missing row, and neither proves zero market demand.
- Missing exact seeds remain rowPresent=false/metrics=null. No substring mapping of paid谷歌广告排名 into genericorganic谷歌排名, no country inference from query language and no country hints from filenames.
- Query/page/country/device tables remain separate. US/HK country rows cover all queries in this unfiltered export; no new query+page+country+device observation is manufactured. Prior UI joint-filter observations stay in their original dated snapshot.
- UI card metrics and reported-row totals are different sources/aggregation scopes. The monthly query table's prior zero reported clicks does not replace the UI property's prior1click/3impressions. CTR is derived from matching counts, never an average of row percentages; exported precision is retained separately. No table averages are promoted to site position.
- CTR levels are percentages and CTR changes are percentage points, not relative percentage growth. Position changes are current minus previous within that source scope; they do not represent fixed-query causal ranking gains.
- Changes are reported measurements, not causal wins/losses. Small/mixed/tiny prior baselines do not authorize retitling pages, deleting localizations or claiming a release effect. The existing100-impression guard is editorial triage, not significance or automatic editing permission.
- Raw dimension values stay intact in JSON, including multiline operator queries. Markdown escapes line breaks, pipes and HTML. Reports and raw exports must still be reviewed for personal information before committing to a public repository. Excluded from the public website does not make repository data private.

## Actual Evidence and Next Step
The original source remains throughOctober27, observedOctober29. Expected reconstruction: weekly property48/32impressions,1/0clicks; monthly264/3and1/1. Exact谷歌代投13impressions/1click, not search volume; its exported prior0impressions gives undefined priorposition, not rank0. Three other exactseed rows are absent, not0marketdemand. Query sums weekly33/22impressions andmonthly217/0 are explicitly not property totals. All-query countries retain US10/15 andHK19/10weekly impressions, no new direct joint observation. No new GA4 sessions, enquiries, fieldCWV or1000dailyorganic goal outcome.

Next: preserve accepted primary pages/current newly revised content, use a genuinely later verified export when available, and obtain a correctly identified GA4 resource before measuring organic visits. No new cron is added merely to reprocess old ZIPs as fresh data. Existing GitHub CI automatically runs the new unit tests; script/report changes are not website body changes. No account login, subscription purchase, OAuth setup, tag, Ads action, indexing request, edge rule, external profile or outreach performed.

## Official Methodology
- https://support.google.com/webmasters/answer/7576553?hl=en explains CTR, dimension aggregation and unavailable-to-zero export behavior.
- https://support.google.com/webmasters/answer/17010575 explains property/table differences, privacy/truncation, typical lag and PT report dates.
- https://support.google.com/webmasters/answer/17011259 explains query omissions and independent country/device/page dimensions.

The optional GSC Wizard connection remains blocked by its last actual subscription response; no changed access evidence, so it was not retried or purchased. No private UI control tool is currently callable; no shell/CDP/browser-profile bypass is attempted. This adapter does not claim to replace authenticated collection.

## Local Validation
17new focused tests pass; full207testsOK withoneWindowspermissionskip. Existing67HTML/65sitemap0errors-warnings, structureddata/policy/performance/discovery/47RSS/JS gates pass. Scoped65pagegraph0orphans/maxdepth3, historicalsingleinlink learning page retained. Staging172publicfiles beforemarker, no newreport/script copied. Gitdiff acrossallpublicsourcepaths is empty andno untrackedassets/articles exist, so no UI/bodychange or newbrowsermatrix is claimed thisbatch; priorverifiedllms/trust matrices remain historical. OriginalZIPs are already trackedforUbuntuCI fixtures. Same-inputrealCLI replay at2026-10-30T11:04:37.564Z givesfalsechangedflag, identicalwindows, no_new_input_evidence; actualdatathroughOctober27 unchanged. See replay-check.json. SourceCI/publiccontent/version verification next.
