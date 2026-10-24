const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const base = new URL(process.argv[2] || "http://127.0.0.1:8781/");
const output = process.argv[3] || path.join(os.tmpdir(), "shumao-service-hub");
const pages = [
  { path: "managed-ads.html", headline: "多平台广告管理与投放咨询", section: "platform-choice" },
  { path: "meta-ads.html", headline: "Meta广告管理与投放咨询", section: "scope-choice" },
  { path: "facebook-ads.html", headline: "Facebook广告管理与投放咨询", section: "lead-handover" },
];
async function main() {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH });
  const results = [], errors = [];
  try {
    for (const width of [2560, 1440, 768, 390, 320]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: "reduce" });
      const page = await context.newPage();
      page.setDefaultTimeout(15000);
      page.on("pageerror", (error) => errors.push(`${width}px: ${error.message}`));
      for (const target of pages) {
        assert.equal((await page.goto(new URL(target.path, base).href, { waitUntil: "networkidle", timeout: 45000 })).status(), 200);
        const content = await page.evaluate(() => ({
          headline: document.querySelector("main h1").textContent.trim(),
          canonical: document.querySelector('link[rel="canonical"]').href,
          description: document.querySelector('meta[name="description"]').content,
          ogDescription: document.querySelector('meta[property="og:description"]').content,
          twitterDescription: document.querySelector('meta[name="twitter:description"]').content,
          cardImages: [...document.querySelectorAll("main img")].map((image) => ({ src: image.getAttribute("src"), loaded: image.complete && image.naturalWidth > 0 })),
          typeCards: document.querySelectorAll("#ad-types .ad-type-card").length,
          routes: [...document.querySelectorAll("[data-platform-route]")].map((row) => ({ key: row.dataset.platformRoute, href: row.querySelector("a").getAttribute("href") })),
          routeLinksInFirstColumn: [...document.querySelectorAll("[data-platform-route] th a")].every((link) => {
            const rect = link.getBoundingClientRect();
            return rect.left >= 0 && rect.right <= innerWidth;
          }),
          handoverItems: document.querySelectorAll("[data-facebook-handover] li").length,
          mainText: document.querySelector("main").textContent,
          localLinks: [...new Set([...document.querySelectorAll("main a[href]")].filter((link) => link.origin === location.origin && !link.getAttribute("href").startsWith("#")).map((link) => link.pathname))],
          ids: [...document.querySelectorAll("[id]")].map((node) => node.id),
          overflow: document.documentElement.scrollWidth > innerWidth + 1,
        }));
        assert.equal(content.headline, target.headline);
        assert.equal(content.canonical, `https://shumaojs.com/${target.path}`);
        assert.equal(content.description, content.ogDescription);
        assert.equal(content.description, content.twitterDescription);
        assert.equal(content.typeCards, 9);
        assert.ok(content.cardImages.every((image) => image.loaded));
        assert.equal(content.overflow, false);
        assert.equal(new Set(content.ids).size, content.ids.length);
        assert.ok(content.mainText.includes("Meta") && content.mainText.includes("Facebook"));
        if (target.path === "managed-ads.html") {
          assert.equal(content.routeLinksInFirstColumn, true);
          assert.deepEqual(content.routes, [
            { key: "google", href: "google-ads.html" }, { key: "meta", href: "meta-ads.html" },
            { key: "facebook", href: "facebook-ads.html" }, { key: "x", href: "x-ads.html" },
          ]);
          assert.ok(content.mainText.includes("不把商品 Feed 当作所有项目的前提"));
          assert.ok(content.mainText.includes("不表示每个项目自动包含全部工作"));
          await page.locator('main a[href="#platform-choice"]').click();
        } else {
          await page.goto(new URL(`${target.path}#${target.section}`, base).href, { waitUntil: "networkidle" });
          assert.equal(await page.locator(`#${target.section} a[href="managed-ads.html#platform-choice"]`).count(), 1);
          const other = target.path === "meta-ads.html" ? "facebook-ads.html" : "meta-ads.html";
          assert.equal(await page.locator(`#${target.section} a[href="${other}"]`).count(), 1);
          if (target.path === "facebook-ads.html") assert.equal(content.handoverItems, 3);
        }
        await page.waitForFunction((id) => {
          const rect = document.getElementById(id).getBoundingClientRect();
          return rect.top >= document.querySelector("header").getBoundingClientRect().bottom - 1 && rect.top < 180;
        }, target.section);
        if (width === 1440) {
          for (const pathname of content.localLinks) assert.equal((await context.request.get(new URL(pathname, base).href)).status(), 200, pathname);
        }
        if (width === 1440 || width === 390) await page.screenshot({ path: path.join(output, `${target.path}-${width}.png`) });
        if (target.path === "managed-ads.html" && width <= 390) {
          const table = page.getByRole("region", { name: "广告平台与服务需求选择", exact: true });
          await table.focus();
          await page.keyboard.press("ArrowRight");
          await page.waitForFunction(() => document.activeElement.scrollLeft > 0);
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
          assert.equal(await menu.getAttribute("aria-expanded"), "false");
          assert.equal(await dropdown.getAttribute("aria-expanded"), "false");
        }
        results.push({ width, path: target.path, ...content, mainText: undefined, anchorClear: true, passed: true });
        console.log(`Passed ${target.path} ${width}px`);
      }
      await context.close();
    }
    const staticContext = await browser.newContext({ viewport: { width: 390, height: 900 }, javaScriptEnabled: false });
    const staticPage = await staticContext.newPage();
    await staticPage.goto(new URL("managed-ads.html", base).href, { waitUntil: "load", timeout: 45000 });
    assert.equal(await staticPage.locator("[data-platform-route] th a").count(), 4);
    for (const link of await staticPage.locator("[data-platform-route] th a").all()) assert.equal(await link.isVisible(), true);
    assert.equal(await staticPage.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
    results.push({ width: 390, path: "managed-ads.html", javascript: false, visibleStaticRoutes: 4, passed: true });
    await staticContext.close();
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, "browser.json"), JSON.stringify({ checkedAt: new Date().toISOString(), base: base.href, results, pageErrors: errors }, null, 2) + "\n");
  } finally { await browser.close(); }
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
