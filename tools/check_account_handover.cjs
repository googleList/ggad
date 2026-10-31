const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const sharp = require(process.env.SHARP_MODULE || "sharp");
const base = new URL(process.argv[2]);
const output = process.argv[3];
const guides = ["google-ads-account-ownership-usa.html", "google-ads-account-access-hong-kong.html"];

(async () => {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH });
  const results = [], errors = [];
  try {
    for (const guide of guides) {
      for (const [width, javaScriptEnabled, dpr] of [[1440,true,1],[768,true,1],[390,true,1],[390,true,2],[320,true,1],[1440,false,1],[390,false,1]]) {
        const context = await browser.newContext({ viewport: { width, height: 900 }, javaScriptEnabled, deviceScaleFactor: dpr, reducedMotion: "reduce" });
        const page = await context.newPage();
        page.on("pageerror", e => errors.push(e.message));
        assert.equal((await page.goto(new URL("articles/" + guide, base).href)).status(), 200);
        await page.locator(".article-cover").evaluate(img => img.decode());
        assert.equal(await page.locator("[data-handover-check]").count(), 6);
        assert.equal(await page.locator("[data-handover-example]").count(), 3);
        assert.equal(await page.locator("[data-handover-records] > li").count(), 4);
        const metadata = await page.evaluate(() => {
          const article = [...document.querySelectorAll('script[type="application/ld+json"]')].map(s=>JSON.parse(s.textContent)).find(s=>s["@type"]==="Article");
          const img = document.querySelector(".article-cover"), rect = img.getBoundingClientRect();
          return { published:article.datePublished, modified:article.dateModified, visibleDate:document.querySelector("main time").dateTime,
            images:[article.image,document.querySelector('meta[property="og:image"]').content,document.querySelector('meta[name="twitter:image"]').content],
            image:{src:img.currentSrc,naturalWidth:img.naturalWidth,renderedWidth:rect.width,ratio:rect.width/rect.height},
            overflow:document.documentElement.scrollWidth>innerWidth+1 };
        });
        assert.equal(metadata.published, "2026-09-28");
        assert.equal(metadata.modified, metadata.visibleDate);
        assert.equal(new Set(metadata.images).size,1);
        const imageResponse = await context.request.get(metadata.image.src);
        assert.equal(imageResponse.status(), 200);
        const decoded = await sharp(await imageResponse.body()).metadata();
        metadata.image.decodedWidth = decoded.width;
        assert.ok(metadata.image.naturalWidth > 0);
        assert.ok(decoded.width >= metadata.image.renderedWidth * dpr * 0.95, JSON.stringify({guide,width,dpr,image:metadata.image}));
        assert.ok(Math.abs(metadata.image.ratio-16/9)<0.01);
        assert.equal(metadata.overflow,false);
        for (const id of ["handover-dependencies","handover-examples","handover-records"]) {
          await page.locator(`a[href="#${id}"]`).focus(); await page.keyboard.press("Enter");
          assert.equal(new URL(page.url()).hash,"#"+id);
          const r = await page.locator("#"+id).evaluate(n=>({top:n.getBoundingClientRect().top,header:document.querySelector("header").getBoundingClientRect().bottom}));
          assert.ok(r.top>=r.header-1 && r.top<195, JSON.stringify(r));
        }
        if (width<=390) {
          const table=page.locator(".article-table-wrap");
          await table.scrollIntoViewIfNeeded(); await table.focus(); await page.keyboard.press("ArrowRight");
          let scrollLeft = 0;
          for (let attempt=0; attempt<30 && !scrollLeft; attempt++) {
            scrollLeft = await table.evaluate(n=>n.scrollLeft);
            if (!scrollLeft) await page.waitForTimeout(50);
          }
          assert.ok(scrollLeft>0, `${guide}/${width}/${javaScriptEnabled}: keyboard horizontal scroll`);
        }
        if ([1440,390].includes(width) && dpr===1) {
          await page.goto(new URL("articles/"+guide,base).href); await page.locator(".article-cover").evaluate(img=>img.decode());
          await page.screenshot({path:path.join(output,`${guide}-${width}-${javaScriptEnabled}.png`)});
          await page.locator('a[href="#handover-dependencies"]').click();
          await page.screenshot({path:path.join(output,`${guide}-checks-${width}-${javaScriptEnabled}.png`)});
        }
        results.push({guide,width,javaScriptEnabled,dpr,...metadata,checks:6,examples:3,records:4});
        await context.close();
      }
    }
    assert.deepEqual(errors,[]);
    const report={checkedAt:new Date().toISOString(),base:base.href,results,pageErrors:errors};
    fs.writeFileSync(path.join(output,"browser.json"),JSON.stringify(report,null,2)+"\n");
    console.log(JSON.stringify({checkedAt:report.checkedAt,cases:results.length,pageErrors:errors.length}));
  } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});
