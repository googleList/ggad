# Official Search Console Exports

Downloaded through the owner-authorized visible Search Console interface on 2026-10-29. Original archives retained unchanged; parsed with standard zipfile/csv APIs. No authentication material, account email or hidden application state is part of these exports.

| Archive | Window verified in reopened date UI | SHA256 |
|---|---|---|
| weekly.zip | 2026-10-21–27 versus 2026-10-14–20 | 73424759eafbac5dd64548225849c71759fd4ddd3cbb9466dbb0005e9e797991 |
| monthly.zip | 2026-09-30–10-27 versus 2026-09-02–29 | b0c7025229dad53b0a6eaafa4ac586f73172cbfb923359643bef6eab4317baf9 |

CSV filters contain relative labels, not these absolute dates. Absolute dates come from the actually reopened four UI fields; raw CSV row precision can exceed rounded UI cards. No API finalness is claimed. Full raw rows are preserved, including zero-impression prior-only rows and operator-shaped queries. Country, page and query tables must not be joined as if they were joint-filter data.

Generated priority reports select just one comparison period. Run separately for one non-overlapping date window:

```powershell
python -B scripts/prioritize_search_console.py "reports/search-console/2026-10-29-exports/weekly/查询数.csv" --comparison-period current --json-output reports/search-console/2026-10-29-exports/weekly-current-priorities.json --report-output reports/search-console/2026-10-29-exports/weekly-current-priorities.md
```

Use previous for the separate prior-period analysis. Never sum weekly and monthly observations, use missing query rows as zero market demand, infer country from language, or treat the heuristic score as a traffic forecast. The query-only file supplies no page/country; the tool honestly leaves them unassigned. Actual service-page mapping and query-country UI observations are separately documented in ../2026-10-29-official-comparison.json and ../seo-follow-up references.

These are research/reporting assets, excluded from the public website artifact. Original downloads remain in Downloads. No page body, public date, account, robots, CDN, index submission, GA4 or outreach settings changed in this data batch.
