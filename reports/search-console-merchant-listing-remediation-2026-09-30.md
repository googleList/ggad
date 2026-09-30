# Search Console Merchant Listing Remediation

Date: 2026-09-30

## Diagnosis

The site is an advertising consultancy and does not sell physical products. Product merchant-listing fields such as `shippingDetails`, GTIN, brand, and `hasMerchantReturnPolicy` are therefore not applicable and must not be invented merely to clear Search Console warnings.

The clean local site contains no legitimate Product pages. Search Console is still able to crawl the legacy storefront deployed on production, including `/product.html`, while the clean branch remains blocked from deployment. The alert's combination of missing product image, shipping, global identifier, return policy, and invalid category is consistent with legacy Product merchant markup rather than the current consultancy content.

## Local remediation completed

- Product JSON-LD is prohibited in static HTML and recursively detected even when nested inside another schema entity.
- JavaScript files are scanned for dynamically generated Product markup.
- Removed optional zero-price Offer entities from the two free agency-evaluation WebApplication pages.
- The free tools now use `isAccessibleForFree: true`, which describes them without creating merchant-offer signals.
- The content-policy gate already rejects the legacy product page, product data script, storefront routes, order flows, and payment artifacts.

## Required deployment and Search Console steps

1. Restore write access to `googleList/ggad` for the Git identity `lg-list`, or authenticate Git as an account with repository write permission.
2. Push the clean `main` branch and wait for the static-site deployment to finish.
3. Verify that `/product.html`, `/product-data.js`, `/admin.html`, and other retired storefront URLs return 404 or 410 rather than 200.
4. Inspect the affected example URLs in Search Console. Do not add shipping, return-policy, GTIN, brand, or Product category fields unless the business genuinely starts selling the represented products.
5. Open **Search Console > Shopping > Merchant listings**, select the issue, and click **Validate fix** only after production verification succeeds.

Search Console may retain historical issue counts while Google recrawls the affected URLs. A submitted validation is not proof of completion until the report shows the affected items have cleared.
