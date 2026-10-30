# Existing Tools Directory: Navigation Repair

## Selection and Evidence

Checked origin/main and public deployment.json: both at 2c1ee1bed8eac883b5fc23da7739bb2d0bbe053d before editing. The preceding goal work added a reproducible comparison pipeline, not a new performance period. The immediately preceding owner-review turn confirmed an already recorded Googlebot acceptance; repeating that record made no new growth progress. This batch instead reproduces and repairs a real existing-resource navigation failure.

Public browser reproduction before editing, October 30:

1. Open nav.html#standard-seo. Click AI tools. Selected tab became ai, but URL stayed #standard-seo and sidebar current class stayed #standard-seo. Reload selected standard again.
2. With JavaScript disabled, the standard panel was not visible and contained zero visible links. The HTML hidden attribute and CSS hid it permanently; tab buttons could not restore it.
3. A normal-motion mobile check found category headings at about 112px while the sticky directory occupied 92-145px. Reserve 160px on mobile (112px desktop) for native category/panel anchors and check that headings clear the actual sticky element.

These are observed usability/discovery defects, not proof they caused rankings, conversion loss or Core Web Vitals regression. Consultation-page inspection found a native Telegram link and no fake submit form; no real contact/message was sent. Existing approved service promises are not expanded.

## Change Scope

- Preserve directory title, description, all tool destinations, 17 category anchors, two-column desktop shell, mobile menu, and existing AI/regular categories.
- Publish both panels in source HTML. Hide inert tabs until the dedicated script is initialized. Both panels remain available with no JavaScript or if the new script is blocked.
- Move the old directory-only handler out of the shared script into assets/tool-navigation-v1.js, requested only by nav.html. The existing asset builder publishes assets; no new application framework, dependency or public planning data.
- The directory requests versioned shared-script and stylesheet URLs so browsers do not reuse old duplicate tool handlers, inert-tab display rules or mobile anchor offsets during rollout. Other pages retain their existing asset URL and behavior.
- Synchronize selected panel, aria-selected, roving tabindex, sidebar aria-current, fragment URL and back/forward. Preserve native sidebar anchor history and modified-click behavior. Add Left/Right/Home/End tab keys and focusable panels.
- Safely ignore malformed/unknown fragments; direct known category/panel URLs remain valid.
- Do not update article titles, bodies, RSS, sitemap dates, publication dates, covers, robots, analytics, account settings, company registration or external profiles.

## Validation Plan

Five focused standard-library unit checks run in existing CI, including actual Node syntax validation. Full existing test/gate suite, scoped internal-link audit and public artifact build. Actual Playwright matrices cover 1440/768/390/320 JavaScript, 1440/390 no JavaScript and 1440/390 blocked dedicated script; exercise all 17 anchors, direct link and tab reload, browser history, keyboard controls, malformed/hash updates, fallback links and overflow. Recheck article-hub and representative header behavior because the old shared handler is removed.

No-JavaScript Playwright actionability waits use frame-based stability that can stall when page JavaScript is disabled; fallback testing uses native keyboard focus/Enter instead of bypassing navigation or marking a timeout as a pass. The first full matrix also caught the existing mobile CSS display override, which was corrected to require successful initialization.

## Measurement and Review

Latest genuine GSC data remain through October 27. No new GSC/GA4/keyword-volume/field-CWV read or growth claim. Preserve all four Simplified Chinese targets and US/HK localizations. Technical repair does not require inventing a new marketing-title batch, article thumbnail, human content approval or a new keyword page. User separately accepted the llms.txt tutorial during this run; record only that article's acceptance. All other pending reviews remain independent.
