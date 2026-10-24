const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const base = new URL(process.argv[2] || "http://127.0.0.1:8779/");
const output = process.argv[3] || path.join(os.tmpdir(), "shumao-landing-guide-check");
const articlePath = "articles/landing-page-checklist.html";

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
          description: document.querySelector('meta[name="description"]').content,
          schemaDescription: schema.description,
          cover: { src: image.currentSrc, loaded: image.complete && image.naturalWidth > 0,
            schema: schema.image, og: document.querySelector('meta[property="og:image"]').content,
            twitter: document.querySelector('meta[name="twitter:image"]').content,
            renderedRatio: image.getBoundingClientRect().width / image.getBoundingClientRect().height },
          checks: [...main.querySelectorAll("[data-launch-check]")].map((row) => row.querySelector("th").textContent.trim()),
          testCases: [...main.querySelectorAll("[data-form-test]")].map((row) => row.dataset.formTest),
          measurementLevels: [...main.querySelectorAll("[data-measurement-levels] li")].map((li) => li.textContent),
          priorities: main.querySelectorAll("[data-release-priorities] li").length,
          faqCount: main.querySelectorAll("#questions h3").length,
          anchors: [...main.querySelectorAll("nav a")].map((link) => link.getAttribute("href")),
          ids: [...document.querySelectorAll("[id]")].map((node) => node.id),
          hypothetical: main.querySelector("#measurement").textContent.includes("教学假设"),
          reviewBoundary: main.textContent.includes("不是 Google 审核认证"),
          localLinks: [...new Set([...main.querySelectorAll("a[href]")].filter((link) => link.origin === location.origin &&
            !link.getAttribute("href").startsWith("#")).map((link) => link.pathname))],
          overflow: document.documentElement.scrollWidth > innerWidth + 1,
        };
      });
      assert.equal(content.headline, "外贸独立站投放前落地页检查清单");
      assert.equal(content.schemaHeadline, content.headline);
      assert.equal(content.canonical, "https://shumaojs.com/articles/landing-page-checklist.html");
      assert.equal(content.published, "2026-09-11");
      assert.equal(content.modified, "2026-10-24T16:33:43+08:00");
      assert.equal(content.visibleModified, content.modified);
      assert.equal(content.description, content.schemaDescription);
      assert.equal(content.cover.loaded, true);
      assert.ok(content.cover.src.endsWith(width <= 600 ? "preflight-thumb-v1.webp" : "preflight-v1.jpg"));
      assert.equal(content.cover.schema, content.cover.og);
      assert.equal(content.cover.schema, content.cover.twitter);
      assert.ok(Math.abs(content.cover.renderedRatio - 16 / 9) < 0.01);
      assert.equal(content.checks.length, 8);
      content.checks.forEach((heading, index) => assert.ok(heading.startsWith(`${index + 1}.`)));
      assert.deepEqual(content.testCases, ["invalid", "failure", "success", "duplicate"]);
      assert.equal(content.measurementLevels.length, 3);
      assert.ok(content.measurementLevels[0].startsWith("意向动作"));
      assert.ok(content.measurementLevels[1].startsWith("真实询盘"));
      assert.ok(content.measurementLevels[2].startsWith("有效线索"));
      assert.equal(content.priorities, 3);
      assert.equal(content.faqCount, 3);
      assert.equal(content.hypothetical, true);
      assert.equal(content.reviewBoundary, true);
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
      if (width <= 390) {
        for (const label of ["落地页八项上线前验收清单", "询盘表单四种测试情境"]) {
          const table = page.getByRole("region", { name: label, exact: true });
          await table.scrollIntoViewIfNeeded();
          await table.focus();
          await page.keyboard.press("ArrowRight");
          await page.waitForFunction(() => document.activeElement.scrollLeft > 0);
        }
      }
      if (width === 1440) {
        for (const pathname of content.localLinks) assert.equal((await context.request.get(new URL(pathname, base).href)).status(), 200, pathname);
        await page.goto(new URL("google-ads.html", base).href, { waitUntil: "networkidle" });
        assert.equal(await page.locator(`main a[href="${articlePath}"]`).count(), 1);
      }
      if (width === 1440 || width === 390) {
        await page.goto(new URL(articlePath, base).href, { waitUntil: "networkidle" });
        await page.screenshot({ path: path.join(output, `article-${width}.png`) });
        await page.locator('main nav a[href="#form-tests"]').click();
        await page.waitForFunction(() => document.querySelector("#form-tests").getBoundingClientRect().top < 180);
        await page.screenshot({ path: path.join(output, `form-tests-${width}.png`) });
      }
      await page.goto(new URL("articles.html", base).href, { waitUntil: "networkidle" });
      await page.locator('[data-article-category-button][data-article-category="website"]').click();
      const card = page.locator("[data-article-card]").filter({ has: page.locator(`h3 a[href="${articlePath}"]`) });
      assert.equal(await card.isVisible(), true);
      assert.ok((await card.locator("small").textContent()).startsWith("2026-10-24"));
      await card.locator("img").scrollIntoViewIfNeeded();
      await card.locator("img").evaluate((image) => image.decode());
      assert.ok((await card.locator("img").getAttribute("src")).endsWith("preflight-thumb-v1.webp"));
      if (width === 1440 || width === 390) await page.screenshot({ path: path.join(output, `listing-${width}.png`) });
      results.push({ width, ...content, anchorsPassed: true, listingPassed: true });
      await context.close();
      console.log(`Passed landing guide ${width}px`);
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, "browser.json"), JSON.stringify({ checkedAt: new Date().toISOString(), base: base.href, results, pageErrors: errors }, null, 2) + "\n");
  } finally { await browser.close(); }
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
