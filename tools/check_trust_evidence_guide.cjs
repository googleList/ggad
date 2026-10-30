const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const base = new URL(process.argv[2] || "http://127.0.0.1:8808/");
const output = process.argv[3];
assert.ok(output, "Provide an evidence directory");
const articlePath = "articles/website-trust-pages.html";

async function stylesheetReady(page) {
  await page.waitForFunction(() => [...document.styleSheets].some(s => s.href && new URL(s.href).pathname.endsWith("/styles.css")));
}

async function main() {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH, headless: true });
  const results = [], errors = [];
  try {
    for (const [width, javaScriptEnabled] of [[1440,true],[768,true],[390,true],[320,true],[1440,false],[390,false]]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, javaScriptEnabled, reducedMotion: "reduce" });
      const page = await context.newPage();
      page.setDefaultTimeout(15000);
      page.setDefaultNavigationTimeout(45000);
      page.on("pageerror", e => errors.push(`${width}/${javaScriptEnabled}: ${e.message}`));
      assert.equal((await page.goto(new URL(articlePath, base).href, { waitUntil: "domcontentloaded" })).status(), 200);
      await stylesheetReady(page);
      await page.locator(".article-cover").evaluate(image => image.decode());
      const content = await page.evaluate(() => {
        const main = document.querySelector("main");
        const schema = [...document.querySelectorAll('script[type="application/ld+json"]')].map(s => JSON.parse(s.textContent)).find(s => s["@type"] === "Article");
        const img = main.querySelector(".article-cover");
        return { title: document.title, headline: main.querySelector("h1").textContent, schema,
          canonical: document.querySelector('link[rel="canonical"]').href, modified: main.querySelector("time").dateTime,
          descriptions: [schema.description, document.querySelector('meta[name="description"]').content, document.querySelector('meta[property="og:description"]').content, document.querySelector('meta[name="twitter:description"]').content],
          images: [schema.image, document.querySelector('meta[property="og:image"]').content, document.querySelector('meta[name="twitter:image"]').content],
          cover: { src: img.currentSrc, loaded: img.naturalWidth > 0, ratio: img.getBoundingClientRect().width / img.getBoundingClientRect().height },
          rows: [...main.querySelectorAll("[data-trust-evidence]")].map(n => n.dataset.trustEvidence),
          cases: [...main.querySelectorAll("[data-trust-case]")].map(n => n.dataset.trustCase),
          journey: main.querySelectorAll("[data-trust-journey] > li").length, review: main.querySelectorAll("[data-trust-review] > li").length,
          anchors: [...main.querySelectorAll("nav a")].map(n => n.getAttribute("href")), ids: [...document.querySelectorAll("[id]")].map(n => n.id),
          links: [...new Set([...main.querySelectorAll("a[href]")].filter(n => n.origin === location.origin && !n.getAttribute("href").startsWith("#")).map(n => n.pathname + n.hash))],
          overflow: document.documentElement.scrollWidth > innerWidth + 1 };
      });
      assert.equal(content.headline, "广告投放站点必须补齐哪些信任页面");
      assert.equal(content.schema.headline, content.headline);
      assert.equal(content.title, content.headline + " | 昆明振润达商贸有限公司");
      assert.equal(content.canonical, "https://shumaojs.com/" + articlePath);
      assert.equal(content.schema.datePublished, "2026-09-11");
      assert.equal(content.modified, "2026-10-30T18:14:15+08:00");
      assert.equal(content.schema.dateModified, content.modified);
      assert.equal(new Set(content.descriptions).size, 1);
      assert.equal(new Set(content.images).size, 1);
      assert.ok(content.images[0].endsWith("site-trust-evidence-v1.jpg"));
      assert.ok(content.cover.loaded);
      assert.ok(content.cover.src.endsWith(width <= 600 ? "site-trust-evidence-thumb-v1.webp" : "site-trust-evidence-v1.jpg"));
      assert.ok(Math.abs(content.cover.ratio - 16 / 9) < 0.01);
      assert.deepEqual(content.rows, ["identity","scope","fees","contact","data","claims"]);
      assert.deepEqual(content.cases, ["identity-mismatch","fee-mismatch","data-mismatch","verification-not-policy"]);
      assert.equal(content.journey, 4);
      assert.equal(content.review, 4);
      assert.equal(content.overflow, false);
      assert.equal(new Set(content.ids).size, content.ids.length);
      assert.equal(content.anchors.length, 7);
      for (const href of content.anchors) {
        await page.locator(`main nav a[href="${href}"]`).click();
        const position = await page.locator(href).evaluate(n => ({ top: n.getBoundingClientRect().top, headingBottom: n.querySelector("h2").getBoundingClientRect().bottom,
          header: document.querySelector("header").getBoundingClientRect().bottom, viewport: innerHeight, bottomDistance: document.documentElement.scrollHeight - innerHeight - scrollY }));
        assert.ok(position.top >= position.header - 1, href);
        assert.ok(position.top < 190 || (position.bottomDistance <= 1 && position.headingBottom < position.viewport), href);
      }
      if (width <= 390) {
        const region = page.getByRole("region", { name: "六项业务信息与可核对证据", exact: true });
        await region.scrollIntoViewIfNeeded();
        await region.focus();
        await page.keyboard.press("ArrowRight");
        let scrolled = false;
        for (let attempt = 0; attempt < 30; attempt += 1) {
          scrolled = await region.evaluate(n => document.activeElement === n && n.scrollLeft > 0);
          if (scrolled) break;
          await new Promise(resolve => setTimeout(resolve, 50));
        }
        assert.ok(scrolled, "Mobile table must remain keyboard-scrollable without page JavaScript");
        if (javaScriptEnabled) {
          await page.evaluate(() => scrollTo(0, 0));
          const toggle = page.locator(".mobile-menu-toggle");
          await toggle.click();
          assert.equal(await toggle.getAttribute("aria-expanded"), "true");
          await toggle.click();
          assert.equal(await toggle.getAttribute("aria-expanded"), "false");
        }
      }
      if (width === 1440 && javaScriptEnabled) {
        for (const href of content.links) {
          const response = await context.request.get(new URL(href, base).href);
          assert.equal(response.status(), 200, href);
          if (new URL(href, base).hash) {
            const fragment = decodeURIComponent(new URL(href, base).hash.slice(1));
            assert.ok((await response.text()).includes(`id="${fragment}"`), href);
          }
        }
      }
      if ([1440,390].includes(width)) {
        await page.goto(new URL(articlePath, base).href, { waitUntil: "domcontentloaded" });
        await stylesheetReady(page);
        await page.locator(".article-cover").evaluate(image => image.decode());
        const suffix = `${width}-${javaScriptEnabled ? "js" : "nojs"}`;
        await page.screenshot({ path: path.join(output, `article-${suffix}.png`) });
        await page.locator('main nav a[href="#evidence-checks"]').click();
        await page.screenshot({ path: path.join(output, `evidence-${suffix}.png`) });
      }
      await page.goto(new URL("articles.html", base).href, { waitUntil: "domcontentloaded" });
      await stylesheetReady(page);
      const card = page.locator("[data-article-card]").filter({ has: page.locator(`h3 a[href="${articlePath}"]`) });
      if (javaScriptEnabled) await page.locator('[data-article-category-button][data-article-category="website"]').click();
      assert.ok(await card.isVisible());
      assert.ok((await card.locator("small").textContent()).startsWith("2026-10-30"));
      await card.locator("img").scrollIntoViewIfNeeded();
      await card.locator("img").evaluate(image => image.decode());
      assert.ok((await card.locator("img").getAttribute("src")).endsWith("site-trust-evidence-thumb-v1.webp"));
      await card.locator("h3 a").click();
      assert.equal(new URL(page.url()).pathname, "/" + articlePath);
      results.push({ width, javaScriptEnabled, ...content, listingJourneyPassed: true });
      console.log(`Passed trust evidence guide ${width}px/${javaScriptEnabled ? "JS" : "noJS"}`);
      await context.close();
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, "browser.json"), JSON.stringify({ checkedAt: new Date().toISOString(), base: base.href, results, pageErrors: errors }, null, 2) + "\n");
  } finally { await browser.close(); }
}
main().catch(e => { console.error(e); process.exitCode = 1; });
