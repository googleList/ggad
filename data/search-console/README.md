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

For reliable US/Hong Kong segmentation, also include the Country dimension. If the export has no country column, include `us`, `usa`, `united-states`, `hk`, or `hong-kong` in the filename.

Run:

```powershell
python scripts/prioritize_search_console.py
```

Outputs:

- `data/search-console-priorities.json`
- `reports/search-console-priorities.md`

The score ranks observed opportunities. It does not predict traffic or rankings.
