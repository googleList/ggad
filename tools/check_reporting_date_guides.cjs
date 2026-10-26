const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const base = new URL(process.argv[2] || "http://127.0.0.1:8797/");
const output = process.argv[3];
assert.ok(output, "Provide an evidence directory");
const guides = [
  { locale: "usa", lang: "en-US", alternate: "zh-Hant-HK", title: "Google Ads Monthly Reporting Guide for US Businesses", h1: "Google Ads monthly reporting for US businesses", region: "Cross-month lead date example" },
  { locale: "hong-kong", lang: "zh-Hant-HK", alternate: "en-US", title: "香港 Google Ads 月度報告指南：預算、查詢及成交", h1: "香港 Google Ads 月度報告指南", region: "跨月查詢日期示例" },
];

async function main() {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH, headless: true });
  const results = [], errors = [];
  try {
    for (const guide of guides) {
      const articlePath = `articles/google-ads-monthly-reporting-${guide.locale}.html`;
      for (const [width, javaScriptEnabled] of [[1440, true], [768, true], [390, true], [320, true], [1440, false], [390, false]]) {
        const context = await browser.newContext({ viewport: { width, height: 900 }, javaScriptEnabled, reducedMotion: "reduce" });
        const page = await context.newPage();
        page.setDefaultTimeout(15000);
        page.on("pageerror", (error) => errors.push(`${guide.locale}/${width}/${javaScriptEnabled}: ${error.message}`));
        assert.equal((await page.goto(new URL(articlePath, base).href, { waitUntil: "networkidle", timeout: 45000 })).status(), 200);
        const content = await page.evaluate(() => {
          const main = document.querySelector("main");
          const schema = [...document.querySelectorAll('script[type="application/ld+json"]')].map((node) => JSON.parse(node.textContent)).find((item) => item["@type"] === "Article");
          const image = main.querySelector(".article-cover");
          return {
            lang: document.documentElement.lang, title: document.title, headline: main.querySelector("h1").textContent, schema,
            canonical: document.querySelector('link[rel="canonical"]').href, modified: main.querySelector("time").dateTime,
            alternates: [...document.querySelectorAll('link[rel="alternate"][hreflang]')].map((node) => ({ lang: node.hreflang, href: node.href })),
            descriptions: [document.querySelector('meta[name="description"]').content, document.querySelector('meta[property="og:description"]').content, document.querySelector('meta[name="twitter:description"]').content, schema.description],
            image: { loaded: image.complete && image.naturalWidth > 0, src: image.currentSrc, ratio: image.getBoundingClientRect().width / image.getBoundingClientRect().height },
            socialImages: [schema.image, document.querySelector('meta[property="og:image"]').content, document.querySelector('meta[name="twitter:image"]').content],
            stages: [...main.querySelectorAll("[data-report-stage]")].map((node) => ({ stage: node.dataset.reportStage, date: node.dataset.eventDate })),
            reportChecks: main.querySelectorAll("[data-report-checks] > li").length,
            boundary: main.querySelector('[data-report-boundary="one-lead"]').textContent,
            anchors: [...main.querySelectorAll("nav a")].map((link) => link.getAttribute("href")),
            ids: [...document.querySelectorAll("[id]")].map((node) => node.id),
            links: [...new Set([...main.querySelectorAll("a[href]")].filter((link) => link.origin === location.origin && !link.getAttribute("href").startsWith("#")).map((link) => link.pathname + link.hash))],
            overflow: document.documentElement.scrollWidth > innerWidth + 1,
          };
        });
        assert.equal(content.lang, guide.lang);
        assert.equal(content.title, guide.title);
        assert.equal(content.headline, guide.h1);
        assert.equal(content.schema.headline, guide.h1);
        assert.equal(content.canonical, "https://shumaojs.com/" + articlePath);
        assert.equal(content.schema.datePublished, "2026-09-29");
        assert.equal(content.modified, "2026-10-26T23:19:41+08:00");
        assert.equal(content.schema.dateModified, content.modified);
        assert.equal(content.alternates.length, 2);
        assert.equal(content.alternates.find((item) => item.lang === guide.lang).href, content.canonical);
        assert.ok(content.alternates.find((item) => item.lang === guide.alternate).href.endsWith(guides.find((item) => item.lang === guide.alternate).locale + ".html"));
        assert.equal(new Set(content.descriptions).size, 1);
        assert.equal(new Set(content.socialImages).size, 1);
        assert.equal(content.image.loaded, true);
        assert.ok(content.image.src.endsWith(width <= 600 ? "plan-thumb-v1.webp" : "plan-v1.jpg"));
        assert.ok(Math.abs(content.image.ratio - 16 / 9) < 0.01);
        assert.deepEqual(content.stages, [{ stage: "interaction", date: "2026-09-29" }, { stage: "form", date: "2026-10-03" }, { stage: "qualified", date: "2026-10-08" }, { stage: "upload", date: "2026-10-10" }]);
        assert.equal(content.reportChecks, 4);
        assert.ok(content.boundary.includes(guide.locale === "usa" ? "not two customers" : "不能把兩個操作相加當作兩名客戶"));
        assert.equal(content.overflow, false);
        assert.equal(new Set(content.ids).size, content.ids.length);
        assert.equal(content.anchors.length, 4);
        for (const href of content.anchors) {
          await page.locator(`main nav a[href="${href}"]`).click();
          const position = await page.locator(href).evaluate((node) => ({ top: node.getBoundingClientRect().top, headerBottom: document.querySelector("header").getBoundingClientRect().bottom }));
          assert.ok(position.top >= position.headerBottom - 1 && position.top < 190, href);
        }
        if (width <= 390) {
          const region = page.getByRole("region", { name: guide.region, exact: true });
          await region.scrollIntoViewIfNeeded();
          await region.focus();
          await page.keyboard.press("ArrowRight");
          let scrolled = false;
          for (let attempt = 0; attempt < 30; attempt += 1) {
            scrolled = await region.evaluate((node) => document.activeElement === node && node.scrollLeft > 0);
            if (scrolled) break;
            await new Promise((resolve) => setTimeout(resolve, 50));
          }
          assert.equal(scrolled, true, guide.region);
          if (javaScriptEnabled) {
            await page.evaluate(() => scrollTo(0, 0));
            const menu = page.locator(".mobile-menu-toggle");
            await menu.click();
            assert.equal(await menu.getAttribute("aria-expanded"), "true");
            assert.equal(await page.locator("header nav a").first().isVisible(), true);
            await menu.click();
            assert.equal(await menu.getAttribute("aria-expanded"), "false");
          }
        }
        if (width === 1440 && javaScriptEnabled) {
          for (const target of content.links) assert.equal((await context.request.get(new URL(target, base).href)).status(), 200, target);
        }
        if ([1440, 390].includes(width)) {
          await page.goto(new URL(articlePath, base).href, { waitUntil: "networkidle" });
          await page.screenshot({ path: path.join(output, `${guide.locale}-${width}-${javaScriptEnabled ? "js" : "nojs"}.png`) });
          await page.locator('main nav a[href="#cohort-example"]').click();
          await page.screenshot({ path: path.join(output, `${guide.locale}-cohort-${width}-${javaScriptEnabled ? "js" : "nojs"}.png`) });
        }
        await page.goto(new URL("articles.html", base).href, { waitUntil: "networkidle" });
        const card = page.locator("[data-article-card]").filter({ has: page.locator(`h3 a[href="${articlePath}"]`) });
        let listingPage = null;
        if (javaScriptEnabled) {
          await page.locator('[data-article-category-button][data-article-category="sem"]').click();
          listingPage = 1;
          while (!await card.isVisible()) {
            assert.ok(listingPage < 7);
            const next = page.locator(".pagination button").last();
            assert.equal(await next.isDisabled(), false);
            await next.click();
            listingPage += 1;
          }
        }
        assert.equal(await card.isVisible(), true);
        assert.ok((await card.locator("small").textContent()).startsWith("2026-10-26"));
        await card.locator("img").scrollIntoViewIfNeeded();
        await card.locator("img").evaluate((image) => image.decode());
        assert.ok((await card.locator("img").getAttribute("src")).endsWith("conversion-evidence-plan-thumb-v1.webp"));
        await card.locator("h3 a").click();
        assert.equal(new URL(page.url()).pathname, "/" + articlePath);
        results.push({ locale: guide.locale, width, javaScriptEnabled, ...content, keyboardScroll: width <= 390, listingPage, listingJourneyPassed: true });
        await context.close();
        console.log(`Passed reporting dates ${guide.locale}/${width}px/${javaScriptEnabled ? "JS" : "noJS"}`);
      }
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, "browser.json"), JSON.stringify({ checkedAt: new Date().toISOString(), base: base.href, results, pageErrors: errors }, null, 2) + "\n");
  } finally { await browser.close(); }
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
