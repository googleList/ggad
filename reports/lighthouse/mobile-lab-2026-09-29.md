# Mobile Lighthouse Lab Check: 2026-09-29

## Scope and limits

- Lighthouse 12.8.2, mobile form factor, performance category only.
- Production baselines were collected from `https://shumaojs.com/` before the responsive-image change.
- Candidate results were collected from a local static server after adding `srcset` and `sizes`.
- These are single-run lab measurements. Different server response times mean the before/after values are directional, not field Core Web Vitals or a deployment claim.
- The PageSpeed Insights API returned HTTP 429, and no CrUX, Search Console CWV, or GA4 data was available.

## Results

| Page | Production score | Candidate score | Production LCP | Candidate LCP | Production transfer | Candidate transfer | CLS | Candidate TBT |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Homepage | 90 | 95 | 3,388 ms | 2,865 ms | 794 KB | 738 KB | 0.000 | 6 ms |
| US management | 100 | 100 | 1,135 ms | 1,052 ms | 815 KB | 750 KB | 0.000 | 0 ms |
| Hong Kong agency | 93 | 97 | 3,198 ms | 2,624 ms | 811 KB | 753 KB | 0.000 | 0 ms |

## Evidence-based change

The production homepage and Hong Kong page used a 1,200px Unsplash source for a mobile rendered width of about 258px. All six Unsplash images on the homepage and localized market pages now provide 480px, 800px, and 1,200px candidates with layout-aware `sizes` values. Width, height, asynchronous decoding, priority, and lazy-loading behavior remain intact.

The static performance gate now rejects Unsplash images without both `srcset` and `sizes`. Recheck production after deployment and use CrUX or Search Console field data when available.
