const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const base = process.argv[2];
const output = process.argv[3];
(async () => {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH });
  const results = [], errors = [];
  try {
    for (const [width, javaScriptEnabled] of [[1440,true],[768,true],[390,true],[320,true],[1440,false],[390,false]]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, javaScriptEnabled, reducedMotion: "reduce" });
      const page = await context.newPage();
      page.on("pageerror", e => errors.push(e.message));
      const response = await page.goto(new URL("articles/seo-course-learning-path.html", base).href);
      assert.equal(response.status(), 200);
      assert.equal(await page.locator("[data-learning-resources] > li").count(), 6);
      assert.equal(await page.locator("[data-learning-tasks] > li").count(), 4);
      assert.equal(await page.locator("[data-course-evidence] > li").count(), 4);
      for (const id of ["official-resources", "practice-tasks", "course-evidence"]) {
        await page.locator(`a[href="#${id}"]`).focus(); await page.keyboard.press("Enter");
        assert.equal(new URL(page.url()).hash, `#${id}`);
        assert.ok(await page.locator(`#${id}`).isVisible());
      }
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
      assert.equal(overflow, false);
      await page.screenshot({path:path.join(output, `learning-${width}-${javaScriptEnabled}.png`)});
      results.push({width,javaScriptEnabled,resources:6,tasks:4,evidenceChecks:4,anchors:3,overflow});
      await context.close();
    }
    assert.deepEqual(errors, []);
    const report = {checkedAt:new Date().toISOString(),base,results,pageErrors:errors};
    fs.writeFileSync(path.join(output,"browser.json"),JSON.stringify(report,null,2)+"\n");
    console.log(JSON.stringify(report));
  } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});
