# Search Console indexing runbook

## Current evidence

- Public searches for `site:shumaojs.com`, `site:shumaojs.com Google Ads`, `site:shumaojs.com 香港 Google Ads`, and `site:shumaojs.com/articles shumao` returned no visible results on September 30, 2026.
- This is a discovery signal, not a substitute for the Search Console Page indexing report.
- `https://shumaojs.com/robots.txt` returns HTTP 200, allows crawling, and declares `https://shumaojs.com/sitemap.xml`.
- The production sitemap returns HTTP 200 and contains 59 HTTPS URLs.
- Core pages expose index/follow robots directives, self-referencing HTTPS canonicals, and no blocking `X-Robots-Tag` header.
- The local environment has no Search Console API credentials. The in-app Search Console tab repeatedly timed out and was displaying the unrelated `nscalculators.com` property, so no submission was attempted.

## One-time property setup

1. In Search Console, use the property selector and choose **Add property**.
2. Select **Domain** and enter `shumaojs.com` without `https://` or a path.
3. Copy the Google verification TXT record exactly.
4. In Cloudflare DNS for `shumaojs.com`, add that TXT record at the apex and leave any existing verification records in place.
5. Return to Search Console and complete verification. Do not add the site under the existing `nscalculators.com` property.

## Sitemap submission

1. Open the verified `sc-domain:shumaojs.com` property.
2. Go to **Indexing → Sitemaps**.
3. Submit `sitemap.xml` so the resolved URL is `https://shumaojs.com/sitemap.xml`.
4. Record the submission date, status, discovered URL count, and any parsing error.
5. Do not repeatedly resubmit an unchanged successful sitemap; investigate the reported error instead.

## Priority URL inspection

Inspect these deployed URLs in this order and request indexing only when the live test confirms they are indexable:

1. `https://shumaojs.com/`
2. `https://shumaojs.com/google-ads-management-usa.html`
3. `https://shumaojs.com/google-ads-agency-hong-kong.html`
4. `https://shumaojs.com/articles/google-ads-bidding-budget-usa.html`
5. `https://shumaojs.com/articles/google-ads-bidding-budget-hong-kong.html`

For each URL, record whether Google reports **URL is on Google**, **Discovered**, **Crawled**, **Duplicate**, **Soft 404**, or another exclusion reason. Requesting indexing is not a guarantee and should not be repeated daily.

## Follow-up evidence

- After data appears, export Search results by query, page, country, and date for the last 7 and 28 days.
- Place the CSV files locally in `data/search-console/`; raw exports are ignored by Git.
- Run `python scripts/prioritize_search_console.py` to rank observed US and Hong Kong opportunities.
- Compare indexed pages with the 59 canonical sitemap URLs. Diagnose exclusions by reason rather than treating every non-indexed URL as the same problem.
- Keep the old product's Search Console property separate. Removing a property from the account does not erase Google's historical crawl data, and the Removals tool is only a temporary visibility mechanism, not a site-migration reset.

## External dependency

Enable Cloudflare **Always Use HTTPS** or an equivalent permanent edge redirect. `http://shumaojs.com/` still returns HTTP 200 instead of redirecting to the canonical HTTPS URL. Recheck this before treating protocol consolidation as complete.
