const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const base = new URL(process.argv[2]);
const output = process.argv[3];
const article = "articles/google-search-ads-cost-guide.html#quote-comparison";

(async () => {
  fs.mkdirSync(output, {recursive:true});
  const browser = await chromium.launch({headless:true, executablePath:process.env.CHROME_PATH});
  const results = [], errors = [];
  try {
    for (const [width, mode] of [[1440,"js"],[768,"js"],[390,"js"],[320,"js"],[1440,"nojs"],[390,"nojs"],[390,"blocked"]]) {
      const context = await browser.newContext({viewport:{width,height:1000},javaScriptEnabled:mode!=="nojs",reducedMotion:"reduce"});
      const page = await context.newPage();
      page.on("pageerror",e=>errors.push(e.message));
      if (mode==="blocked") await page.route("**/assets/quote-comparison-v1.js*",r=>r.abort());
      assert.equal((await page.goto(new URL(article,base).href,{waitUntil:"networkidle"})).status(),200);
      const form = page.locator("[data-quote-comparison]");
      const fields = form.locator("[data-quote-fields]");
      const result = form.locator("[data-quote-results]");
      const number = async key => Number((await form.locator(`[data-quote-output="${key}"]`).textContent()).replace(/[^0-9.-]/g,""));
      if (mode==="js") {
        assert.equal(await form.getAttribute("data-quote-ready"),"true");
        assert.equal(await fields.evaluate(n=>n.disabled),false);
        assert.equal(await number("0-termTotalCents"),10500);
        assert.equal(await number("1-termTotalCents"),10500);
        assert.equal(await number("0-firstMonthCents"),3500);
        assert.equal(await number("1-firstMonthCents"),3700);
        const b=form.locator("[data-quote-offer]").nth(1);
        await b.locator("[data-quote-mode]").selectOption("hybrid");
        await b.locator("[data-quote-base]").fill("200");
        await b.locator("[data-quote-rate]").fill("5");
        await b.locator("[data-quote-setup]").fill("100");
        assert.equal(await number("1-termTotalCents"),10300);
        await form.locator("[data-quote-media]").fill("");
        assert.equal(await result.isVisible(),false);
        assert.equal(await form.locator("[data-quote-error]").isVisible(),true);
        assert.equal(await form.locator('[data-quote-output="0-termTotalCents"]').textContent(),"—");
        await form.locator("[data-quote-media]").fill("1e3");
        assert.equal(await result.isVisible(),false);
        assert.equal(await form.locator("[data-quote-media]").getAttribute("aria-invalid"),"true");
        assert.equal(await form.locator("[data-quote-months]").getAttribute("aria-invalid"),"false");
        await form.locator("[data-quote-media]").fill("0");
        assert.equal(await result.isVisible(),true);
        await form.locator("[data-quote-months]").fill("1.5");
        assert.equal(await result.isVisible(),false);
        await form.locator("[data-quote-months]").fill("3");
        await form.locator("[data-quote-currency]").selectOption("HKD");
        assert.equal(await form.locator("[data-quote-media]").inputValue(),"0");
        assert.ok((await form.locator('[data-quote-output="0-termTotalCents"]').textContent()).includes("HK"));
        await form.locator('[type="reset"]').click();
        await page.waitForFunction(()=>document.querySelector("[data-quote-currency]").value==="USD" && document.querySelector('[data-quote-output="0-termTotalCents"]').textContent.includes("10,500"));
        assert.equal(await number("1-termTotalCents"),10500);
        assert.equal(await b.locator("[data-quote-base]").isDisabled(),true);
        assert.equal(await b.locator("[data-quote-base]").isVisible(),false);
        const previous = page.url();
        await form.locator("[data-quote-months]").press("Enter");
        assert.equal(page.url(),previous);
      } else {
        assert.equal(await fields.evaluate(n=>n.disabled),true);
        assert.equal(await form.locator("[data-quote-media]").isDisabled(),true);
        assert.equal(await form.locator('[type="reset"]').isDisabled(),true);
        assert.equal(await result.isVisible(),false);
        assert.equal(await form.locator("[data-quote-unavailable]").isVisible(),true);
        assert.equal(await page.locator("[data-quote-formulas] > li").count(),4);
      }
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
      assert.equal(overflow,false);
      await page.locator("#quote-comparison").scrollIntoViewIfNeeded();
      await page.screenshot({path:path.join(output,`quote-${width}-${mode}.png`),fullPage:false});
      results.push({width,mode,overflow,defaultAndHybridChecked:mode==="js",fallbackChecked:mode!=="js"});
      await context.close();
    }
    assert.deepEqual(errors,[]);
    const report={checkedAt:new Date().toISOString(),base:base.href,results,pageErrors:errors};
    fs.writeFileSync(path.join(output,"browser.json"),JSON.stringify(report,null,2)+"\n");
    console.log(JSON.stringify({checkedAt:report.checkedAt,cases:results.length,pageErrors:errors.length}));
  } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});
