const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const base = new URL(process.argv[2] || "http://127.0.0.1:8799/");
const output = process.argv[3];
assert.ok(output, "Provide a separate evidence directory");
const articlePath = "articles/performance-max-basics.html";

async function main() {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH, headless: true });
  const results = [], errors = [];
  try {
    for (const [width, javaScriptEnabled] of [[1440, true], [768, true], [390, true], [320, true], [1440, false], [390, false]]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, javaScriptEnabled, reducedMotion: "reduce" });
      const page = await context.newPage();
      page.setDefaultTimeout(15000);
      page.setDefaultNavigationTimeout(45000);
      page.on("pageerror", error => errors.push(`${width}/${javaScriptEnabled}: ${error.message}`));
      assert.equal((await page.goto(new URL(articlePath, base).href, { waitUntil: "domcontentloaded" })).status(), 200);
      let stylesheetReady = false;
      for (let attempt = 0; attempt < 100; attempt += 1) {
        stylesheetReady = await page.evaluate(() => [...document.styleSheets].some(sheet => sheet.href && new URL(sheet.href).pathname.endsWith("/styles.css")));
        if (stylesheetReady) break;
        await new Promise(resolve => setTimeout(resolve, 50));
      }
      assert.equal(stylesheetReady, true, "Site stylesheet must load before layout acceptance");
      await page.locator(".article-cover").evaluate(image => image.decode());
      const content = await page.evaluate(() => {
        const main = document.querySelector("main");
        const schema = [...document.querySelectorAll('script[type="application/ld+json"]')].map(n => JSON.parse(n.textContent)).find(n => n["@type"] === "Article");
        const image = main.querySelector(".article-cover");
        return {
          title: document.title, headline: main.querySelector("h1").textContent, schema,
          canonical: document.querySelector('link[rel="canonical"]').href, modified: main.querySelector("time").dateTime,
          descriptions: [schema.description, document.querySelector('meta[name="description"]').content,
            document.querySelector('meta[property="og:description"]').content, document.querySelector('meta[name="twitter:description"]').content],
          images: [schema.image, document.querySelector('meta[property="og:image"]').content, document.querySelector('meta[name="twitter:image"]').content],
          cover: { loaded: image.naturalWidth > 0, src: image.currentSrc, ratio: image.getBoundingClientRect().width / image.getBoundingClientRect().height },
          controls: [...main.querySelectorAll("[data-pmax-control]")].map(n => n.dataset.pmaxControl),
          examples: [...main.querySelectorAll("[data-pmax-example]")].map(n => n.dataset.pmaxExample),
          records: main.querySelectorAll("[data-pmax-records] > li").length, launchChecks: main.querySelectorAll("#launch ol > li").length,
          anchors: [...main.querySelectorAll("nav a")].map(n => n.getAttribute("href")),
          ids: [...document.querySelectorAll("[id]")].map(n => n.id),
          links: [...new Set([...main.querySelectorAll("a[href]")].filter(n => n.origin === location.origin && !n.getAttribute("href").startsWith("#")).map(n => n.pathname + n.hash))],
          overflow: document.documentElement.scrollWidth > innerWidth + 1,
        };
      });
      assert.equal(content.headline, "Performance Max 怎么投？适用条件与上线清单");
      assert.equal(content.schema.headline, content.headline);
      assert.equal(content.title, content.headline + " | 振润达");
      assert.equal(content.canonical, "https://shumaojs.com/" + articlePath);
      assert.equal(content.schema.datePublished, "2026-09-11");
      assert.equal(content.modified, "2026-10-27T16:35:12+08:00");
      assert.equal(content.schema.dateModified, content.modified);
      assert.equal(new Set(content.descriptions).size, 1);
      assert.equal(new Set(content.images).size, 1);
      assert.ok(content.images[0].endsWith("pmax-controls-plan-v1.jpg"));
      assert.ok(content.cover.loaded);
      assert.ok(content.cover.src.endsWith(width <= 600 ? "plan-thumb-v1.webp" : "plan-v1.jpg"));
      assert.ok(Math.abs(content.cover.ratio - 16 / 9) < 0.01);
      assert.deepEqual(content.controls, ["campaign", "goals", "creative", "signals", "urls", "products"]);
      assert.deepEqual(content.examples, ["geography", "destination", "lead-quality"]);
      assert.equal(content.records, 4);
      assert.equal(content.launchChecks, 5);
      assert.equal(content.overflow, false);
      assert.equal(new Set(content.ids).size, content.ids.length);
      assert.equal(content.anchors.length, 7);
      for (const href of content.anchors) {
        await page.locator(`main nav a[href="${href}"]`).click();
        const position = await page.locator(href).evaluate(n => ({ top: n.getBoundingClientRect().top,
          headingBottom: n.querySelector("h2").getBoundingClientRect().bottom,
          header: document.querySelector("header").getBoundingClientRect().bottom,
          viewport: innerHeight, bottomDistance: document.documentElement.scrollHeight - innerHeight - scrollY }));
        assert.ok(position.top >= position.header - 1, href);
        assert.ok(position.top < 190 || (position.bottomDistance <= 1 && position.headingBottom < position.viewport), href);
      }
      if (width <= 390) {
        const region = page.getByRole("region", { name: "PMax 六项配置、作用范围与误读", exact: true });
        await region.scrollIntoViewIfNeeded();
        await region.focus();
        await page.keyboard.press("ArrowRight");
        let scrolled = false;
        for (let attempt = 0; attempt < 30; attempt += 1) {
          scrolled = await region.evaluate(n => document.activeElement === n && n.scrollLeft > 0);
          if (scrolled) break;
          await new Promise(resolve => setTimeout(resolve, 50));
        }
        assert.equal(scrolled, true);
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
        await page.goto(new URL(articlePath, base).href, { waitUntil: "domcontentloaded" });
        await page.locator(".article-cover").evaluate(image => image.decode());
        const suffix = `${width}-${javaScriptEnabled ? "js" : "nojs"}`;
        await page.screenshot({ path: path.join(output, `article-${suffix}.png`) });
        await page.locator('main nav a[href="#control-scope"]').click();
        await page.screenshot({ path: path.join(output, `controls-${suffix}.png`) });
      }
      await page.goto(new URL("articles.html", base).href, { waitUntil: "domcontentloaded" });
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
      assert.ok((await card.locator("small").textContent()).startsWith("2026-10-27"));
      await card.locator("img").scrollIntoViewIfNeeded();
      await card.locator("img").evaluate(image => image.decode());
      assert.ok((await card.locator("img").getAttribute("src")).endsWith("pmax-controls-plan-thumb-v1.webp"));
      await card.locator("h3 a").click();
      assert.equal(new URL(page.url()).pathname, "/" + articlePath);
      results.push({ width, javaScriptEnabled, stylesheetReady, ...content, listingPage, listingJourneyPassed: true });
      console.log(`Passed PMax guide ${width}px/${javaScriptEnabled ? "JS" : "noJS"}`);
      await context.close();
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, "browser.json"), JSON.stringify({ checkedAt: new Date().toISOString(), base: base.href, results, pageErrors: errors }, null, 2) + "\n");
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
