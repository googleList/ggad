const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const base = new URL(process.argv[2] || "http://127.0.0.1:8777/");
const output = process.argv[3] || path.join(os.tmpdir(), "shumao-match-guide-check");
const articlePath = "articles/sem-keyword-match-guide.html";
const expectedRules = [
  ["steel bolts", [true, true, true]],
  ["buy steel bolts", [true, true, false]],
  ["bolts steel", [true, false, false]],
  ["steel hex bolts", [true, false, false]],
  ["steel bolt", [false, false, false]],
  ["brass bolts", [false, false, false]],
];

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
        const schema = [...document.querySelectorAll('script[type="application/ld+json"]')]
          .map((node) => JSON.parse(node.textContent)).find((item) => item["@type"] === "Article");
        const image = main.querySelector(".article-cover");
        return {
          headline: main.querySelector("h1").textContent.trim(), schemaHeadline: schema.headline,
          canonical: document.querySelector('link[rel="canonical"]').href,
          published: schema.datePublished, modified: schema.dateModified, visibleModified: main.querySelector("time").dateTime,
          image: { src: image.currentSrc, loaded: image.complete && image.naturalWidth > 0, schema: schema.image,
            og: document.querySelector('meta[property="og:image"]').content, twitter: document.querySelector('meta[name="twitter:image"]').content },
          positiveRows: main.querySelectorAll("#positive-match tbody tr").length,
          negativeHeaders: [...main.querySelectorAll("#negative-rule-table thead code")].map((node) => node.textContent),
          rules: [...main.querySelectorAll("#negative-rule-table tbody tr")].map((row) => [row.querySelector("th").textContent,
            [...row.querySelectorAll("td")].map((cell) => cell.textContent)]),
          warning: main.querySelector("#negative-match strong").textContent,
          faqCount: main.querySelectorAll("#match-faq h3").length,
          anchors: [...main.querySelectorAll("nav a")].map((node) => node.getAttribute("href")),
          ids: [...document.querySelectorAll("[id]")].map((node) => node.id),
          localLinks: [...new Set([...main.querySelectorAll("a[href]")].filter((link) => link.origin === location.origin &&
            !link.getAttribute("href").startsWith("#")).map((link) => link.pathname))],
          overflow: document.documentElement.scrollWidth > innerWidth + 1,
        };
      });
      assert.equal(content.headline, "SEM 关键词匹配方式怎么选");
      assert.equal(content.schemaHeadline, content.headline);
      assert.equal(content.canonical, "https://shumaojs.com/articles/sem-keyword-match-guide.html");
      assert.equal(content.published, "2026-09-11");
      assert.equal(content.modified, "2026-10-24T13:01:49+08:00");
      assert.equal(content.visibleModified, content.modified);
      assert.equal(content.image.loaded, true);
      assert.ok(content.image.src.endsWith(width <= 600 ? "thumb-v1.webp" : "groups-v1.jpg"));
      assert.equal(content.image.schema, content.image.og);
      assert.equal(content.image.schema, content.image.twitter);
      assert.equal(content.positiveRows, 3);
      assert.deepEqual(content.negativeHeaders, ["steel bolts", '"steel bolts"', "[steel bolts]"]);
      assert.deepEqual(content.rules, expectedRules.map(([query, excluded]) => [query, excluded.map((value) => value ? "排除" : "本规则不排除")]));
      assert.ok(content.warning.includes("不等于广告一定展示"));
      assert.equal(content.faqCount, 3);
      assert.equal(content.anchors.length, 5);
      assert.equal(new Set(content.ids).size, content.ids.length);
      assert.equal(content.overflow, false);
      for (const href of content.anchors) {
        await page.locator(`main nav a[href="${href}"]`).click();
        await page.waitForFunction((selector) => {
          const top = document.querySelector(selector).getBoundingClientRect().top;
          return top >= document.querySelector("header").getBoundingClientRect().bottom - 1 && top < 180;
        }, href);
      }
      if (width <= 390) for (const table of await page.locator(".article-table-wrap").all()) {
        await table.scrollIntoViewIfNeeded();
        await table.focus();
        await page.keyboard.press("ArrowRight");
        await page.waitForFunction(() => document.activeElement.scrollLeft > 0);
      }
      if (width === 1440) {
        for (const pathname of content.localLinks) assert.equal((await context.request.get(new URL(pathname, base).href)).status(), 200, pathname);
        await page.goto(new URL("articles/google-search-keywords.html", base).href);
        assert.equal(await page.locator(`main a[href="sem-keyword-match-guide.html"]`).count(), 1);
        await page.goto(new URL("google-ads.html", base).href);
        assert.equal(await page.locator(`main a[href="${articlePath}"]`).count(), 1);
      }
      await page.goto(new URL(articlePath, base).href, { waitUntil: "networkidle" });
      if (width === 1440 || width === 390) {
        await page.screenshot({ path: path.join(output, `article-${width}.png`) });
        await page.locator("#negative-match").scrollIntoViewIfNeeded();
        await page.screenshot({ path: path.join(output, `rules-${width}.png`) });
      }
      await page.goto(new URL("articles.html", base).href, { waitUntil: "networkidle" });
      const card = page.locator("[data-article-card]").filter({ has: page.locator(`h3 a[href="${articlePath}"]`) });
      assert.equal(await card.isVisible(), true);
      assert.ok((await card.locator("small").textContent()).startsWith("2026-10-24"));
      await card.locator("img").scrollIntoViewIfNeeded();
      await card.locator("img").evaluate((image) => image.decode());
      results.push({ width, ...content, ruleCellsPassed: 18, anchorsPassed: true, listingPassed: true });
      await context.close();
      console.log(`Passed match guide ${width}px`);
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, "browser.json"), JSON.stringify({ checkedAt: new Date().toISOString(), base: base.href, results, pageErrors: errors }, null, 2) + "\n");
  } finally { await browser.close(); }
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
