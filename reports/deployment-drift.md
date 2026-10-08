# Production deployment drift audit

Generated: 2026-10-08T08:08:44.307633+00:00
Production sitemap: https://shumaojs.com/sitemap.xml

## Summary

- Local sitemap URLs: 63
- Production sitemap URLs: 63
- Missing from production sitemap: 0
- Production-only URLs: 0
- HTTP to HTTPS redirect: fail

## Missing from production

- None

## Production-only URLs

- None

## Protocol canonicalization

- Requested: http://shumaojs.com/
- Final URL: http://shumaojs.com/
- Status: 200
- Action required: configure an edge-level permanent redirect from HTTP to HTTPS.

## Interpretation

A local page is not deployable or indexable evidence until it appears on production and returns a successful HTTP response. Submit the production sitemap to Search Console only after the deployment difference is cleared.
