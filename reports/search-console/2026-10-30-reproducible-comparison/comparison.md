# Reproducible Search Console Export Comparison

Property: `sc-domain:shumaojs.com`
As-of PT calendar: 2026-10-30; source observed date: 2026-10-29.
No account read was performed. Reprocessed exports are not new performance observations.

## Weekly

Current: 2026-10-21 through 2026-10-27; previous: 2026-10-14 through 2026-10-20 (PT).
Archive SHA256: `73424759eafbac5dd64548225849c71759fd4ddd3cbb9466dbb0005e9e797991`; freshness: matches_lag_policy.

Previously observed UI cards; CTR below is recalculated from matching counts, not averaged across rows. CTR values are percentages; changes are percentage points. Average position is not a fixed keyword rank.
| Metric | Current | Previous | Current minus previous |
|---|---:|---:|---:|
| clicks | 1 | 0 | 1 |
| impressions | 48 | 32 | 16 |
| ctrFromCountsPercent | 2.08 | 0.00 | 2.08 |
| averagePosition | 20.90 | 37.50 | -16.60 |

Exact seeds, independent query table only. Missing rows are not filled with zeros. Exported zeros can also represent unavailable UI values; 0 / 0 is not proof of zero market demand.
| Query | Row present | Current clicks / impressions | Previous clicks / impressions | Current / previous position |
|---|---|---:|---:|---:|
| 谷歌代投 | True | 1 / 13 | 0 / 0 | 3.54 / unknown |
| 谷歌开户 | False | unknown | unknown | unknown |
| 谷歌排名 | False | unknown | unknown | unknown |
| 谷歌广告 | False | unknown | unknown | unknown |

Country rows cover all queries, not these seeds; device and page tables remain separate in JSON.
| Country | Current clicks / impressions | Previous clicks / impressions |
|---|---:|---:|
| US | 0 / 10 | 0 / 15 |
| HK | 0 / 19 | 0 / 10 |

Reported query rows with largest absolute impression changes, not causal wins/losses.
| Value | Current impressions | Previous impressions | Click change |
|---|---:|---:|---:|
| 谷歌代投 | 13 | 0 | 1 |
| search ads evaluation form | 1 | 8 | 0 |
| google ads management cost | 0 | 3 | 0 |
| google ads 報告 | 7 | 4 | 0 |
| google ads代运营 | 3 | 0 | 0 |

Reported page rows with largest absolute impression changes, not causal wins/losses.
| Value | Current impressions | Previous impressions | Click change |
|---|---:|---:|---:|
| https://shumaojs.com/google-ads.html | 15 | 2 | 1 |
| https://shumaojs.com/articles.html | 4 | 0 | 0 |
| https://shumaojs.com/articles/google-ads-monthly-reporting-hong-kong.html | 8 | 4 | 0 |
| https://shumaojs.com/google-ads-agency-checklist-usa.html | 4 | 8 | 0 |
| https://shumaojs.com/articles/google-ads-monthly-reporting-usa.html | 3 | 0 | 0 |

## Monthly

Current: 2026-09-30 through 2026-10-27; previous: 2026-09-02 through 2026-09-29 (PT).
Archive SHA256: `b0c7025229dad53b0a6eaafa4ac586f73172cbfb923359643bef6eab4317baf9`; freshness: matches_lag_policy.

Previously observed UI cards; CTR below is recalculated from matching counts, not averaged across rows. CTR values are percentages; changes are percentage points. Average position is not a fixed keyword rank.
| Metric | Current | Previous | Current minus previous |
|---|---:|---:|---:|
| clicks | 1 | 1 | 0 |
| impressions | 264 | 3 | 261 |
| ctrFromCountsPercent | 0.38 | 33.33 | -32.95 |
| averagePosition | 52.70 | 2.30 | 50.40 |

Exact seeds, independent query table only. Missing rows are not filled with zeros. Exported zeros can also represent unavailable UI values; 0 / 0 is not proof of zero market demand.
| Query | Row present | Current clicks / impressions | Previous clicks / impressions | Current / previous position |
|---|---|---:|---:|---:|
| 谷歌代投 | True | 1 / 13 | 0 / 0 | 3.54 / unknown |
| 谷歌开户 | False | unknown | unknown | unknown |
| 谷歌排名 | False | unknown | unknown | unknown |
| 谷歌广告 | False | unknown | unknown | unknown |

Country rows cover all queries, not these seeds; device and page tables remain separate in JSON.
| Country | Current clicks / impressions | Previous clicks / impressions |
|---|---:|---:|
| US | 0 / 123 | 0 / 1 |
| HK | 0 / 73 | 1 / 1 |

Reported query rows with largest absolute impression changes, not causal wins/losses.
| Value | Current impressions | Previous impressions | Click change |
|---|---:|---:|---:|
| search ads evaluation form | 25 | 0 | 0 |
| google ads 報告 | 21 | 0 | 0 |
| google 廣告收費 | 19 | 0 | 0 |
| google ads audit | 18 | 0 | 0 |
| google ads audit checklist | 14 | 0 | 0 |

Reported page rows with largest absolute impression changes, not causal wins/losses.
| Value | Current impressions | Previous impressions | Click change |
|---|---:|---:|---:|
| https://shumaojs.com/articles/google-ads-account-audit-usa.html | 84 | 0 | 0 |
| https://shumaojs.com/google-ads-agency-checklist-usa.html | 29 | 0 | 0 |
| https://shumaojs.com/articles/google-ads-cost-hong-kong.html | 26 | 0 | 0 |
| https://shumaojs.com/articles/google-ads-management-cost-usa.html | 24 | 0 | 0 |
| https://shumaojs.com/articles/google-ads-monthly-reporting-hong-kong.html | 23 | 0 | 0 |

## Editorial Gate

Action: `observe_only_small_or_missing_seed_rows`. Input evidence changed since supplied baseline: None.
The impression guard is editorial triage, not statistical significance or automatic editing permission.

## Limits

- Existing exports are reprocessed, not a new Google account read. A new report timestamp does not advance the data period.
- Separate weekly and monthly windows overlap; never add them together or join the independent dimension tables.
- Missing rows remain absent/null, not zero demand. Exported zeros can also represent unavailable UI values; zero-impression CTR/position are undefined, not rank zero.
- Property/UI totals differ from reported-row sums through aggregation, privacy and truncation; no forced reconciliation or query-country attribution.
- As-of date and lag policy use the PT report calendar, not the machine's timezone. Lag matching does not prove complete/final API data.
- Clicks are not sessions, customers or enquiries; small samples, mixed queries and a tiny prior baseline do not establish causal growth or a title-test winner.

Method sources: [Google documentation 1](https://support.google.com/webmasters/answer/7576553?hl=en), [Google documentation 2](https://support.google.com/webmasters/answer/17010575), [Google documentation 3](https://support.google.com/webmasters/answer/17011259)
