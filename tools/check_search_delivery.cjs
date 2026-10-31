const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const sharp = require(process.env.SHARP_MODULE || "sharp");
const base = new URL(process.argv[2] || "http://127.0.0.1:8781/");
const output = process.argv[3] || path.join(require("node:os").tmpdir(), "search-delivery-check");
const relative = "articles/google-ads-not-showing.html";

(async () => {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH });
  const results = [], errors = [];
  try {
    const cases = [[1440, 1, true], [768, 1, true], [390, 1, true], [320, 1, true], [390, 2, true], [1440, 1, false], [390, 1, false]];
    for (const [width, deviceScaleFactor, javaScriptEnabled] of cases) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, deviceScaleFactor, javaScriptEnabled, reducedMotion: "reduce" });
      const page = await context.newPage();
      page.setDefaultTimeout(15000);
      page.on("pageerror", e => errors.push(`${width}/${javaScriptEnabled}: ${e.message}`));
      assert.equal((await page.goto(new URL(relative, base).href, { waitUntil: "networkidle", timeout: 45000 })).status(), 200);
      await page.locator(".article-cover").evaluate(img => img.decode());
      if (width<=390 && javaScriptEnabled) {
        const toggle=page.locator(".mobile-menu-toggle");
        assert.equal(await toggle.getAttribute("aria-expanded"),"false");
        await toggle.click();
        assert.equal(await toggle.getAttribute("aria-expanded"),"true");
        await page.locator(".nav-drop-toggle").click();
        assert.equal(await page.locator('.nav-dropdown-menu a[href="../google-ads.html"]').isVisible(),true);
        await toggle.click();
        assert.equal(await toggle.getAttribute("aria-expanded"),"false");
      }
      const state = await page.evaluate(() => {
        const schema = [...document.querySelectorAll('script[type="application/ld+json"]')].map(s => JSON.parse(s.textContent)).find(s => s["@type"] === "Article");
        const img = document.querySelector(".article-cover"), rect = img.getBoundingClientRect();
        return { title:document.querySelector("h1").textContent, schema, visibleDate:document.querySelector("main time").dateTime,
          descriptions:[document.querySelector('meta[name="description"]').content,document.querySelector('meta[property="og:description"]').content,document.querySelector('meta[name="twitter:description"]').content],
          images:[schema.image,document.querySelector('meta[property="og:image"]').content,document.querySelector('meta[name="twitter:image"]').content],
          canonical:document.querySelector('link[rel="canonical"]').href,
          image:{src:img.currentSrc,renderedWidth:rect.width,ratio:rect.width/rect.height}, overflow:document.documentElement.scrollWidth>innerWidth+1,
          anchors:[...document.querySelectorAll("main nav a")].map(a=>a.getAttribute("href")),
          localLinks:[...new Set([...document.querySelectorAll("main a")].filter(a=>a.origin===location.origin&&!a.getAttribute("href").startsWith("#")).map(a=>a.href))] };
      });
      assert.equal(state.title, state.schema.headline);
      assert.equal(state.canonical, "https://shumaojs.com/"+relative);
      assert.equal(state.schema.datePublished, "2026-11-01T01:00:00+08:00");
      assert.equal(state.schema.dateModified, state.visibleDate);
      assert.equal(new Set(state.descriptions).size, 1);
      assert.equal(new Set(state.images).size, 1);
      assert.equal(state.overflow, false);
      assert.equal(await page.locator("[data-delivery-check]").count(), 7);
      assert.equal(await page.locator("[data-delivery-example]").count(), 4);
      assert.equal(await page.locator("[data-delivery-log]").count(), 3);
      assert.equal(await page.locator("[data-delivery-symptom]").count(), 4);
      assert.equal(await page.locator("[data-preview-steps] > li").count(), 4);
      assert.equal(await page.locator("[data-delivery-records] > li").count(), 4);
      const imageResponse = await context.request.get(state.image.src);
      assert.equal(imageResponse.status(), 200);
      state.image.decodedWidth = (await sharp(await imageResponse.body()).metadata()).width;
      assert.ok(state.image.decodedWidth >= state.image.renderedWidth * deviceScaleFactor * 0.95, JSON.stringify(state.image));
      assert.ok(Math.abs(state.image.ratio - 16/9) < 0.01);
      for (const href of state.anchors) {
        await page.locator(`main nav a[href="${href}"]`).focus();
        await page.keyboard.press("Enter");
        assert.equal(new URL(page.url()).hash, href);
        const rect = await page.locator(href).evaluate(n=>({top:n.getBoundingClientRect().top,header:document.querySelector("header").getBoundingClientRect().bottom}));
        assert.ok(rect.top >= rect.header-1 && rect.top < 195, JSON.stringify({width,href,rect}));
      }
      for (const href of state.localLinks) {
        const response = await context.request.get(href);
        assert.equal(response.status(), 200, href);
        const hash = new URL(href).hash;
        if (hash) assert.ok((await response.text()).includes(`id="${hash.slice(1)}"`), href);
      }
      if (width <= 390) {
        for (const table of await page.locator(".article-table-wrap").all()) {
          await table.scrollIntoViewIfNeeded(); await table.focus(); await page.keyboard.press("ArrowRight");
          let scrollLeft = 0;
          for (let attempt=0; attempt<30 && !scrollLeft; attempt++) {
            scrollLeft = await table.evaluate(n=>n.scrollLeft);
            if (!scrollLeft) await page.waitForTimeout(50);
          }
          assert.ok(scrollLeft>0, `${width}/${deviceScaleFactor}/${javaScriptEnabled}: keyboard table scroll`);
        }
      }
      if ([1440,390].includes(width) && deviceScaleFactor===1 && javaScriptEnabled) {
        await page.goto(new URL(relative,base).href); await page.locator(".article-cover").evaluate(img=>img.decode());
        await page.screenshot({path:path.join(output,`article-${width}.png`)});
        await page.locator('a[href="#checks"]').click();
        await page.screenshot({path:path.join(output,`checks-${width}.png`)});
      }
      await page.goto(new URL("articles.html",base).href,{waitUntil:"load"});
      if(javaScriptEnabled) await page.locator('[data-article-category-button][data-article-category="sem"]').click();
      const card=page.locator("[data-article-card]").filter({has:page.locator(`h3 a[href="${relative}"]`)});
      if(javaScriptEnabled) {
        for(let i=0;i<20 && !(await card.isVisible());i++) {
          const next=page.locator(".pagination button").last();
          assert.equal(await next.isDisabled(),false,"new SEM card reachable through pagination");
          await next.click();
        }
      }
      assert.equal(await card.isVisible(),true);
      await card.locator("img").scrollIntoViewIfNeeded(); await card.locator("img").evaluate(img=>img.decode());
      await card.locator("h3 a").click();
      assert.equal(new URL(page.url()).pathname,"/"+relative);
      results.push({width,deviceScaleFactor,javaScriptEnabled,...state,listingJourney:true,mobileMenuChecked:width<=390&&javaScriptEnabled});
      await context.close();
    }
    assert.deepEqual(errors,[]);
    const report={checkedAt:new Date().toISOString(),base:base.href,results,pageErrors:errors};
    fs.writeFileSync(path.join(output,"browser.json"),JSON.stringify(report,null,2)+"\n");
    console.log(JSON.stringify({checkedAt:report.checkedAt,cases:results.length,errors:errors.length}));
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
