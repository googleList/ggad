# Reproducible Search Console Export Comparison

Property: `sc-domain:shumaojs.com`
As-of PT calendar: 2026-10-31; source observed date: 2026-11-01.
No account read was performed. Reprocessed exports are not new performance observations.

## Weekly

Current: 2026-10-23 through 2026-10-29; previous: 2026-10-16 through 2026-10-22 (PT).
Archive SHA256: `8dbe465f1e06e514b80051e212e08f0a84a77de5f41a8eab5cf72f2e60bd6f3d`; freshness: recent_edge_not_assumed_final.

Previously observed UI cards; CTR below is recalculated from matching counts, not averaged across rows. CTR values are percentages; changes are percentage points. Average position is not a fixed keyword rank.
| Metric | Current | Previous | Current minus previous |
|---|---:|---:|---:|
| clicks | 1 | 0 | 1 |
| impressions | 66 | 33 | 33 |
| ctrFromCountsPercent | 1.52 | 0.00 | 1.52 |
| averagePosition | 20.80 | 24.70 | -3.90 |

Exact seeds, independent query table only. Missing rows are not filled with zeros. Exported zeros can also represent unavailable UI values; 0 / 0 is not proof of zero market demand.
| Query | Row present | Current clicks / impressions | Previous clicks / impressions | Current / previous position |
|---|---|---:|---:|---:|
| 谷歌代投 | True | 1 / 19 | 0 / 4 | 3.84 / 2.00 |
| 谷歌开户 | False | unknown | unknown | unknown |
| 谷歌排名 | False | unknown | unknown | unknown |
| 谷歌广告 | False | unknown | unknown | unknown |

Country rows cover all queries, not these seeds; device and page tables remain separate in JSON.
| Country | Current clicks / impressions | Previous clicks / impressions |
|---|---:|---:|
| US | 0 / 11 | 0 / 11 |
| HK | 0 / 30 | 0 / 10 |

Reported query rows with largest absolute impression changes, not causal wins/losses.
| Value | Current impressions | Previous impressions | Click change |
|---|---:|---:|---:|
| 谷歌代投 | 19 | 4 | 1 |
| google 廣告收費 | 4 | 0 | 0 |
| search ads evaluation form | 1 | 5 | 0 |
| google ads代运营 | 3 | 0 | 0 |
| adwords hk | 1 | 0 | 0 |

Reported page rows with largest absolute impression changes, not causal wins/losses.
| Value | Current impressions | Previous impressions | Click change |
|---|---:|---:|---:|
| https://shumaojs.com/google-ads.html | 21 | 7 | 1 |
| https://shumaojs.com/articles/meta-creative-testing.html | 7 | 0 | 0 |
| https://shumaojs.com/articles/google-ads-cost-hong-kong.html | 5 | 0 | 0 |
| https://shumaojs.com/google-ads-agency-checklist-usa.html | 2 | 7 | 0 |
| https://shumaojs.com/articles/google-ads-vs-meta-ads-guide.html | 4 | 0 | 0 |

## Monthly

Current: 2026-10-02 through 2026-10-29; previous: 2026-09-04 through 2026-10-01 (PT).
Archive SHA256: `5a0e0edde80a4fd4149f16fa0d675471c7b5e2bf1f622b93cf75022d5399d8d1`; freshness: recent_edge_not_assumed_final.

Previously observed UI cards; CTR below is recalculated from matching counts, not averaged across rows. CTR values are percentages; changes are percentage points. Average position is not a fixed keyword rank.
| Metric | Current | Previous | Current minus previous |
|---|---:|---:|---:|
| clicks | 1 | 1 | 0 |
| impressions | 281 | 15 | 266 |
| ctrFromCountsPercent | 0.36 | 6.67 | -6.31 |
| averagePosition | 48.50 | 51.10 | -2.60 |

Exact seeds, independent query table only. Missing rows are not filled with zeros. Exported zeros can also represent unavailable UI values; 0 / 0 is not proof of zero market demand.
| Query | Row present | Current clicks / impressions | Previous clicks / impressions | Current / previous position |
|---|---|---:|---:|---:|
| 谷歌代投 | True | 1 / 23 | 0 / 0 | 3.52 / unknown |
| 谷歌开户 | False | unknown | unknown | unknown |
| 谷歌排名 | False | unknown | unknown | unknown |
| 谷歌广告 | False | unknown | unknown | unknown |

Country rows cover all queries, not these seeds; device and page tables remain separate in JSON.
| Country | Current clicks / impressions | Previous clicks / impressions |
|---|---:|---:|
| US | 0 / 116 | 0 / 11 |
| HK | 0 / 86 | 1 / 3 |

Reported query rows with largest absolute impression changes, not causal wins/losses.
| Value | Current impressions | Previous impressions | Click change |
|---|---:|---:|---:|
| search ads evaluation form | 25 | 0 | 0 |
| google ads 報告 | 23 | 0 | 0 |
| 谷歌代投 | 23 | 0 | 1 |
| google ads audit | 18 | 0 | 0 |
| google 廣告收費 | 20 | 2 | 0 |

Reported page rows with largest absolute impression changes, not causal wins/losses.
| Value | Current impressions | Previous impressions | Click change |
|---|---:|---:|---:|
| https://shumaojs.com/articles/google-ads-account-audit-usa.html | 77 | 7 | 0 |
| https://shumaojs.com/google-ads.html | 29 | 0 | 1 |
| https://shumaojs.com/google-ads-agency-checklist-usa.html | 28 | 1 | 0 |
| https://shumaojs.com/articles/google-ads-cost-hong-kong.html | 28 | 2 | 0 |
| https://shumaojs.com/articles/google-ads-monthly-reporting-hong-kong.html | 27 | 1 | 0 |

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
