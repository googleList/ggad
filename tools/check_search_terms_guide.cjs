const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const base = new URL(process.argv[2] || "http://127.0.0.1:8780/");
const output = process.argv[3] || path.join(os.tmpdir(), "shumao-search-terms-check");
const articlePath = "articles/search-terms-optimization.html";

async function main() {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH });
  const results = [];
  const errors = [];
  try {
    for (const [width, javaScriptEnabled] of [[1440, true], [768, true], [390, true], [320, true], [1440, false], [390, false]]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, javaScriptEnabled, reducedMotion: "reduce" });
      const page = await context.newPage();
      page.setDefaultTimeout(15000);
      page.on("pageerror", (error) => errors.push(`${width}px/${javaScriptEnabled}: ${error.message}`));
      assert.equal((await page.goto(new URL(articlePath, base).href, { waitUntil: "networkidle", timeout: 45000 })).status(), 200);
      await page.waitForFunction(() => [...document.styleSheets].some((sheet) => sheet.href && sheet.href.includes("styles.css")));
      const content = await page.evaluate(() => {
        const main = document.querySelector("main");
        const schema = [...document.querySelectorAll('script[type="application/ld+json"]')]
          .map((node) => JSON.parse(node.textContent)).find((item) => item["@type"] === "Article");
        const image = main.querySelector(".article-cover");
        return {
          headline: main.querySelector("h1").textContent.trim(), schemaHeadline: schema.headline,
          canonical: document.querySelector('link[rel="canonical"]').href,
          published: schema.datePublished, modified: schema.dateModified, visibleModified: main.querySelector("time").dateTime,
          descriptions: [document.querySelector('meta[name="description"]').content,
            document.querySelector('meta[property="og:description"]').content,
            document.querySelector('meta[name="twitter:description"]').content, schema.description],
          cover: { src: image.currentSrc, loaded: image.complete && image.naturalWidth > 0,
            schema: schema.image, og: document.querySelector('meta[property="og:image"]').content,
            twitter: document.querySelector('meta[name="twitter:image"]').content,
            ratio: image.getBoundingClientRect().width / image.getBoundingClientRect().height },
          checks: main.querySelectorAll("[data-report-checks] > li").length,
          decisions: [...main.querySelectorAll("[data-term-decision]")].map((row) => row.dataset.termDecision),
          negatives: main.querySelectorAll("[data-negative-checks] > li").length,
          records: [...main.querySelectorAll("[data-review-record]")].map((row) => row.dataset.reviewRecord),
          faqCount: main.querySelectorAll("#questions h3").length,
          anchors: [...main.querySelectorAll("nav a")].map((link) => link.getAttribute("href")),
          ids: [...document.querySelectorAll("[id]")].map((node) => node.id),
          links: [...new Set([...main.querySelectorAll("a[href]")].filter((link) => link.origin === location.origin &&
            !link.getAttribute("href").startsWith("#")).map((link) => link.pathname + link.hash))],
          boundaries: ["每次转化费用不能算成 0 美元", "没有可靠关联就保留", "不是通用否定词库", "不保证广告展示", "不是客户结果或投放基准"]
            .map((text) => ({ text, present: main.textContent.includes(text) })),
          overflow: document.documentElement.scrollWidth > innerWidth + 1,
        };
      });
      assert.equal(content.headline, "Google Ads 搜索词报告怎么分析与加否定词");
      assert.equal(content.schemaHeadline, content.headline);
      assert.equal(content.canonical, "https://shumaojs.com/" + articlePath);
      assert.equal(content.published, "2026-09-11");
      assert.equal(content.modified, "2026-10-25T09:56:10+08:00");
      assert.equal(content.visibleModified, content.modified);
      assert.equal(new Set(content.descriptions).size, 1);
      assert.equal(content.cover.loaded, true);
      assert.ok(content.cover.src.endsWith(width <= 600 ? "review-thumb-v1.webp" : "review-v1.jpg"));
      assert.equal(content.cover.schema, content.cover.og);
      assert.equal(content.cover.schema, content.cover.twitter);
      assert.ok(Math.abs(content.cover.ratio - 16 / 9) < 0.01);
      assert.equal(content.checks, 4);
      assert.deepEqual(content.decisions, ["irrelevant", "ambiguous", "price", "spend", "qualified", "insufficient"]);
      assert.equal(content.negatives, 4);
      assert.deepEqual(content.records, ["exclude", "page", "observe"]);
      assert.equal(content.faqCount, 3);
      assert.equal(content.anchors.length, 6);
      assert.equal(new Set(content.ids).size, content.ids.length);
      assert.ok(content.boundaries.every((item) => item.present));
      assert.equal(content.overflow, false);
      const anchors = [];
      for (const href of content.anchors) {
        await page.locator(`main nav a[href="${href}"]`).click();
        await page.waitForFunction((selector) => {
          const top = document.querySelector(selector).getBoundingClientRect().top;
          const end = scrollY + innerHeight >= document.documentElement.scrollHeight - 2;
          return top >= document.querySelector("header").getBoundingClientRect().bottom - 1 &&
            (top < 180 || (end && top < innerHeight - 60));
        }, href);
        anchors.push(await page.evaluate((selector) => ({ selector,
          top: document.querySelector(selector).getBoundingClientRect().top,
          headerBottom: document.querySelector("header").getBoundingClientRect().bottom,
          atScrollEnd: scrollY + innerHeight >= document.documentElement.scrollHeight - 2,
        }), href));
      }
      if (width <= 390) {
        for (const name of ["六种搜索词处理情境", "搜索词变更复核记录示例"]) {
          const table = page.getByRole("region", { name, exact: true });
          await table.scrollIntoViewIfNeeded();
          await table.focus();
          await page.keyboard.press("ArrowRight");
          // Poll from Node: page timers can be disabled in no-JavaScript contexts.
          let scrolled = false;
          for (let attempt = 0; attempt < 30; attempt += 1) {
            scrolled = await table.evaluate((element) => document.activeElement === element && element.scrollLeft > 0);
            if (scrolled) break;
            await new Promise((resolve) => setTimeout(resolve, 50));
          }
          assert.equal(scrolled, true, `${name}: keyboard horizontal scroll`);
        }
      }
      if (width === 1440 && javaScriptEnabled) {
        for (const target of content.links) {
          const url = new URL(target, base);
          const response = await context.request.get(url.href);
          assert.equal(response.status(), 200, target);
          if (url.hash) assert.equal(await page.evaluate(({ html, id }) =>
            new DOMParser().parseFromString(html, "text/html").getElementById(id) !== null,
          { html: await response.text(), id: url.hash.slice(1) }), true, target);
        }
      }
      if (width === 1440 || width === 390) {
        await page.goto(new URL(articlePath, base).href, { waitUntil: "networkidle" });
        const suffix = javaScriptEnabled ? "js" : "nojs";
        await page.screenshot({ path: path.join(output, `article-${width}-${suffix}.png`) });
        await page.locator('main nav a[href="#term-decisions"]').click();
        await page.waitForFunction(() => document.querySelector("#term-decisions").getBoundingClientRect().top < 180);
        await page.screenshot({ path: path.join(output, `decisions-${width}-${suffix}.png`) });
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
      assert.ok((await card.locator("small").textContent()).startsWith("2026-10-25"));
      await card.locator("img").scrollIntoViewIfNeeded();
      await card.locator("img").evaluate((image) => image.decode());
      assert.ok((await card.locator("img").getAttribute("src")).endsWith("search-terms-review-thumb-v1.webp"));
      await card.locator("h3 a").click();
      assert.equal(new URL(page.url()).pathname, "/" + articlePath);
      results.push({ width, javaScriptEnabled, ...content, anchors, tableScrollPassed: width <= 390, listingPage, listingPassed: true });
      await context.close();
      console.log(`Passed search terms guide ${width}px/${javaScriptEnabled ? "JS" : "noJS"}`);
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, "browser.json"), JSON.stringify({ checkedAt: new Date().toISOString(), base: base.href, results, pageErrors: errors }, null, 2) + "\n");
  } finally { await browser.close(); }
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
