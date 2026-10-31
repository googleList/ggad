# Reproducible Search Console Export Comparison

Property: `sc-domain:shumaojs.com`
As-of PT calendar: 2026-10-30; source observed date: 2026-10-31.
No account read was performed. Reprocessed exports are not new performance observations.

## Weekly

Current: 2026-10-22 through 2026-10-28; previous: 2026-10-15 through 2026-10-21 (PT).
Archive SHA256: `cd81cd751a25e0d7ca44ec89a7ce42d9b7cf1213029872f424441586935f5b89`; freshness: recent_edge_not_assumed_final.

Previously observed UI cards; CTR below is recalculated from matching counts, not averaged across rows. CTR values are percentages; changes are percentage points. Average position is not a fixed keyword rank.
| Metric | Current | Previous | Current minus previous |
|---|---:|---:|---:|
| clicks | 1 | 0 | 1 |
| impressions | 64 | 28 | 36 |
| ctrFromCountsPercent | 1.56 | 0.00 | 1.56 |
| averagePosition | 19.70 | 33.00 | -13.30 |

Exact seeds, independent query table only. Missing rows are not filled with zeros. Exported zeros can also represent unavailable UI values; 0 / 0 is not proof of zero market demand.
| Query | Row present | Current clicks / impressions | Previous clicks / impressions | Current / previous position |
|---|---|---:|---:|---:|
| 谷歌代投 | True | 1 / 20 | 0 / 0 | 3.20 / unknown |
| 谷歌开户 | False | unknown | unknown | unknown |
| 谷歌排名 | False | unknown | unknown | unknown |
| 谷歌广告 | False | unknown | unknown | unknown |

Country rows cover all queries, not these seeds; device and page tables remain separate in JSON.
| Country | Current clicks / impressions | Previous clicks / impressions |
|---|---:|---:|
| US | 0 / 13 | 0 / 11 |
| HK | 0 / 28 | 0 / 9 |

Reported query rows with largest absolute impression changes, not causal wins/losses.
| Value | Current impressions | Previous impressions | Click change |
|---|---:|---:|---:|
| 谷歌代投 | 20 | 0 | 1 |
| search ads evaluation form | 1 | 6 | 0 |
| google ads 報告 | 7 | 4 | 0 |
| google ads代运营 | 3 | 0 | 0 |
| google 廣告收費 | 3 | 0 | 0 |

Reported page rows with largest absolute impression changes, not causal wins/losses.
| Value | Current impressions | Previous impressions | Click change |
|---|---:|---:|---:|
| https://shumaojs.com/google-ads.html | 21 | 3 | 1 |
| https://shumaojs.com/articles/google-ads-monthly-reporting-hong-kong.html | 11 | 4 | 0 |
| https://shumaojs.com/articles/meta-creative-testing.html | 6 | 0 | 0 |
| https://shumaojs.com/articles.html | 4 | 0 | 0 |
| https://shumaojs.com/articles/google-ads-landing-page-checklist-hong-kong.html | 5 | 1 | 0 |

## Monthly

Current: 2026-10-01 through 2026-10-28; previous: 2026-09-03 through 2026-09-30 (PT).
Archive SHA256: `968d27e0c2514527e51f8e730360c5f68aa2c6c3853e77de0f822785f367f803`; freshness: recent_edge_not_assumed_final.

Previously observed UI cards; CTR below is recalculated from matching counts, not averaged across rows. CTR values are percentages; changes are percentage points. Average position is not a fixed keyword rank.
| Metric | Current | Previous | Current minus previous |
|---|---:|---:|---:|
| clicks | 1 | 1 | 0 |
| impressions | 279 | 6 | 273 |
| ctrFromCountsPercent | 0.36 | 16.67 | -16.31 |
| averagePosition | 50.60 | 12.70 | 37.90 |

Exact seeds, independent query table only. Missing rows are not filled with zeros. Exported zeros can also represent unavailable UI values; 0 / 0 is not proof of zero market demand.
| Query | Row present | Current clicks / impressions | Previous clicks / impressions | Current / previous position |
|---|---|---:|---:|---:|
| 谷歌代投 | True | 1 / 20 | 0 / 0 | 3.20 / unknown |
| 谷歌开户 | False | unknown | unknown | unknown |
| 谷歌排名 | False | unknown | unknown | unknown |
| 谷歌广告 | False | unknown | unknown | unknown |

Country rows cover all queries, not these seeds; device and page tables remain separate in JSON.
| Country | Current clicks / impressions | Previous clicks / impressions |
|---|---:|---:|
| US | 0 / 123 | 0 / 4 |
| HK | 0 / 83 | 1 / 1 |

Reported query rows with largest absolute impression changes, not causal wins/losses.
| Value | Current impressions | Previous impressions | Click change |
|---|---:|---:|---:|
| search ads evaluation form | 25 | 0 | 0 |
| google ads 報告 | 22 | 0 | 0 |
| google 廣告收費 | 21 | 0 | 0 |
| 谷歌代投 | 20 | 0 | 1 |
| google ads audit | 18 | 0 | 0 |

Reported page rows with largest absolute impression changes, not causal wins/losses.
| Value | Current impressions | Previous impressions | Click change |
|---|---:|---:|---:|
| https://shumaojs.com/articles/google-ads-account-audit-usa.html | 83 | 1 | 0 |
| https://shumaojs.com/articles/google-ads-cost-hong-kong.html | 28 | 0 | 0 |
| https://shumaojs.com/google-ads-agency-checklist-usa.html | 28 | 1 | 0 |
| https://shumaojs.com/articles/google-ads-monthly-reporting-hong-kong.html | 26 | 1 | 0 |
| https://shumaojs.com/google-ads.html | 25 | 0 | 1 |

## Editorial Gate

Action: `verify_newer_window_first`. Input evidence changed since supplied baseline: True.
The impression guard is editorial triage, not statistical significance or automatic editing permission.

## Limits

- Existing exports are reprocessed, not a new Google account read. A new report timestamp does not advance the data period.
- Separate weekly and monthly windows overlap; never add them together or join the independent dimension tables.
- Missing rows remain absent/null, not zero demand. Exported zeros can also represent unavailable UI values; zero-impression CTR/position are undefined, not rank zero.
- Property/UI totals differ from reported-row sums through aggregation, privacy and truncation; no forced reconciliation or query-country attribution.
- As-of date and lag policy use the PT report calendar, not the machine's timezone. Lag matching does not prove complete/final API data.
- Clicks are not sessions, customers or enquiries; small samples, mixed queries and a tiny prior baseline do not establish causal growth or a title-test winner.

Method sources: [Google documentation 1](https://support.google.com/webmasters/answer/7576553?hl=en), [Google documentation 2](https://support.google.com/webmasters/answer/17010575), [Google documentation 3](https://support.google.com/webmasters/answer/17011259)
