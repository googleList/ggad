const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");

const base = new URL(process.argv[2] || "http://127.0.0.1:8765/");
const output = process.argv[3] || path.join(os.tmpdir(), "shumao-article-index-check");

async function visibleUrls(page) {
  return page.locator("[data-article-card]:not([hidden]) h3 a")
    .evaluateAll((links) => links.map((link) => link.getAttribute("href")));
}

async function sourceSnapshot(page, html) {
  return page.evaluate((source) => {
    const doc = new DOMParser().parseFromString(source, "text/html");
    const cards = [...doc.querySelectorAll("[data-article-card]")].map((card) => ({
      url: card.querySelector("h3 a").getAttribute("href"),
      name: card.querySelector("h3").textContent.trim(),
      category: card.dataset.articleCategory,
      priority: Number(card.dataset.searchPriority || 0), hidden: card.hidden,
    }));
    const schema = [...doc.querySelectorAll('script[type="application/ld+json"]')]
      .map((script) => JSON.parse(script.textContent)).find((block) => block["@type"] === "CollectionPage");
    return { cards, items: schema.mainEntity.itemListElement };
  }, html);
}

async function main() {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH });
  const results = [];
  const errors = [];
  try {
    for (const width of [1440, 768, 390, 320]) {
      const context = await browser.newContext({ viewport: { width, height: 900 } });
      const page = await context.newPage();
      page.setDefaultTimeout(15000);
      page.setDefaultNavigationTimeout(45000);
      page.on("pageerror", (error) => errors.push(`${width}px: ${error.message}`));
      const response = await page.goto(new URL("articles.html", base).href, { waitUntil: "domcontentloaded" });
      assert.equal(response.status(), 200);
      const source = await sourceSnapshot(page, await response.text());
      assert.ok(source.cards.length > 6);
      assert.ok(source.cards.every((card) => !card.hidden));
      assert.deepEqual(source.cards.map((card) => card.priority),
        source.cards.map((card) => card.priority).sort((a, b) => b - a));
      assert.deepEqual(source.items.map((item) => ({ url: new URL(item.url).pathname.slice(1), name: item.name })),
        source.cards.map(({ url, name }) => ({ url, name })));
      await page.waitForFunction(() => document.documentElement.classList.contains("article-index-ready"));
      assert.deepEqual(await visibleUrls(page), source.cards.slice(0, 6).map((card) => card.url));
      assert.equal(await page.locator('.pagination button[aria-current="page"]').textContent(), "1");

      const categories = await page.locator("[data-article-category-button]").evaluateAll((buttons) =>
        buttons.map((button) => button.dataset.articleCategory));
      const categoryCounts = {};
      const categorySummaries = {};
      for (const category of categories) {
        await page.locator(`[data-article-category-button][data-article-category="${category}"]`).click();
        const summary = await page.locator(`[data-article-category-button][data-article-category="${category}"]`).getAttribute("data-article-summary");
        assert.ok(summary && summary.length > 30);
        assert.equal(await page.locator("p[data-article-summary]").textContent(), summary);
        assert.equal(await page.locator('[data-article-category-button][aria-pressed="true"]').count(), 1);
        categorySummaries[category] = summary;
        const expected = source.cards.filter((card) => category === "all" || card.category === category);
        const collected = [];
        let pageNumber = 1;
        while (true) {
          collected.push(...await visibleUrls(page));
          assert.equal(await page.locator('.pagination button[aria-current="page"]').textContent(), String(pageNumber));
          const next = page.locator(".pagination button").last();
          if (await next.isDisabled()) break;
          await next.click();
          pageNumber += 1;
          assert.ok(pageNumber <= Math.ceil(expected.length / 6));
        }
        assert.deepEqual(collected, expected.map((card) => card.url));
        assert.equal(new Set(collected).size, collected.length);
        if (pageNumber > 1) {
          await page.locator(".pagination button").first().click();
          assert.equal(await page.locator('.pagination button[aria-current="page"]').textContent(), String(pageNumber - 1));
        }
        categoryCounts[category] = expected.length;
      }
      await page.locator('[data-article-category-button][data-article-category="all"]').click();
      for (const image of await page.locator("[data-article-card]:not([hidden]) img").all()) {
        await image.scrollIntoViewIfNeeded();
        await image.evaluate((node) => Promise.race([
          node.decode(), new Promise((_, reject) => setTimeout(() => reject(new Error("Image decode timed out")), 10000)),
        ]));
      }
      const layout = await page.evaluate(() => {
        const cards = [...document.querySelectorAll("[data-article-card]:not([hidden])")];
        const top = cards[0].getBoundingClientRect().top;
        return {
          overflow: document.documentElement.scrollWidth > innerWidth + 1,
          firstRowCards: cards.filter((card) => Math.abs(card.getBoundingClientRect().top - top) < 2).length,
          imagesLoaded: cards.every((card) => card.querySelector("img").naturalWidth > 0),
        };
      });
      assert.equal(layout.overflow, false);
      assert.equal(layout.imagesLoaded, true);
      assert.equal(layout.firstRowCards, width >= 1100 ? 3 : width >= 768 ? 2 : 1);
      if (width === 1440 || width === 390) {
        await page.evaluate(() => scrollTo(0, 0));
        await page.screenshot({ path: path.join(output, `articles-${width}.png`), fullPage: true });
      }
      assert.equal(new Set(Object.values(categorySummaries)).size, categories.length);
      results.push({ width, javascript: true, categories: categoryCounts, categorySummaries, ...layout, passed: true });
      console.log(`Passed ${width}px categories, pagination and images`);
      await context.close();
    }
    for (const width of [1440, 390]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, javaScriptEnabled: false });
      const page = await context.newPage();
      await page.route("**/styles.css", async (route) => {
        await new Promise((resolve) => setTimeout(resolve, 250));
        await route.continue();
      });
      await page.goto(new URL("articles.html", base).href, { waitUntil: "load", timeout: 45000 });
      await page.waitForFunction(() => [...document.styleSheets].some((sheet) =>
        sheet.href?.endsWith("/styles.css") && sheet.cssRules.length > 0));
      const count = await page.locator("[data-article-card]").count();
      assert.equal((await visibleUrls(page)).length, count);
      assert.equal(await page.locator("[data-article-card]:visible").count(), count);
      assert.equal(await page.locator(".category-tabs").isVisible(), false);
      assert.equal(await page.locator(".pagination").isVisible(), false);
      assert.equal(await page.locator("[data-article-status]").isVisible(), false);
      assert.ok((await page.locator("p[data-article-summary]").textContent()).includes("自然搜索"));
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
      results.push({ width, javascript: false, visibleCards: count, inactiveControlsHidden: true,
        delayedStylesheetRegression: true, stylesheetReady: true, passed: true });
      await context.close();
    }
    assert.deepEqual(errors, []);
    const report = { checkedAt: new Date().toISOString(), base: base.href, results, pageErrors: errors };
    fs.writeFileSync(path.join(output, "browser.json"), JSON.stringify(report, null, 2) + "\n");
    console.log(JSON.stringify(report, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch((error) => { console.error(error); process.exitCode = 1; });
