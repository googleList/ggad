const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");

const base = new URL(process.argv[2] || "http://127.0.0.1:8775/");
const output = process.argv[3] || path.join(os.tmpdir(), "shumao-service-scope-check");

async function main() {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH });
  const results = [];
  const errors = [];
  try {
    for (const width of [2560, 1440, 768, 390, 320]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: "reduce" });
      const page = await context.newPage();
      page.setDefaultTimeout(15000);
      page.on("pageerror", (error) => errors.push(`${width}px: ${error.message}`));
      const response = await page.goto(new URL("google-ads.html", base).href, { waitUntil: "networkidle", timeout: 45000 });
      assert.equal(response.status(), 200);
      const content = await page.evaluate(() => {
        const main = document.querySelector("main");
        const schema = [...document.querySelectorAll('script[type="application/ld+json"]')].map((node) => JSON.parse(node.textContent));
        return {
          title: document.title,
          h1: main.querySelector("h1").textContent.trim(),
          canonical: document.querySelector('link[rel="canonical"]').href,
          campaigns: [...main.querySelectorAll("#ad-types .ad-type-card > span")].map((node) => node.textContent),
          strategies: [...main.querySelectorAll("#audience-strategies .ad-type-card > span")].map((node) => node.textContent),
          scopeRows: main.querySelectorAll("#service-scope tbody tr").length,
          processSteps: main.querySelectorAll("#cooperation-process ol li").length,
          questions: main.querySelectorAll("#service-questions h3").length,
          ids: [...document.querySelectorAll("[id]")].map((node) => node.id),
          imagesLoaded: [...main.querySelectorAll("img")].every((node) => node.complete && node.naturalWidth > 0),
          overflow: document.documentElement.scrollWidth > innerWidth + 1,
          schemaTypes: schema.map((item) => item["@type"]),
          localLinks: [...new Set([...main.querySelectorAll("a[href]")]
            .filter((link) => link.origin === location.origin && !link.getAttribute("href").startsWith("#"))
            .map((link) => link.pathname))],
        };
      });
      assert.equal(content.title, "谷歌代投服务 | Google Ads投放管理与开户协助 | 昆明振润达");
      assert.equal(content.h1, "谷歌代投服务与开户协助");
      assert.equal(content.canonical, "https://shumaojs.com/google-ads.html");
      assert.deepEqual(content.campaigns, ["Search", "Display", "YouTube", "Shopping", "PMax", "Demand Gen", "App"]);
      assert.deepEqual(content.strategies, ["Remarketing", "Brand"]);
      assert.equal(content.scopeRows, 3);
      assert.equal(content.processSteps, 4);
      assert.equal(content.questions, 4);
      assert.equal(content.imagesLoaded, true);
      assert.equal(content.overflow, false);
      assert.equal(new Set(content.ids).size, content.ids.length);
      assert.ok(!content.schemaTypes.some((type) => ["Product", "Offer", "FAQPage"].includes(type)));
      await page.locator('.managed-hero a[href="#service-scope"]').click();
      await page.waitForFunction(() => {
        const top = document.querySelector("#service-scope").getBoundingClientRect().top;
        return top >= document.querySelector("header").getBoundingClientRect().bottom - 1 && top < 220;
      });
      const table = page.getByRole("region", { name: "合作范围确认清单", exact: true });
      if (width <= 390) {
        await table.focus();
        await page.keyboard.press("ArrowRight");
        await page.waitForFunction(() => document.querySelector(".article-table-wrap").scrollLeft > 0);
      }
      if (width === 1440) {
        for (const pathname of content.localLinks) {
          assert.equal((await context.request.get(new URL(pathname, base).href)).status(), 200, pathname);
        }
      }
      if (width === 1440 || width === 390) {
        await page.screenshot({ path: path.join(output, `scope-${width}.png`) });
        await page.evaluate(() => scrollTo(0, 0));
        await page.screenshot({ path: path.join(output, `service-${width}.png`), fullPage: true });
      }
      if (width <= 390) {
        const menu = page.locator(".mobile-menu-toggle");
        await menu.click();
        assert.equal(await menu.getAttribute("aria-expanded"), "true");
        const dropdown = page.locator(".nav-drop-toggle");
        await dropdown.click();
        assert.equal(await dropdown.getAttribute("aria-expanded"), "true");
        assert.equal(await page.locator('.nav-dropdown-menu a[href="google-ads.html"]').isVisible(), true);
        await menu.click();
        assert.equal(await dropdown.getAttribute("aria-expanded"), "false");
      }
      results.push({ width, ...content, scopeAnchorClear: true, mobileTableKeyboardScroll: width <= 390, passed: true });
      await context.close();
      console.log(`Passed service ${width}px`);
    }
    assert.deepEqual(errors, []);
    const report = { checkedAt: new Date().toISOString(), base: base.href, results, pageErrors: errors };
    fs.writeFileSync(path.join(output, "browser.json"), JSON.stringify(report, null, 2) + "\n");
  } finally {
    await browser.close();
  }
}

main().catch((error) => { console.error(error); process.exitCode = 1; });
