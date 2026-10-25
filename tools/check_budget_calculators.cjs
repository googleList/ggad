const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const base = new URL(process.argv[2] || "http://127.0.0.1:8784/");
const output = process.argv[3] || path.join(os.tmpdir(), "shumao-budget-calculators");
const pages = [
  { path: "articles/google-budget-pacing.html", locale: "zh-CN", currency: "USD", initial: [3000, 30, 10, 850] },
  { path: "articles/google-ads-bidding-budget-usa.html", locale: "en-US", currency: "USD", initial: [3000, 30, 10, 850] },
  { path: "articles/google-ads-bidding-budget-hong-kong.html", locale: "zh-Hant-HK", currency: "HKD", initial: [24000, 30, 10, 6800] },
];
const keys = ["total", "days", "elapsed", "spent"];
async function fill(form, values) {
  for (let i = 0; i < keys.length; i++) await form.locator("[data-budget-" + keys[i] + "]").fill(String(values[i]));
}
async function read(form) {
  return form.evaluate((node) => ({
    daily: node.querySelector("[data-budget-daily]").textContent,
    expected: node.querySelector("[data-budget-expected]").textContent,
    variance: node.querySelector("[data-budget-variance]").textContent,
    remaining: node.querySelector("[data-budget-remaining]").textContent,
    status: node.querySelector("[data-budget-status]").textContent,
  }));
}
async function main() {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH });
  const results = [], errors = [];
  try {
    for (const width of [1440, 768, 390, 320]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: "reduce" });
      for (const target of pages) {
        const page = await context.newPage();
        page.on("pageerror", (error) => errors.push(target.locale + ":" + error.message));
        assert.equal((await page.goto(new URL(target.path, base).href, { waitUntil: "networkidle", timeout: 45000 })).status(), 200);
        const form = page.locator("[data-budget-calculator]");
        await page.waitForFunction(() => document.querySelector("[data-budget-calculator]").dataset.budgetReady === "true");
        const money = new Intl.NumberFormat(target.locale, { style: "currency", currency: target.currency, maximumFractionDigits: 2 });
        await fill(form, [3000, 30, 10, 850]);
        const nominal = await read(form);
        assert.equal(nominal.daily, money.format(100));
        assert.equal(nominal.expected, money.format(1000));
        assert.equal(nominal.variance, "-" + money.format(150));
        assert.equal(nominal.remaining, money.format(107.5));
        assert.equal(await form.locator("[data-budget-error]").isVisible(), false);
        let invalidCases = 0;
        const invalid = [
          ["total", ""], ["days", ""], ["elapsed", ""], ["spent", ""],
          ["total", "0"], ["days", "0"], ["spent", "-1"], ["elapsed", "31"],
          ["days", "30.5"], ["elapsed", "10.5"], ["spent", "1.001"],
        ];
        for (const [key, value] of invalid) {
          await fill(form, [3000, 30, 10, 850]);
          await form.locator("[data-budget-" + key + "]").fill(value);
          assert.equal(await form.locator("[data-budget-error]").isVisible(), true, key + ":" + value);
          assert.equal(await form.locator(".budget-calculator-results").isVisible(), false);
          assert.equal(await form.locator("[data-budget-" + key + "]").getAttribute("aria-invalid"), "true");
          const stale = await read(form);
          assert.deepEqual([stale.daily, stale.expected, stale.variance, stale.remaining], ["—", "—", "—", "—"]);
          assert.equal(stale.status, "");
          invalidCases++;
        }
        await fill(form, [3000, 30, 0, 0]);
        assert.equal((await read(form)).expected, money.format(0));
        assert.equal(await form.locator("[data-budget-error]").isVisible(), false);
        await fill(form, [3000, 30, 30, 850]);
        assert.equal((await read(form)).remaining, "—");
        await fill(form, [3000, 30, 10, 3500]);
        const overspend = await read(form);
        assert.equal(overspend.remaining, money.format(0));
        assert.match(overspend.status, /超|exceeds/);
        await fill(form, [3000, 30, 10, 1000]);
        assert.equal((await read(form)).variance, "+" + money.format(0));
        const currentUrl = page.url();
        await form.locator("[data-budget-spent]").press("Enter");
        assert.equal(page.url(), currentUrl);
        await form.locator('[type="reset"]').click();
        await page.waitForFunction(({ spent, remaining }) => {
          const node = document.querySelector("[data-budget-calculator]");
          return node.querySelector("[data-budget-spent]").value === String(spent) &&
            node.querySelector("[data-budget-remaining]").textContent === remaining && !node.querySelector(".budget-calculator-results").hidden;
        }, { spent: target.initial[3], remaining: money.format((target.initial[0] - target.initial[3]) / (target.initial[1] - target.initial[2])) });
        assert.equal((await read(form)).daily, money.format(target.initial[0] / target.initial[1]));
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
        if (width === 1440 || width === 390) {
          await form.evaluate((node) => scrollTo({ top: scrollY + node.getBoundingClientRect().top - 112, behavior: "instant" }));
          await page.screenshot({ path: path.join(output, target.locale + "-form-" + width + ".png") });
          await form.locator(".budget-calculator-results").evaluate((node) => scrollTo({ top: scrollY + node.getBoundingClientRect().top - 112, behavior: "instant" }));
          await page.screenshot({ path: path.join(output, target.locale + "-results-" + width + ".png") });
        }
        const anchorChecks = [];
        if (target.locale === "zh-CN") {
          const metadata = await page.evaluate(() => {
            const article = [...document.querySelectorAll('script[type="application/ld+json"]')].map((node) => JSON.parse(node.textContent)).find((node) => node["@type"] === "Article");
            const image = document.querySelector(".article-cover");
            return { headline: document.querySelector("h1").textContent, schemaHeadline: article.headline,
              published: article.datePublished, modified: article.dateModified, visibleModified: document.querySelector("time").dateTime,
              canonical: document.querySelector('link[rel="canonical"]').href,
              image: image.currentSrc, loaded: image.naturalWidth > 0,
              descriptions: [article.description, document.querySelector('meta[name="description"]').content, document.querySelector('meta[property="og:description"]').content, document.querySelector('meta[name="twitter:description"]').content],
              internalLinks: [...new Set([...document.querySelectorAll("main a[href]")].filter((link) =>
                link.origin === location.origin && !link.getAttribute("href").startsWith("#")).map((link) => link.pathname))],
              sharingImages: [article.image, document.querySelector('meta[property="og:image"]').content, document.querySelector('meta[name="twitter:image"]').content] };
          });
          assert.equal(metadata.headline, "Google Ads 小预算怎么投？日预算与测试计划");
          assert.equal(metadata.schemaHeadline, metadata.headline);
          assert.equal(metadata.published, "2026-09-11");
          assert.equal(metadata.modified, "2026-10-25T09:32:01+08:00");
          assert.equal(metadata.visibleModified, metadata.modified);
          assert.equal(metadata.canonical, "https://shumaojs.com/articles/google-budget-pacing.html");
          assert.equal(metadata.loaded, true);
          assert.equal(new Set(metadata.sharingImages).size, 1);
          assert.equal(new Set(metadata.descriptions).size, 1);
          assert.ok(metadata.image.endsWith(width <= 600 ? "plan-thumb-v1.webp" : "plan-v1.jpg"));
          if (width === 1440) for (const link of metadata.internalLinks) assert.equal((await context.request.get(new URL(link, base).href)).status(), 200, link);
          for (const href of await page.locator("main nav a").evaluateAll((links) => links.map((link) => link.getAttribute("href")))) {
            await page.locator('main nav a[href="' + href + '"]').click();
            await page.waitForFunction((selector) => {
              const top = document.querySelector(selector).getBoundingClientRect().top;
              const atEnd = scrollY + innerHeight >= document.documentElement.scrollHeight - 2;
              return top >= document.querySelector("header").getBoundingClientRect().bottom - 1 &&
                (top < 180 || (atEnd && top < innerHeight - 80));
            }, href);
            anchorChecks.push(await page.evaluate((selector) => ({ selector,
              top: document.querySelector(selector).getBoundingClientRect().top,
              atEnd: scrollY + innerHeight >= document.documentElement.scrollHeight - 2 }), href));
          }
        }
        results.push({ width, page: target.path, locale: target.locale, currency: target.currency,
          nominal, invalidCasesPassed: invalidCases, zeroAndCompleteAndOverspendPassed: true,
          resetAndEnterPassed: true, anchorChecks, noOverflow: true });
        await page.close();
        console.log("Passed pacing " + target.locale + " " + width + "px");
      }
      await context.close();
    }
    for (const target of pages) {
      for (const mode of ["no-javascript", "blocked-calculator-script"]) {
        const context = await browser.newContext({ viewport: { width: 390, height: 900 }, javaScriptEnabled: mode !== "no-javascript" });
        const page = await context.newPage();
        if (mode === "blocked-calculator-script") await page.route("**/budget-calculator.js?*", (route) => route.abort());
        await page.goto(new URL(target.path, base).href, { waitUntil: "load", timeout: 45000 });
        const form = page.locator("[data-budget-calculator]");
        for (const field of await form.locator("input").all()) assert.equal(await field.isDisabled(), true);
        assert.equal(await form.locator(".budget-calculator-results").isVisible(), false);
        assert.equal(await form.locator('[type="reset"]').isDisabled(), true);
        assert.equal(await form.locator("[data-budget-unavailable]").isVisible(), true);
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
        results.push({ page: target.path, mode, inactiveControlsDisabled: true, staleResultsHidden: true, noOverflow: true });
        await context.close();
      }
    }
    const listingContext = await browser.newContext({ viewport: { width: 390, height: 900 } });
    const listing = await listingContext.newPage();
    await listing.goto(new URL("articles.html", base).href, { waitUntil: "networkidle", timeout: 45000 });
    await listing.locator('[data-article-category-button][data-article-category="sem"]').click();
    const card = listing.locator("[data-article-card]").filter({ has: listing.locator('h3 a[href="articles/google-budget-pacing.html"]') });
    let listingPage = 1;
    while (!await card.isVisible()) {
      assert.ok(listingPage < 7);
      await listing.locator(".pagination button").last().click();
      listingPage++;
    }
    assert.ok((await card.locator("small").textContent()).startsWith("2026-10-25"));
    assert.ok((await card.locator("img").getAttribute("src")).endsWith("pacing-plan-thumb-v1.webp"));
    await card.locator("img").scrollIntoViewIfNeeded();
    await card.locator("img").evaluate((image) => image.decode());
    await listing.screenshot({ path: path.join(output, "listing-390.png") });
    results.push({ mode: "simplified-listing", width: 390, listingPage, cardDateAndThumbnailPassed: true });
    await listing.goto(new URL("nav.html", base).href, { waitUntil: "networkidle", timeout: 45000 });
    await listing.getByRole("tab", { name: "常规工具", exact: true }).click();
    const directoryLink = listing.locator('a.resource-card[href="articles/google-budget-pacing.html#calculator"]');
    assert.equal(await directoryLink.isVisible(), true);
    assert.equal(await directoryLink.getAttribute("target"), null);
    assert.equal(await listing.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
    await directoryLink.click();
    await listing.waitForURL(new URL("articles/google-budget-pacing.html#calculator", base).href);
    await listing.waitForFunction(() => {
      const top = document.querySelector("#calculator").getBoundingClientRect().top;
      return top >= document.querySelector("header").getBoundingClientRect().bottom - 1 && top < 180;
    });
    results.push({ mode: "tools-directory-entry", width: 390, nativeSameTabNavigationPassed: true, anchorClear: true });
    await listingContext.close();
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, "browser.json"), JSON.stringify({ checkedAt: new Date().toISOString(), base: base.href, results, pageErrors: errors }, null, 2) + "\n");
  } finally { await browser.close(); }
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
