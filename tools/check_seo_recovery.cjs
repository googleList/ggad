const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const base = new URL(process.argv[2] || "http://127.0.0.1:8783/");
const output = process.argv[3] || path.join(os.tmpdir(), "shumao-seo-recovery");
const simulate = process.argv.includes("--simulate-nested-404");
assert.ok(!simulate || ["localhost", "127.0.0.1"].includes(base.hostname), "Never simulate production responses");
const articlePages = ["google-budget-pacing.html", "performance-max-basics.html", "search-terms-optimization.html", "seo-content-cluster.html"];

async function main() {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH });
  const results = [];
  try {
    for (const [width, missing] of [[1440, "seo-recovery-check/missing.html"], [390, "seo-recovery-check/deeper/missing.html"], [320, "seo-recovery-check/deleted/"]]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, javaScriptEnabled: false });
      const page = await context.newPage();
      const url = new URL(missing, base).href;
      if (simulate) await page.route(url, (route) => route.fulfill({ status: 404, contentType: "text/html",
        body: fs.readFileSync(path.join(__dirname, "..", "404.html"), "utf8") }));
      assert.equal((await page.goto(url, { waitUntil: "load", timeout: 45000 })).status(), 404);
      const content = await page.evaluate(() => ({
        headline: document.querySelector("h1").textContent.trim(),
        robots: document.querySelector('meta[name="robots"]').content,
        stylesheetLoaded: [...document.styleSheets].some((sheet) => sheet.href?.endsWith("/styles.css") && sheet.cssRules.length > 0),
        logo: document.querySelector(".brand img").currentSrc,
        logoLoaded: document.querySelector(".brand img").complete && document.querySelector(".brand img").naturalWidth > 0,
        home: document.querySelector(".legal-actions a").href,
        links: [...document.querySelectorAll("a[href]")].map((link) => ({ href: link.getAttribute("href"), url: link.href, text: link.textContent.trim() })),
        resources: [...document.querySelectorAll('link[href], img[src]')].map((node) => node.href || node.src),
        overflow: document.documentElement.scrollWidth > innerWidth + 1,
      }));
      assert.equal(content.headline, "这个页面已经下线");
      assert.ok(content.robots.includes("noindex"));
      assert.equal(content.stylesheetLoaded, true);
      assert.equal(content.logoLoaded, true);
      assert.equal(content.logo, new URL("assets/logo.svg", base).href);
      assert.equal(content.home, new URL("index.html", base).href);
      assert.equal(content.overflow, false);
      assert.ok(content.links.every((link) => link.href.startsWith("/") && !link.href.startsWith("//")));
      assert.ok(content.links.some((link) => link.text.includes("Ad Rank")));
      for (const target of new Set([...content.links.map((link) => link.url), ...content.resources])) {
        assert.equal((await context.request.get(target)).status(), 200, target);
      }
      await page.screenshot({ path: path.join(output, "missing-" + width + ".png") });
      const navigation = page.waitForURL(new URL("index.html", base).href);
      await page.locator("main .legal-actions a").click();
      await navigation;
      assert.equal(new URL(page.url()).pathname, "/index.html");
      results.push({ width, missing: url, responseStatus: 404, simulatedDelivery: simulate, javascript: false,
        ...content, recoveryNavigationPassed: true });
      await context.close();
      console.log("Passed nested404 recovery " + width + "px");
    }
    for (const width of [1440, 390]) {
      const context = await browser.newContext({ viewport: { width, height: 900 } });
      for (const filename of articlePages) {
        const page = await context.newPage();
        assert.equal((await page.goto(new URL("articles/" + filename, base).href, { waitUntil: "networkidle", timeout: 45000 })).status(), 200);
        const link = page.locator('main a[href="google-search-ads-guide.html"]');
        assert.equal(await link.count(), 1);
        const label = (await link.textContent()).trim();
        assert.ok(/排名|广告评级|Ad Rank/.test(label), label);
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
        await link.click();
        await page.waitForURL(new URL("articles/google-search-ads-guide.html", base).href);
        assert.equal(await page.locator("h1").textContent(), "谷歌广告排名怎么提升？Ad Rank影响因素与优化方法");
        results.push({ width, article: filename, label, destinationHeadlinePassed: true, noOverflow: true });
        await page.close();
      }
      await context.close();
    }
    fs.writeFileSync(path.join(output, "browser.json"), JSON.stringify({ checkedAt: new Date().toISOString(), base: base.href,
      simulated404Delivery: simulate, results }, null, 2) + "\n");
  } finally { await browser.close(); }
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
