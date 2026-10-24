const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const base = new URL(process.argv[2] || "http://127.0.0.1:8778/");
const output = process.argv[3] || path.join(os.tmpdir(), "shumao-agency-guide-check");
const articlePath = "articles/how-to-choose-advertising-agency.html";

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
        const schema = [...document.querySelectorAll('script[type="application/ld+json"]')].map((node) => JSON.parse(node.textContent))
          .find((item) => item["@type"] === "Article");
        const cover = main.querySelector(".article-cover");
        return {
          headline: main.querySelector("h1").textContent.trim(), schemaHeadline: schema.headline,
          canonical: document.querySelector('link[rel="canonical"]').href,
          published: schema.datePublished, modified: schema.dateModified, visibleModified: main.querySelector("time").dateTime,
          cover: { src: cover.currentSrc, loaded: cover.complete && cover.naturalWidth > 0, schema: schema.image,
            og: document.querySelector('meta[property="og:image"]').content, twitter: document.querySelector('meta[name="twitter:image"]').content },
          criteria: [...main.querySelectorAll("[data-agency-criterion]")].map((section) => ({
            id: section.id, heading: section.querySelector("h2").textContent.trim(),
            evidence: section.querySelectorAll("[data-evidence]").length,
            questions: section.querySelectorAll("[data-question]").length,
          })),
          feeRows: main.querySelectorAll("#fees tbody tr").length,
          anchors: [...main.querySelectorAll("nav a")].map((node) => node.getAttribute("href")),
          ids: [...document.querySelectorAll("[id]")].map((node) => node.id),
          selfDisclosure: main.querySelector("p:not([class])").textContent,
          localLinks: [...new Set([...main.querySelectorAll("a[href]")].filter((link) => link.origin === location.origin &&
            !link.getAttribute("href").startsWith("#")).map((link) => link.pathname))],
          overflow: document.documentElement.scrollWidth > innerWidth + 1,
        };
      });
      assert.equal(content.headline, "广告代理商怎么选？签约前要看的 6 个指标");
      assert.equal(content.schemaHeadline, content.headline);
      assert.equal(content.canonical, "https://shumaojs.com/articles/how-to-choose-advertising-agency.html");
      assert.equal(content.published, "2026-09-11");
      assert.equal(content.modified, "2026-10-24T13:18:20+08:00");
      assert.equal(content.visibleModified, content.modified);
      assert.equal(content.cover.loaded, true);
      assert.ok(content.cover.src.endsWith(width <= 600 ? "thumb-v1.webp" : "review-v1.jpg"));
      assert.equal(content.cover.schema, content.cover.og);
      assert.equal(content.cover.schema, content.cover.twitter);
      assert.deepEqual(content.criteria.map((criterion) => criterion.id), ["scope", "ownership", "measurement", "fees", "evidence", "handover"]);
      content.criteria.forEach((criterion, index) => {
        assert.ok(criterion.heading.startsWith(`${index + 1}.`));
        assert.equal(criterion.evidence, 1);
        assert.equal(criterion.questions, 1);
      });
      assert.ok(content.selfDisclosure.includes("不是第三方榜单或认证"));
      assert.equal(content.feeRows, 5);
      assert.equal(content.anchors.length, 6);
      assert.equal(new Set(content.ids).size, content.ids.length);
      assert.equal(content.overflow, false);
      for (const href of content.anchors) {
        await page.locator(`main nav a[href="${href}"]`).click();
        await page.waitForFunction((selector) => {
          const top = document.querySelector(selector).getBoundingClientRect().top;
          return top >= document.querySelector("header").getBoundingClientRect().bottom - 1 && top < 180;
        }, href);
      }
      const table = page.getByRole("region", { name: "广告代理报价的五项费用核对", exact: true });
      if (width <= 390) {
        await table.scrollIntoViewIfNeeded();
        await table.focus();
        await page.keyboard.press("ArrowRight");
        await page.waitForFunction(() => document.activeElement.scrollLeft > 0);
      }
      if (width === 1440) {
        for (const pathname of content.localLinks) assert.equal((await context.request.get(new URL(pathname, base).href)).status(), 200, pathname);
        await page.goto(new URL("google-ads.html", base).href);
        assert.equal(await page.locator(`main a[href="${articlePath}"]`).count(), 1);
      }
      await page.goto(new URL(articlePath, base).href, { waitUntil: "networkidle" });
      if (width === 1440 || width === 390) {
        await page.screenshot({ path: path.join(output, `article-${width}.png`) });
        await page.locator('main nav a[href="#fees"]').click();
        await page.waitForFunction(() => document.querySelector("#fees").getBoundingClientRect().top < 180);
        await page.screenshot({ path: path.join(output, `fees-${width}.png`) });
      }
      await page.goto(new URL("articles.html", base).href, { waitUntil: "networkidle" });
      const card = page.locator("[data-article-card]").filter({ has: page.locator(`h3 a[href="${articlePath}"]`) });
      assert.equal(await card.isVisible(), true);
      assert.ok((await card.locator("small").textContent()).startsWith("2026-10-24"));
      await card.locator("img").scrollIntoViewIfNeeded();
      await card.locator("img").evaluate((image) => image.decode());
      assert.ok((await card.locator("img").getAttribute("src")).endsWith("review-thumb-v1.webp"));
      results.push({ width, ...content, anchorsPassed: true, listingPassed: true });
      await context.close();
      console.log(`Passed agency guide ${width}px`);
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, "browser.json"), JSON.stringify({ checkedAt: new Date().toISOString(), base: base.href, results, pageErrors: errors }, null, 2) + "\n");
  } finally { await browser.close(); }
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
