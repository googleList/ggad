const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");

const base = new URL(process.argv[2] || "http://127.0.0.1:8774/");
const output = process.argv[3] || path.join(os.tmpdir(), "shumao-cost-guide-check");
const articlePath = "articles/google-search-ads-cost-guide.html";

async function main() {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH });
  const results = [];
  const errors = [];
  try {
    for (const width of [1440, 768, 390, 320]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: "reduce" });
      const page = await context.newPage();
      page.setDefaultTimeout(15000);
      page.on("pageerror", (error) => errors.push(`${width}px: ${error.message}`));
      const response = await page.goto(new URL(articlePath, base).href, { waitUntil: "networkidle" });
      assert.equal(response.status(), 200);
      const content = await page.evaluate(() => {
        const article = [...document.querySelectorAll('script[type="application/ld+json"]')]
          .map((node) => JSON.parse(node.textContent)).find((item) => item["@type"] === "Article");
        const main = document.querySelector("main");
        const cover = main.querySelector(".article-cover");
        return {
          headline: document.querySelector("h1").textContent.trim(), schemaHeadline: article.headline,
          published: article.datePublished, modified: article.dateModified,
          visibleModified: main.querySelector("time").dateTime,
          cover: { src: cover.currentSrc, loaded: cover.complete && cover.naturalWidth > 0 },
          rows: [...main.querySelectorAll("#lead-budget tbody tr")]
            .map((row) => [...row.querySelectorAll("th,td")].map((cell) => cell.textContent.trim())),
          anchors: [...main.querySelectorAll('nav a[href^="#"]')].map((node) => node.getAttribute("href")),
          ids: [...main.querySelectorAll("[id]")].map((node) => node.id),
          localLinks: [...new Set([...main.querySelectorAll("a[href]")]
            .filter((link) => link.origin === location.origin && !link.getAttribute("href").startsWith("#"))
            .map((link) => link.pathname))],
          overflow: document.documentElement.scrollWidth > innerWidth + 1,
        };
      });
      assert.equal(content.headline, content.schemaHeadline);
      assert.equal(content.published, "2026-09-11");
      assert.equal(content.modified, "2026-10-24T00:20:55+08:00");
      assert.equal(content.visibleModified, content.modified);
      assert.equal(content.cover.loaded, true);
      assert.ok(content.cover.src.endsWith(width <= 600 ? "thumb-v1.webp" : "leads-v1.jpg"));
      assert.equal(content.overflow, false);
      assert.equal(new Set(content.ids).size, content.ids.length);
      assert.equal(content.rows.length, 3);
      for (const row of content.rows) {
        const [qualifiedPercent, raw, clicks, budget] = row.map((value) => Number(value.replace(/[% ,]/g, "")));
        const rate = qualifiedPercent / 100;
        assert.equal(raw, 20 / rate);
        assert.equal(clicks, Math.ceil(20 / 0.03 / rate));
        assert.equal(budget, clicks * 2);
      }
      assert.equal(content.anchors.length, 5);
      for (const href of content.anchors) {
        assert.ok(content.ids.includes(href.slice(1)));
        await page.locator(`main nav a[href="${href}"]`).click();
        await page.waitForFunction((id) => {
          const top = document.querySelector(id).getBoundingClientRect().top;
          return top >= document.querySelector("header").getBoundingClientRect().bottom - 1 && top < 180;
        }, href);
      }
      const region = page.getByRole("region", { name: "假设演算：合格率如何改变 20 条有效询盘的媒体预算", exact: true });
      await region.scrollIntoViewIfNeeded();
      if (width <= 390) {
        await region.focus();
        await page.keyboard.press("ArrowRight");
        await page.waitForFunction(() => document.querySelector(".article-table-wrap").scrollLeft > 0);
      }
      if (width === 1440) {
        for (const pathname of content.localLinks) {
          assert.equal((await context.request.get(new URL(pathname, base).href)).status(), 200, pathname);
        }
      }
      if (width === 1440 || width === 390) {
        await page.evaluate(() => scrollTo(0, 0));
        await page.screenshot({ path: path.join(output, `article-${width}.png`) });
        await region.scrollIntoViewIfNeeded();
        await page.screenshot({ path: path.join(output, `scenario-${width}.png`) });
      }
      await page.goto(new URL("articles.html", base).href, { waitUntil: "networkidle" });
      const card = page.locator("article[data-article-card]").filter({
        has: page.locator(`h3 a[href="${articlePath}"]`),
      });
      await card.scrollIntoViewIfNeeded();
      await page.waitForFunction(() => {
        const image = document.querySelector('img[src*="ads-budget-qualified-leads-thumb"]');
        return image?.complete && image.naturalWidth === 480;
      });
      assert.ok((await card.locator("small").innerText()).startsWith("2026-10-24"));
      if (width === 1440 || width === 390) {
        await page.screenshot({ path: path.join(output, `listing-${width}.png`) });
      }
      results.push({ width, ...content, listingImageLoaded: true, tableKeyboardScrollPassed: width <= 390 ? true : null });
      console.log(`Passed ${width}px cost guide, scenario math and article card`);
      await context.close();
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, "browser.json"), JSON.stringify({
      checkedAt: new Date().toISOString(), base: base.href, results, pageErrors: errors,
    }, null, 2) + "\n");
  } finally {
    await browser.close();
  }
}

main().catch((error) => { console.error(error); process.exitCode = 1; });
