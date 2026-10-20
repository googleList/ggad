const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");

const base = new URL(process.argv[2] || "http://127.0.0.1:8765/");
const output = process.argv[3] || path.join(os.tmpdir(), "shumao-setup-guide-check");

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
      page.setDefaultNavigationTimeout(45000);
      page.on("pageerror", (error) => errors.push(`${width}px: ${error.message}`));
      const response = await page.goto(new URL("articles/google-ads-basics.html", base).href,
        { waitUntil: "domcontentloaded" });
      assert.equal(response.status(), 200);
      const content = await page.evaluate(() => {
        const main = document.querySelector("main");
        const article = [...document.querySelectorAll('script[type="application/ld+json"]')]
          .map((script) => JSON.parse(script.textContent)).find((item) => item["@type"] === "Article");
        return {
          title: document.querySelector("h1").textContent.trim(), headline: article.headline,
          modified: article.dateModified, published: article.datePublished,
          visibleModified: document.querySelector("time").dateTime,
          ids: [...main.querySelectorAll("[id]")].map((node) => node.id),
          anchors: [...main.querySelectorAll('a[href^="#"]')].map((node) => node.getAttribute("href")),
          localLinks: [...new Set([...main.querySelectorAll('a[href]')]
            .filter((link) => link.origin === location.origin && !link.getAttribute("href").startsWith("#"))
            .map((link) => link.pathname))],
          setupSteps: document.querySelectorAll("#setup ol > li").length,
          preparationRows: document.querySelectorAll("#preparation tbody tr").length,
          overflow: document.documentElement.scrollWidth > innerWidth + 1,
        };
      });
      assert.equal(content.title, content.headline);
      assert.equal(content.modified, "2026-10-20T16:21:48+08:00");
      assert.equal(content.visibleModified, content.modified);
      assert.equal(content.published, "2026-09-11");
      assert.equal(content.setupSteps, 6);
      assert.equal(content.preparationRows, 6);
      assert.equal(content.overflow, false);
      assert.equal(new Set(content.ids).size, content.ids.length);
      assert.equal(content.anchors.length, 6);
      for (const href of content.anchors) {
        assert.ok(content.ids.includes(href.slice(1)));
        await page.locator(`main nav a[href="${href}"]`).click();
        await page.waitForFunction((id) => {
          const target = document.querySelector(id);
          const header = document.querySelector("header");
          return target.getBoundingClientRect().top >= header.getBoundingClientRect().bottom - 1
            && target.getBoundingClientRect().top < 180;
        }, href);
      }
      const region = page.locator(".article-table-wrap");
      await region.scrollIntoViewIfNeeded();
      const scrollable = await region.evaluate((node) => node.scrollWidth > node.clientWidth);
      if (width <= 390) {
        assert.equal(scrollable, true);
        await region.focus();
        await page.keyboard.press("ArrowRight");
        await page.waitForFunction(() => document.querySelector(".article-table-wrap").scrollLeft > 0);
      }
      if (width === 1440) {
        for (const pathname of content.localLinks) {
          const linked = await context.request.get(new URL(pathname, base).href);
          assert.equal(linked.status(), 200, pathname);
        }
      }
      await page.evaluate(() => scrollTo(0, 0));
      if (width === 1440 || width === 390) {
        await page.screenshot({ path: path.join(output, `guide-${width}.png`) });
        await page.locator("#preparation").scrollIntoViewIfNeeded();
        await page.screenshot({ path: path.join(output, `checklist-${width}.png`) });
      }
      results.push({ width, ...content, tableKeyboardScrollPassed: width <= 390 ? true : null, passed: true });
      console.log(`Passed ${width}px guide content, anchors and table layout`);
      await context.close();
    }
    assert.deepEqual(errors, []);
    const report = { checkedAt: new Date().toISOString(), base: base.href, results, pageErrors: errors };
    fs.writeFileSync(path.join(output, "browser.json"), JSON.stringify(report, null, 2) + "\n");
  } finally {
    await browser.close();
  }
}

main().catch((error) => { console.error(error); process.exitCode = 1; });
