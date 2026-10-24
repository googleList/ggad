const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const base = new URL(process.argv[2] || "http://127.0.0.1:8776/");
const output = process.argv[3] || path.join(os.tmpdir(), "shumao-keyword-guide-check");
const articlePath = "articles/google-search-keywords.html";

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
      assert.equal((await page.goto(new URL(articlePath, base).href, { waitUntil: "networkidle", timeout: 45000 })).status(), 200);
      const content = await page.evaluate(() => {
        const main = document.querySelector("main");
        const article = [...document.querySelectorAll('script[type="application/ld+json"]')]
          .map((node) => JSON.parse(node.textContent)).find((item) => item["@type"] === "Article");
        const image = main.querySelector(".article-cover");
        return {
          headline: main.querySelector("h1").textContent.trim(), schemaHeadline: article.headline,
          canonical: document.querySelector('link[rel="canonical"]').href,
          published: article.datePublished, modified: article.dateModified, visibleModified: main.querySelector("time").dateTime,
          cover: { src: image.currentSrc, loaded: image.complete && image.naturalWidth > 0, schema: article.image,
            og: document.querySelector('meta[property="og:image"]').content, twitter: document.querySelector('meta[name="twitter:image"]').content },
          mappingRows: main.querySelectorAll("#intent-map tbody tr").length,
          negativeRows: main.querySelectorAll("#negative-keywords tbody tr").length,
          faqCount: main.querySelectorAll("#keyword-faq h3").length,
          anchors: [...main.querySelectorAll("nav a")].map((link) => link.getAttribute("href")),
          localLinks: [...new Set([...main.querySelectorAll("a[href]")]
            .filter((link) => link.origin === location.origin && !link.getAttribute("href").startsWith("#"))
            .map((link) => link.pathname))],
          overflow: document.documentElement.scrollWidth > innerWidth + 1,
          hypotheticalExample: main.querySelector("#review").textContent.includes("假设") && main.querySelector("#review").textContent.includes("100 美元"),
          exampleValues: main.querySelector("[data-lead-cost-example]").textContent.match(/\d+/g).map(Number),
        };
      });
      assert.equal(content.headline, "Google 搜索广告关键词怎么分组");
      assert.equal(content.headline, content.schemaHeadline);
      assert.equal(content.canonical, "https://shumaojs.com/articles/google-search-keywords.html");
      assert.equal(content.published, "2026-09-11");
      assert.equal(content.modified, "2026-10-24T01:07:23+08:00");
      assert.equal(content.visibleModified, content.modified);
      assert.equal(content.cover.loaded, true);
      assert.ok(content.cover.src.endsWith(width <= 600 ? "thumb-v1.webp" : "groups-v1.jpg"));
      assert.equal(content.cover.schema, content.cover.og);
      assert.equal(content.cover.schema, content.cover.twitter);
      assert.equal(content.mappingRows, 4);
      assert.equal(content.negativeRows, 3);
      assert.equal(content.faqCount, 3);
      assert.equal(content.hypotheticalExample, true);
      const [spend, raw, qualified, rawCost, qualifiedCost] = content.exampleValues;
      assert.equal(spend / raw, rawCost);
      assert.equal(spend / qualified, qualifiedCost);
      assert.equal(content.overflow, false);
      assert.equal(content.anchors.length, 6);
      for (const href of content.anchors) {
        await page.locator(`main nav a[href="${href}"]`).click();
        await page.waitForFunction((selector) => {
          const top = document.querySelector(selector).getBoundingClientRect().top;
          return top >= document.querySelector("header").getBoundingClientRect().bottom - 1 && top < 180;
        }, href);
        assert.ok(await page.locator(href).isVisible());
      }
      for (const region of await page.locator(".article-table-wrap").all()) {
        await region.scrollIntoViewIfNeeded();
        if (width <= 390) {
          await region.focus();
          await page.keyboard.press("ArrowRight");
          await page.waitForFunction(() => document.activeElement.scrollLeft > 0);
        }
      }
      if (width === 1440) for (const pathname of content.localLinks) {
        assert.equal((await context.request.get(new URL(pathname, base).href)).status(), 200, pathname);
      }
      if (width === 1440 || width === 390) {
        await page.locator("#negative-keywords").scrollIntoViewIfNeeded();
        await page.screenshot({ path: path.join(output, `negative-${width}.png`) });
        await page.evaluate(() => scrollTo(0, 0));
        await page.screenshot({ path: path.join(output, `article-${width}.png`) });
      }
      await page.goto(new URL("articles.html", base).href, { waitUntil: "networkidle", timeout: 45000 });
      const card = page.locator("[data-article-card]").filter({ has: page.locator(`h3 a[href="${articlePath}"]`) });
      assert.equal(await card.isVisible(), true);
      assert.ok((await card.locator("small").textContent()).startsWith("2026-10-24"));
      await card.locator("img").scrollIntoViewIfNeeded();
      await card.locator("img").evaluate((image) => image.decode());
      assert.ok((await card.locator("img").getAttribute("src")).endsWith("groups-thumb-v1.webp"));
      results.push({ width, ...content, anchorsPassed: true, mobileTablesKeyboardScroll: width <= 390, listingPassed: true });
      await context.close();
      console.log(`Passed keyword guide ${width}px`);
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, "browser.json"), JSON.stringify({ checkedAt: new Date().toISOString(), base: base.href, results, pageErrors: errors }, null, 2) + "\n");
  } finally { await browser.close(); }
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
