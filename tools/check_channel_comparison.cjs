const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const base = new URL(process.argv[2] || "http://127.0.0.1:8782/");
const output = process.argv[3] || path.join(os.tmpdir(), "shumao-channel-comparison");
const articlePath = "articles/google-ads-vs-meta-ads-guide.html";

async function main() {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH });
  const results = [], errors = [];
  try {
    for (const width of [1440, 768, 390, 320]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: "reduce" });
      const page = await context.newPage();
      page.setDefaultTimeout(15000);
      page.on("pageerror", (error) => errors.push(width + "px: " + error.message));
      assert.equal((await page.goto(new URL(articlePath, base).href, { waitUntil: "networkidle", timeout: 45000 })).status(), 200);
      const content = await page.evaluate(() => {
        const main = document.querySelector("main");
        const schema = [...document.querySelectorAll('script[type="application/ld+json"]')]
          .map((node) => JSON.parse(node.textContent)).find((item) => item["@type"] === "Article");
        const image = main.querySelector(".article-cover");
        return {
          headline: main.querySelector("h1").textContent.trim(), schemaHeadline: schema.headline,
          title: document.title, canonical: document.querySelector('link[rel="canonical"]').href,
          published: schema.datePublished, modified: schema.dateModified, visibleModified: main.querySelector("time").dateTime,
          descriptions: [document.querySelector('meta[name="description"]').content, schema.description,
            document.querySelector('meta[property="og:description"]').content, document.querySelector('meta[name="twitter:description"]').content],
          cover: { src: image.currentSrc, loaded: image.complete && image.naturalWidth > 0, schema: schema.image,
            og: document.querySelector('meta[property="og:image"]').content, twitter: document.querySelector('meta[name="twitter:image"]').content,
            ratio: image.getBoundingClientRect().width / image.getBoundingClientRect().height },
          dimensions: [...main.querySelectorAll("[data-channel-dimension]")].map((row) => row.dataset.channelDimension),
          scenarios: [...main.querySelectorAll("[data-project-scenario]")].map((node) => node.dataset.projectScenario),
          costRows: [...main.querySelectorAll("[data-cost-comparison]")].map((row) => ({ key: row.dataset.costComparison, text: row.textContent })),
          steps: main.querySelectorAll("[data-channel-test-steps] > li").length, faqCount: main.querySelectorAll("#questions h3").length,
          anchors: [...main.querySelectorAll("nav a")].map((link) => link.getAttribute("href")),
          ids: [...document.querySelectorAll("[id]")].map((node) => node.id),
          hypothetical: main.textContent.includes("下面全部是假设演算") && main.textContent.includes("A、B 不对应指定平台"),
          uncertainty: main.textContent.includes("小样本不足以证明长期优胜") && main.textContent.includes("不是零成本"),
          sources: main.querySelectorAll('a[href^="https://support.google.com/"], a[href^="https://about.fb.com/"]').length,
          localLinks: [...new Set([...main.querySelectorAll("a[href]")].filter((link) => link.origin === location.origin &&
            !link.getAttribute("href").startsWith("#")).map((link) => link.pathname + link.hash))],
          overflow: document.documentElement.scrollWidth > innerWidth + 1,
        };
      });
      assert.equal(content.headline, "Google Ads 和 Meta Ads 怎么选？投放场景对比");
      assert.equal(content.schemaHeadline, content.headline);
      assert.equal(content.title, content.headline + " | 昆明振润达商贸有限公司");
      assert.equal(content.canonical, "https://shumaojs.com/" + articlePath);
      assert.equal(content.published, "2026-09-11");
      assert.equal(content.modified, "2026-10-24T23:36:37+08:00");
      assert.equal(content.visibleModified, content.modified);
      assert.equal(new Set(content.descriptions).size, 1);
      assert.equal(content.cover.loaded, true);
      assert.ok(content.cover.src.endsWith(width <= 600 ? "evidence-thumb-v1.webp" : "evidence-v1.jpg"));
      assert.equal(content.cover.schema, content.cover.og);
      assert.equal(content.cover.schema, content.cover.twitter);
      assert.ok(Math.abs(content.cover.ratio - 16 / 9) < 0.01);
      assert.deepEqual(content.dimensions, ["demand", "assets", "destination", "measurement", "diagnostics", "constraints"]);
      assert.deepEqual(content.scenarios, ["industrial", "retail", "services"]);
      assert.deepEqual(content.costRows.map((row) => row.key), ["received", "raw-cpl", "qualified", "qualified-cpl"]);
      assert.ok(content.costRows[1].text.includes("600 ÷ 12 = 50") && content.costRows[1].text.includes("600 ÷ 30 = 20"));
      assert.ok(content.costRows[3].text.includes("600 ÷ 4 = 150") && content.costRows[3].text.includes("600 ÷ 3 = 200"));
      assert.equal(content.steps, 4);
      assert.equal(content.faqCount, 3);
      assert.equal(content.hypothetical, true);
      assert.equal(content.uncertainty, true);
      assert.equal(content.sources, 4);
      assert.equal(content.anchors.length, 6);
      assert.equal(new Set(content.ids).size, content.ids.length);
      assert.equal(content.overflow, false);
      for (const href of content.anchors) {
        await page.locator('main nav a[href="' + href + '"]').click();
        await page.waitForFunction((selector) => {
          const top = document.querySelector(selector).getBoundingClientRect().top;
          return top >= document.querySelector("header").getBoundingClientRect().bottom - 1 && top < 180;
        }, href);
      }
      if (width <= 390) {
        for (const label of ["六项广告渠道选择对照", "假设渠道线索成本演算"]) {
          const table = page.getByRole("region", { name: label, exact: true });
          await table.scrollIntoViewIfNeeded();
          await table.focus();
          await page.keyboard.press("ArrowRight");
          await page.waitForFunction(() => document.activeElement.scrollLeft > 0);
        }
      }
      if (width === 1440) {
        for (const destination of content.localLinks) {
          const url = new URL(destination, base);
          const response = await context.request.get(url.href);
          assert.equal(response.status(), 200, destination);
          if (url.hash) assert.equal(await page.evaluate(({ html, id }) =>
            !!new DOMParser().parseFromString(html, "text/html").getElementById(id),
          { html: await response.text(), id: decodeURIComponent(url.hash.slice(1)) }), true, destination);
        }
      }
      if (width === 1440 || width === 390) {
        await page.goto(new URL(articlePath, base).href, { waitUntil: "networkidle" });
        await page.screenshot({ path: path.join(output, "article-" + width + ".png") });
        await page.locator('main nav a[href="#measurement"]').click();
        await page.waitForFunction(() => document.querySelector("#measurement").getBoundingClientRect().top < 180);
        await page.screenshot({ path: path.join(output, "measurement-" + width + ".png") });
      }
      await page.goto(new URL("articles.html", base).href, { waitUntil: "networkidle" });
      await page.locator('[data-article-category-button][data-article-category="sem"]').click();
      const card = page.locator("[data-article-card]").filter({ has: page.locator('h3 a[href="' + articlePath + '"]') });
      let listingPage = 1;
      while (!await card.isVisible()) {
        assert.ok(listingPage < 7);
        const next = page.locator(".pagination button").last();
        assert.equal(await next.isDisabled(), false);
        await next.click();
        listingPage += 1;
      }
      assert.ok((await card.locator("small").textContent()).startsWith("2026-10-24"));
      await card.locator("img").scrollIntoViewIfNeeded();
      await card.locator("img").evaluate((image) => image.decode());
      assert.ok((await card.locator("img").getAttribute("src")).endsWith("evidence-thumb-v1.webp"));
      if (width === 1440 || width === 390) await page.screenshot({ path: path.join(output, "listing-" + width + ".png") });
      results.push({ width, ...content, anchorsPassed: true, listingPage, listingPassed: true });
      await context.close();
      console.log("Passed channel comparison " + width + "px");
    }
    const context = await browser.newContext({ viewport: { width: 390, height: 900 }, javaScriptEnabled: false });
    const page = await context.newPage();
    await page.goto(new URL(articlePath, base).href, { waitUntil: "load", timeout: 45000 });
    assert.equal(await page.locator("main nav a:visible").count(), 6);
    assert.equal(await page.locator("[data-channel-dimension]").count(), 6);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
    assert.equal(await page.locator(".article-cover").evaluate((image) => image.complete && image.naturalWidth > 0), true);
    results.push({ width: 390, javascript: false, anchorsVisible: 6, comparisonRows: 6, imageLoaded: true, noOverflow: true });
    await context.close();
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, "browser.json"), JSON.stringify({ checkedAt: new Date().toISOString(), base: base.href, results, pageErrors: errors }, null, 2) + "\n");
  } finally { await browser.close(); }
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
