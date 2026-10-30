const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const base = new URL(process.argv[2] || "http://127.0.0.1:8803/");
const output = process.argv[3];
assert.ok(output, "Provide an evidence directory");
const articlePath = "articles/google-seo-ranking-guide.html";

async function stylesheetReady(page) {
  for (let attempt = 0; attempt < 100; attempt += 1) {
    if (await page.evaluate(() => [...document.styleSheets].some(sheet => sheet.href && new URL(sheet.href).pathname.endsWith("/styles.css")))) return true;
    await new Promise(resolve => setTimeout(resolve, 50));
  }
  throw new Error("Site stylesheet did not become ready");
}

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
      await stylesheetReady(page);
      await page.locator(".article-cover").evaluate(image => image.decode());
      const content = await page.evaluate(() => {
        const main = document.querySelector("main");
        const schema = [...document.querySelectorAll('script[type="application/ld+json"]')].map(n => JSON.parse(n.textContent)).find(n => n["@type"] === "Article");
        const image = main.querySelector(".article-cover");
        return { title: document.title, headline: main.querySelector("h1").textContent, schema,
          canonical: document.querySelector('link[rel="canonical"]').href, modified: main.querySelector("time").dateTime,
          descriptions: [schema.description, document.querySelector('meta[name="description"]').content,
            document.querySelector('meta[property="og:description"]').content, document.querySelector('meta[name="twitter:description"]').content],
          images: [schema.image, document.querySelector('meta[property="og:image"]').content, document.querySelector('meta[name="twitter:image"]').content],
          cover: { src: image.currentSrc, loaded: image.naturalWidth > 0, ratio: image.getBoundingClientRect().width / image.getBoundingClientRect().height },
          diagnosisRows: [...main.querySelectorAll("[data-seo-diagnosis]")].map(n => n.dataset.seoDiagnosis),
          caseRows: [...main.querySelectorAll("[data-seo-case]")].map(n => n.dataset.seoCase),
          reviewRecords: main.querySelectorAll("[data-seo-review] > li").length,
          anchors: [...main.querySelectorAll("nav a")].map(n => n.getAttribute("href")),
          ids: [...document.querySelectorAll("[id]")].map(n => n.id),
          links: [...new Set([...main.querySelectorAll("a[href]")].filter(n => n.origin === location.origin && !n.getAttribute("href").startsWith("#")).map(n => n.pathname + n.hash))],
          overflow: document.documentElement.scrollWidth > innerWidth + 1 };
      });
      assert.equal(content.headline, "谷歌排名怎么提升？自然搜索 SEO 排查与优化指南");
      assert.equal(content.title, content.headline + " | 昆明振润达商贸有限公司");
      assert.equal(content.schema.headline, content.headline);
      assert.equal(content.canonical, "https://shumaojs.com/" + articlePath);
      assert.equal(content.schema.datePublished, "2026-10-29T22:10:36+08:00");
      assert.equal(content.modified, "2026-10-29T22:10:36+08:00");
      assert.equal(content.schema.dateModified, content.modified);
      assert.equal(new Set(content.descriptions).size, 1);
      assert.equal(new Set(content.images).size, 1);
      assert.ok(content.images[0].endsWith("organic-seo-ranking-plan-v1.jpg"));
      assert.ok(content.cover.loaded);
      assert.ok(content.cover.src.endsWith(width <= 600 ? "organic-seo-ranking-plan-thumb-v1.webp" : "organic-seo-ranking-plan-v1.jpg"));
      assert.ok(Math.abs(content.cover.ratio - 16 / 9) < 0.01);
      assert.deepEqual(content.diagnosisRows, ["access", "indexability", "canonical", "intent", "content", "snippet", "links", "experience"]);
      assert.deepEqual(content.caseRows, ["not-indexed", "weak-visibility", "ctr-with-mix", "click-no-enquiry"]);
      assert.equal(content.reviewRecords, 4);
      assert.equal(content.overflow, false);
      assert.equal(new Set(content.ids).size, content.ids.length);
      assert.equal(content.anchors.length, 8);
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
        const region = page.getByRole("region", { name: "自然搜索 SEO 的证据、动作与边界", exact: true });
        await region.scrollIntoViewIfNeeded();
        await region.focus();
        await page.keyboard.press("ArrowRight");
        let scrolled = false;
        for (let attempt = 0; attempt < 30; attempt += 1) {
          scrolled = await region.evaluate(n => document.activeElement === n && n.scrollLeft > 0);
          if (scrolled) break;
          await new Promise(resolve => setTimeout(resolve, 50));
        }
        assert.ok(scrolled, "Mobile table must be keyboard-scrollable");
        if (javaScriptEnabled) {
          await page.evaluate(() => scrollTo(0, 0));
          const toggle = page.locator(".mobile-menu-toggle");
          await toggle.click();
          assert.equal(await toggle.getAttribute("aria-expanded"), "true");
          assert.ok(await page.locator("header nav a").first().isVisible());
          await toggle.click();
          assert.equal(await toggle.getAttribute("aria-expanded"), "false");
        }
      }
      const downloadEvent = page.waitForEvent("download");
      await page.locator("[data-seo-worksheet-download]").click();
      const download = await downloadEvent;
      assert.equal(download.suggestedFilename(), "organic-seo-audit-worksheet-v1.csv");
      const bytes = fs.readFileSync(await download.path());
      assert.deepEqual([...bytes.subarray(0, 3)], [239, 187, 191], "Chinese CSV must retain its UTF-8 BOM");
      assert.deepEqual(bytes, fs.readFileSync("assets/resources/organic-seo-audit-worksheet-v1.csv"));
      content.worksheetDownload = { name: download.suggestedFilename(), bytes: bytes.length,
        sha256: require("node:crypto").createHash("sha256").update(bytes).digest("hex"), matchesLocal: true };
      if (width === 1440 && javaScriptEnabled) {
        for (const target of content.links) assert.equal((await context.request.get(new URL(target, base).href)).status(), 200, target);
      }
      if ([1440,390].includes(width)) {
        await page.goto(new URL(articlePath, base).href, { waitUntil: "domcontentloaded" });
        await stylesheetReady(page);
        await page.locator(".article-cover").evaluate(image => image.decode());
        const suffix = `${width}-${javaScriptEnabled ? "js" : "nojs"}`;
        await page.screenshot({ path: path.join(output, `article-${suffix}.png`) });
        await page.locator('main nav a[href="#seo-diagnosis"]').click();
        await page.screenshot({ path: path.join(output, `diagnosis-${suffix}.png`) });
        await page.locator("[data-seo-worksheet-download]").scrollIntoViewIfNeeded();
        await page.screenshot({ path: path.join(output, `download-${suffix}.png`) });
      }
      assert.equal((await page.goto(new URL("articles.html", base).href, { waitUntil: "domcontentloaded" })).status(), 200);
      await stylesheetReady(page);
      const card = page.locator("[data-article-card]").filter({ has: page.locator(`h3 a[href="${articlePath}"]`) });
      let listingPage = null;
      if (javaScriptEnabled) {
        await page.locator('[data-article-category-button][data-article-category="seo"]').click();
        listingPage = 1;
        while (!await card.isVisible()) {
          assert.ok(listingPage < 8);
          const next = page.locator(".pagination button").last();
          assert.equal(await next.isDisabled(), false);
          await next.click();
          listingPage += 1;
        }
      }
      assert.ok(await card.isVisible());
      assert.ok((await card.locator("small").textContent()).startsWith("2026-10-29"));
      await card.locator("img").scrollIntoViewIfNeeded();
      await card.locator("img").evaluate(image => image.decode());
      assert.ok((await card.locator("img").getAttribute("src")).endsWith("organic-seo-ranking-plan-thumb-v1.webp"));
      await card.locator("h3 a").click();
      assert.equal(new URL(page.url()).pathname, "/" + articlePath);
      assert.equal((await page.goto(new URL("index.html", base).href, { waitUntil: "domcontentloaded" })).status(), 200);
      await stylesheetReady(page);
      const homeLink = page.locator('.home-guide h3 a[href="' + articlePath + '"]');
      await homeLink.scrollIntoViewIfNeeded();
      const homeCard = page.locator(".home-guide").filter({ has: page.locator('h3 a[href="' + articlePath + '"]') });
      await homeCard.locator("img").evaluate(image => image.decode());
      assert.ok((await homeCard.textContent()).includes("自然搜索 SEO"));
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
      if ([1440,390].includes(width)) await page.screenshot({ path: path.join(output, `home-guide-${width}-${javaScriptEnabled ? "js" : "nojs"}.png`) });
      await homeLink.click();
      assert.equal(new URL(page.url()).pathname, "/" + articlePath);
      results.push({ width, javaScriptEnabled, ...content, listingPage, listingJourneyPassed: true, homeJourneyPassed: true });
      console.log(`Passed organic SEO ranking guide ${width}px/${javaScriptEnabled ? "JS" : "noJS"}`);
      await context.close();
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, "browser.json"), JSON.stringify({ checkedAt: new Date().toISOString(), base: base.href, results, pageErrors: errors }, null, 2) + "\n");
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
