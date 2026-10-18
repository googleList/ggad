# Search Console exports

Place Google Search Console CSV exports in this directory. The analyzer accepts English, Simplified Chinese, and Traditional Chinese column labels.

Raw CSV files are ignored by Git because query and page performance can be commercially sensitive. Keep them local; commit only a reviewed aggregate report when appropriate.

Required metrics:

- Clicks
- Impressions
- CTR
- Position

Include at least one dimension:

- Query
- Page

Include the Country dimension to compare user locations separately from query language. The analyzer recognizes US, Hong Kong, China, and other/unassigned rows; Simplified Chinese target queries are prioritized across all countries. If the export has no country column, include `us`, `usa`, `united-states`, `hk`, or `hong-kong` in the filename.

Primary Simplified Chinese query themes:

- 谷歌代投
- 谷歌开户
- 谷歌排名
- 谷歌广告

The report shows matching queries first, then retains the full multilingual query list. If a target query is absent, that means it was not present in the supplied export, not that its search demand is zero.

Run:

```powershell
python scripts/prioritize_search_console.py
```

Outputs:

- `data/search-console-priorities.json`
- `reports/search-console-priorities.md`

The score ranks observed opportunities. It does not predict traffic or rankings.

For initial property verification, sitemap submission, and priority URL inspection, follow `reports/search-console-indexing-runbook-2026-09-30.md`. Confirm that the selected property is `sc-domain:shumaojs.com`; do not upload this site's sitemap under another domain property.
