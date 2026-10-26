const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const base = new URL(process.argv[2] || "http://127.0.0.1:8794/");
const output = process.argv[3] || path.join(os.tmpdir(), "shumao-us-audit-check");
const articlePath = "articles/google-ads-account-audit-usa.html";

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
      page.on("pageerror", (error) => errors.push(`${width}/${javaScriptEnabled}: ${error.message}`));
      assert.equal((await page.goto(new URL(articlePath, base).href, { waitUntil: "networkidle", timeout: 45000 })).status(), 200);
      const content = await page.evaluate(() => {
        const main = document.querySelector("main");
        const schema = [...document.querySelectorAll('script[type="application/ld+json"]')]
          .map((node) => JSON.parse(node.textContent)).find((item) => item["@type"] === "Article");
        const image = main.querySelector(".article-cover");
        return {
          title: document.title, headline: main.querySelector("h1").textContent.trim(), schemaHeadline: schema.headline,
          canonical: document.querySelector('link[rel="canonical"]').href,
          alternate: document.querySelector('link[hreflang="zh-Hant-HK"]').href,
          published: schema.datePublished, modified: schema.dateModified, visibleModified: main.querySelector("time").dateTime,
          descriptions: [document.querySelector('meta[name="description"]').content,
            document.querySelector('meta[property="og:description"]').content,
            document.querySelector('meta[name="twitter:description"]').content, schema.description],
          cover: { src: image.currentSrc, loaded: image.complete && image.naturalWidth > 0,
            schema: schema.image, og: document.querySelector('meta[property="og:image"]').content,
            twitter: document.querySelector('meta[name="twitter:image"]').content,
            ratio: image.getBoundingClientRect().width / image.getBoundingClientRect().height },
          checks: main.querySelectorAll("[data-baseline-checks] > li").length,
          locations: main.querySelectorAll("[data-location-checks] > li").length,
          decisions: [...main.querySelectorAll("[data-audit-decision]")].map((row) => row.dataset.auditDecision),
          math: main.querySelector("[data-audit-math]").textContent,
          boundaries: ["Source and optimization role are not interchangeable", "custom goal", "not checked",
            "qualification is unknown, not zero", "not a complete traffic census", "not automatically wasted spend",
            "Do not automatically change every campaign to Presence", "not findings in your account"]
            .map((text) => ({ text, present: main.textContent.includes(text) })),
          anchors: [...main.querySelectorAll("nav a")].map((link) => link.getAttribute("href")),
          ids: [...document.querySelectorAll("[id]")].map((node) => node.id),
          links: [...new Set([...main.querySelectorAll("a[href]")].filter((link) => link.origin === location.origin &&
            !link.getAttribute("href").startsWith("#")).map((link) => link.pathname + link.hash))],
          overflow: document.documentElement.scrollWidth > innerWidth + 1,
        };
      });
      assert.equal(content.title, "Google Ads Account Audit Checklist for US Businesses");
      assert.equal(content.headline, "Google Ads account audit checklist for US businesses");
      assert.equal(content.schemaHeadline.toLowerCase(), content.headline.toLowerCase());
      assert.equal(content.canonical, "https://shumaojs.com/" + articlePath);
      assert.equal(content.alternate, "https://shumaojs.com/articles/google-ads-account-audit-hong-kong.html");
      assert.equal(content.published, "2026-09-28");
      assert.equal(content.modified, "2026-10-26T12:05:14+08:00");
      assert.equal(content.visibleModified, content.modified);
      assert.equal(new Set(content.descriptions).size, 1);
      assert.equal(content.cover.loaded, true);
      assert.ok(content.cover.src.endsWith(width <= 600 ? "evidence-thumb-v1.webp" : "evidence-v1.jpg"));
      assert.equal(content.cover.schema, content.cover.og);
      assert.equal(content.cover.schema, content.cover.twitter);
      assert.ok(Math.abs(content.cover.ratio - 16 / 9) < 0.01);
      assert.equal(content.checks, 4);
      assert.equal(content.locations, 4);
      assert.deepEqual(content.decisions, ["defect", "hypothesis", "gap"]);
      assert.ok(content.math.includes("USD 60") && content.math.includes("USD 300"));
      assert.ok(content.math.includes("undefined, not USD 0"));
      assert.ok(content.boundaries.every((item) => item.present));
      assert.equal(content.overflow, false);
      assert.equal(content.anchors.length, 6);
      assert.equal(new Set(content.ids).size, content.ids.length);
      const anchors = [];
      for (const href of content.anchors) {
        await page.locator(`main nav a[href="${href}"]`).click();
        const position = await page.locator(href).evaluate((node) => ({ top: node.getBoundingClientRect().top,
          headerBottom: document.querySelector("header").getBoundingClientRect().bottom }));
        assert.ok(position.top >= position.headerBottom - 1 && position.top < 190, href);
        anchors.push({ href, ...position });
      }
      if (width <= 390) {
        const table = page.getByRole("region", { name: "Audit evidence and action examples", exact: true });
        await table.scrollIntoViewIfNeeded();
        await table.focus();
        await page.keyboard.press("ArrowRight");
        let scrolled = false;
        for (let attempt = 0; attempt < 30; attempt += 1) {
          scrolled = await table.evaluate((node) => document.activeElement === node && node.scrollLeft > 0);
          if (scrolled) break;
          await new Promise((resolve) => setTimeout(resolve, 50));
        }
        assert.equal(scrolled, true, "keyboard horizontal scroll");
        if (javaScriptEnabled) {
          await page.evaluate(() => scrollTo(0, 0));
          const menu = page.locator(".mobile-menu-toggle");
          await menu.click();
          assert.equal(await menu.getAttribute("aria-expanded"), "true");
          await page.locator("header nav a").first().isVisible().then((visible) => assert.equal(visible, true));
          await menu.click();
          assert.equal(await menu.getAttribute("aria-expanded"), "false");
        }
      }
      if (width === 1440 && javaScriptEnabled) {
        for (const target of content.links) {
          const response = await context.request.get(new URL(target, base).href);
          assert.equal(response.status(), 200, target);
        }
      }
      if (width === 1440 || width === 390) {
        await page.goto(new URL(articlePath, base).href, { waitUntil: "networkidle" });
        const suffix = javaScriptEnabled ? "js" : "nojs";
        await page.screenshot({ path: path.join(output, `article-${width}-${suffix}.png`) });
        await page.locator('main nav a[href="#evidence-log"]').click();
        await page.screenshot({ path: path.join(output, `evidence-${width}-${suffix}.png`) });
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
      assert.ok((await card.locator("small").textContent()).startsWith("2026-10-26"));
      await card.locator("img").scrollIntoViewIfNeeded();
      await card.locator("img").evaluate((image) => image.decode());
      assert.ok((await card.locator("img").getAttribute("src")).endsWith("account-audit-evidence-thumb-v1.webp"));
      await card.locator("h3 a").click();
      assert.equal(new URL(page.url()).pathname, "/" + articlePath);
      results.push({ width, javaScriptEnabled, ...content, anchors, keyboardScroll: width <= 390, listingPage, listingPassed: true });
      await context.close();
      console.log(`Passed US audit ${width}px/${javaScriptEnabled ? "JS" : "noJS"}`);
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, "browser.json"), JSON.stringify({ checkedAt: new Date().toISOString(), base: base.href, results, pageErrors: errors }, null, 2) + "\n");
  } finally { await browser.close(); }
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
