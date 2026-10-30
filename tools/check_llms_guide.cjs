const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const base = new URL(process.argv[2] || "http://127.0.0.1:8809/");
const output = process.argv[3];
assert.ok(output, "Provide an evidence directory");
const articlePath = "articles/llms-txt-ai-search-guide.html";
const headline = "llms.txt 是什么？作用、写法与 Google 搜索边界";

async function stylesheetReady(page) {
  for (let i = 0; i < 100; i += 1) {
    if (await page.evaluate(() => [...document.styleSheets].some(s => s.href && new URL(s.href).pathname.endsWith("/styles.css")))) return;
    await new Promise(resolve => setTimeout(resolve, 50));
  }
  throw new Error("Site stylesheet did not become ready");
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
      await page.locator(".article-cover").evaluate(img => img.decode());
      const content = await page.evaluate(() => {
        const main = document.querySelector("main"), img = main.querySelector(".article-cover");
        const schema = [...document.querySelectorAll('script[type="application/ld+json"]')].map(s => JSON.parse(s.textContent)).find(s => s["@type"] === "Article");
        return { title: document.title, headline: main.querySelector("h1").textContent, canonical: document.querySelector('link[rel="canonical"]').href, schema,
          modified: main.querySelector("time").dateTime,
          descriptions: [schema.description, document.querySelector('meta[name="description"]').content, document.querySelector('meta[property="og:description"]').content, document.querySelector('meta[name="twitter:description"]').content],
          images: [schema.image, document.querySelector('meta[property="og:image"]').content, document.querySelector('meta[name="twitter:image"]').content],
          cover: { src: img.currentSrc, loaded: img.naturalWidth > 0, ratio: img.getBoundingClientRect().width / img.getBoundingClientRect().height },
          boundaries: [...main.querySelectorAll("[data-llms-boundary]")].map(n => n.dataset.llmsBoundary), cases: [...main.querySelectorAll("[data-llms-case]")].map(n => n.dataset.llmsCase),
          checks: main.querySelectorAll("[data-llms-checks] > li").length, review: main.querySelectorAll("[data-llms-review] > li").length,
          ids: [...document.querySelectorAll("[id]")].map(n => n.id), anchors: [...main.querySelectorAll("nav a")].map(n => n.getAttribute("href")),
          links: [...new Set([...main.querySelectorAll("a[href]")].filter(n => n.origin === location.origin && !n.getAttribute("href").startsWith("#")).map(n => n.pathname + n.hash))], overflow: document.documentElement.scrollWidth > innerWidth + 1 };
      });
      assert.equal(content.headline, headline);
      assert.equal(content.title, headline + " | 昆明振润达商贸有限公司");
      assert.equal(content.schema.headline, headline);
      assert.equal(content.canonical, "https://shumaojs.com/" + articlePath);
      assert.equal(content.schema.datePublished, "2026-09-11");
      assert.equal(content.modified, "2026-10-30T18:32:42+08:00");
      assert.equal(content.schema.dateModified, content.modified);
      assert.equal(new Set(content.descriptions).size, 1);
      assert.equal(new Set(content.images).size, 1);
      assert.ok(content.cover.loaded && Math.abs(content.cover.ratio - 16/9) < 0.01);
      assert.ok(content.cover.src.endsWith(width <= 600 ? "llms-reading-guide-thumb-v1.webp" : "llms-reading-guide-v1.jpg"));
      assert.deepEqual(content.boundaries, ["proposal","robots","sitemap","access","full-file","outcome"]);
      assert.deepEqual(content.cases, ["search-goal","blocked-target","stale-version","large-bundle"]);
      assert.equal(content.checks, 6);
      assert.equal(content.review, 4);
      assert.equal(content.overflow, false);
      assert.equal(new Set(content.ids).size, content.ids.length);
      assert.equal(content.anchors.length, 7);
      for (const href of content.anchors) {
        await page.locator(`main nav a[href="${href}"]`).click();
        const p = await page.locator(href).evaluate(n => ({ top: n.getBoundingClientRect().top, headingBottom: n.querySelector("h2").getBoundingClientRect().bottom, header: document.querySelector("header").getBoundingClientRect().bottom, viewport: innerHeight, bottomDistance: document.documentElement.scrollHeight - innerHeight - scrollY }));
        assert.ok(p.top >= p.header - 1, href);
        assert.ok(p.top < 190 || (p.bottomDistance <= 1 && p.headingBottom < p.viewport), href);
      }
      if (width <= 390) {
        for (const name of ["llms.txt 与其他文件和结果的作用边界", "公开站点导读示例"]) {
          const region = page.getByRole("region", { name, exact: true });
          await region.scrollIntoViewIfNeeded();
          await region.focus();
          await page.keyboard.press("ArrowRight");
          let scrolled = false;
          for (let i = 0; i < 30; i += 1) {
            scrolled = await region.evaluate(n => document.activeElement === n && n.scrollLeft > 0);
            if (scrolled) break;
            await new Promise(resolve => setTimeout(resolve, 50));
          }
          assert.ok(scrolled, name);
        }
        if (javaScriptEnabled) {
          await page.evaluate(() => scrollTo(0, 0));
          const toggle = page.locator(".mobile-menu-toggle");
          await toggle.click(); assert.equal(await toggle.getAttribute("aria-expanded"), "true");
          await toggle.click(); assert.equal(await toggle.getAttribute("aria-expanded"), "false");
        }
      }
      if (width === 1440 && javaScriptEnabled) {
        for (const href of content.links) {
          const r = await context.request.get(new URL(href, base).href);
          assert.equal(r.status(), 200, href);
          if (new URL(href, base).hash) assert.ok((await r.text()).includes(`id="${decodeURIComponent(new URL(href, base).hash.slice(1))}"`), href);
        }
        const r = await context.request.get(new URL("llms.txt", base).href);
        const text = await r.text();
        assert.equal(r.status(), 200);
        assert.equal(text.replace(/\r\n/g,"\n"), fs.readFileSync("llms.txt","utf8").replace(/\r\n/g,"\n"));
        const links = [...text.matchAll(/^- \[([^\]]+)\]\((https:\/\/shumaojs\.com\/[^\s)]*)\):/gm)];
        for (const [,label,url] of links) {
          const target = new URL(url);
          assert.equal((await context.request.get(new URL(target.pathname + target.hash, base).href)).status(), 200, label);
        }
        content.directory = { status: r.status(), contentMatchesSource: true, linkedPublicPages: links.length };
      }
      if ([1440,390].includes(width)) {
        await page.goto(new URL(articlePath, base).href, { waitUntil: "domcontentloaded" });
        await stylesheetReady(page);
        await page.locator(".article-cover").evaluate(img => img.decode());
        const suffix = `${width}-${javaScriptEnabled ? "js" : "nojs"}`;
        await page.screenshot({ path: path.join(output, `article-${suffix}.png`) });
        await page.locator('main nav a[href="#example"]').click();
        await page.screenshot({ path: path.join(output, `example-${suffix}.png`) });
      }
      await page.goto(new URL("articles.html", base).href, { waitUntil: "domcontentloaded" });
      await stylesheetReady(page);
      if (javaScriptEnabled) await page.locator('[data-article-category-button][data-article-category="geo"]').click();
      const card = page.locator("[data-article-card]").filter({ has: page.locator(`h3 a[href="${articlePath}"]`) });
      assert.ok(await card.isVisible());
      assert.equal(await card.locator("h3").textContent(), headline);
      await card.locator("img").scrollIntoViewIfNeeded();
      await card.locator("img").evaluate(img => img.decode());
      assert.ok((await card.locator("img").getAttribute("src")).endsWith("llms-reading-guide-thumb-v1.webp"));
      await card.locator("h3 a").click();
      assert.equal(new URL(page.url()).pathname, "/" + articlePath);
      results.push({ width, javaScriptEnabled, ...content, listingJourneyPassed: true });
      console.log(`Passed llms guide ${width}px/${javaScriptEnabled ? "JS" : "noJS"}`);
      await context.close();
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output,"browser.json"), JSON.stringify({ checkedAt: new Date().toISOString(), base: base.href, results, pageErrors: errors },null,2) + "\n");
  } finally { await browser.close(); }
}
main().catch(e => { console.error(e); process.exitCode = 1; });
