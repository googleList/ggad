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
    for (const [width, javaScriptEnabled] of [[1440, true], [768, true], [390, true], [320, true], [1440, false], [390, false]]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, javaScriptEnabled, reducedMotion: "reduce" });
      const page = await context.newPage();
      page.setDefaultTimeout(15000);
      page.setDefaultNavigationTimeout(45000);
      page.on("pageerror", (error) => errors.push(`${width}px: ${error.message}`));
      const response = await page.goto(new URL("articles/google-ads-basics.html", base).href,
        { waitUntil: "domcontentloaded" });
      assert.equal(response.status(), 200);
      await page.locator(".article-cover").evaluate((image) => image.decode());
      const content = await page.evaluate(() => {
        const main = document.querySelector("main");
        const article = [...document.querySelectorAll('script[type="application/ld+json"]')]
          .map((script) => JSON.parse(script.textContent)).find((item) => item["@type"] === "Article");
        return {
          title: document.querySelector("h1").textContent.trim(), headline: article.headline,
          modified: article.dateModified, published: article.datePublished,
          visibleModified: document.querySelector("time").dateTime,
          canonical: document.querySelector('link[rel="canonical"]').href,
          descriptions: [article.description, document.querySelector('meta[name="description"]').content,
            document.querySelector('meta[property="og:description"]').content, document.querySelector('meta[name="twitter:description"]').content],
          socialImages: [article.image, document.querySelector('meta[property="og:image"]').content,
            document.querySelector('meta[name="twitter:image"]').content],
          image: { src: main.querySelector(".article-cover").currentSrc,
            loaded: main.querySelector(".article-cover").naturalWidth > 0,
            ratio: main.querySelector(".article-cover").getBoundingClientRect().width / main.querySelector(".article-cover").getBoundingClientRect().height },
          checks: [...main.querySelectorAll("[data-setup-check]")].map((node) => node.dataset.setupCheck),
          examples: [...main.querySelectorAll("[data-setup-example]")].map((node) => node.dataset.setupExample),
          reviewRecords: main.querySelectorAll("[data-setup-review-records] > li").length,
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
      assert.equal(content.title, "谷歌广告开户流程：账户准备与投放入门");
      assert.equal(content.canonical, "https://shumaojs.com/articles/google-ads-basics.html");
      assert.equal(content.modified, "2026-10-27T15:41:01+08:00");
      assert.equal(content.visibleModified, content.modified);
      assert.equal(content.published, "2026-09-11");
      assert.equal(content.setupSteps, 6);
      assert.equal(content.preparationRows, 6);
      assert.deepEqual(content.checks, ["delivery", "measurement", "intent", "maturity", "economics"]);
      assert.deepEqual(content.examples, ["failure", "irrelevant", "unknown"]);
      assert.equal(content.reviewRecords, 4);
      assert.equal(new Set(content.descriptions).size, 1);
      assert.equal(new Set(content.socialImages).size, 1);
      assert.ok(content.socialImages[0].endsWith("account-setup-readiness-v1.jpg"));
      assert.equal(content.image.loaded, true);
      assert.ok(content.image.src.endsWith(width <= 600 ? "readiness-thumb-v1.webp" : "readiness-v1.jpg"));
      assert.ok(Math.abs(content.image.ratio - 16 / 9) < 0.01);
      assert.equal(content.overflow, false);
      assert.equal(new Set(content.ids).size, content.ids.length);
      assert.equal(content.anchors.length, 8);
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
      if (width <= 390) {
        for (const name of ["Google Ads 开户与首次投放准备清单", "首次投放的五项证据与下一步"]) {
          const region = page.getByRole("region", { name, exact: true });
          await region.scrollIntoViewIfNeeded();
          assert.equal(await region.evaluate((node) => node.scrollWidth > node.clientWidth), true);
          await region.focus();
          await page.keyboard.press("ArrowRight");
          let scrolled = false;
          for (let attempt = 0; attempt < 30; attempt += 1) {
            scrolled = await region.evaluate((node) => document.activeElement === node && node.scrollLeft > 0);
            if (scrolled) break;
            await new Promise((resolve) => setTimeout(resolve, 50));
          }
          assert.equal(scrolled, true, name);
        }
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
      if (width === 1440) {
        for (const pathname of content.localLinks) {
          const linked = await context.request.get(new URL(pathname, base).href);
          assert.equal(linked.status(), 200, pathname);
        }
      }
      await page.evaluate(() => scrollTo(0, 0));
      if (width === 1440 || width === 390) {
        const suffix = `${width}-${javaScriptEnabled ? "js" : "nojs"}`;
        await page.screenshot({ path: path.join(output, `guide-${suffix}.png`) });
        await page.locator('main nav a[href="#first-review"]').click();
        await page.screenshot({ path: path.join(output, `checklist-${suffix}.png`) });
        await page.locator('main nav a[href="#review-examples"]').click();
        await page.screenshot({ path: path.join(output, `examples-${suffix}.png`) });
      }
      await page.goto(new URL("articles.html", base).href, { waitUntil: "domcontentloaded" });
      if (javaScriptEnabled) await page.locator('[data-article-category-button][data-article-category="sem"]').click();
      const card = page.locator("[data-article-card]").filter({ has: page.locator('h3 a[href="articles/google-ads-basics.html"]') });
      assert.equal(await card.isVisible(), true);
      assert.ok((await card.locator("small").textContent()).startsWith("2026-10-27"));
      await card.locator("img").scrollIntoViewIfNeeded();
      await card.locator("img").evaluate((image) => image.decode());
      assert.ok((await card.locator("img").getAttribute("src")).endsWith("account-setup-readiness-thumb-v1.webp"));
      await card.locator("h3 a").click();
      assert.equal(new URL(page.url()).pathname, "/articles/google-ads-basics.html");
      results.push({ width, javaScriptEnabled, ...content, tableKeyboardScrollPassed: width <= 390 ? true : null, listingJourneyPassed: true, passed: true });
      console.log(`Passed ${width}px/${javaScriptEnabled ? "JS" : "noJS"} guide content, anchors, tables, image and listing journey`);
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
