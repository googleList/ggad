const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const base = new URL(process.argv[2] || "http://127.0.0.1:8795/");
const output = process.argv[3] || path.join(os.tmpdir(), "shumao-hk-audit-check");
const articlePath = "articles/google-ads-account-audit-hong-kong.html";

async function main() {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH });
  const results = [], errors = [];
  try {
    for (const [width, javaScriptEnabled] of [[1440, true], [768, true], [390, true], [320, true], [1440, false], [390, false]]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, javaScriptEnabled, reducedMotion: "reduce" });
      const page = await context.newPage();
      page.setDefaultTimeout(15000);
      page.on("pageerror", (error) => errors.push(`${width}/${javaScriptEnabled}: ${error.message}`));
      assert.equal((await page.goto(new URL(articlePath, base).href, { waitUntil: "networkidle", timeout: 45000 })).status(), 200);
      const content = await page.evaluate(() => {
        const main = document.querySelector("main"), img = main.querySelector(".article-cover");
        const schema = [...document.querySelectorAll('script[type="application/ld+json"]')].map((n) => JSON.parse(n.textContent)).find((s) => s["@type"] === "Article");
        return { title: document.title, headline: main.querySelector("h1").textContent, lang: document.documentElement.lang,
          schema, canonical: document.querySelector('link[rel="canonical"]').href,
          alternates: [...document.querySelectorAll("link[hreflang]")].map((n) => ({ lang: n.hreflang, href: n.href })),
          descriptions: [document.querySelector('meta[name="description"]').content, document.querySelector('meta[property="og:description"]').content, document.querySelector('meta[name="twitter:description"]').content, schema.description],
          image: { src: img.currentSrc, loaded: img.complete && img.naturalWidth > 0, ratio: img.width / img.height,
            og: document.querySelector('meta[property="og:image"]').content, twitter: document.querySelector('meta[name="twitter:image"]').content },
          modified: main.querySelector("time").dateTime, baseline: main.querySelectorAll("[data-hk-baseline] > li").length,
          evidence: [...main.querySelectorAll("[data-hk-evidence]")].map((n) => n.dataset.hkEvidence),
          boundaries: ["廣告活動使用的自訂目標", "不能證明對方已傳送訊息", "電話連結點擊不等於接通", "不是可直接套用的否定詞庫", "不要一律改成", "分母為零而無法計算", "不編造逐詞歸因"].map((text) => ({ text, present: main.textContent.includes(text) })),
          anchors: [...main.querySelectorAll("nav a")].map((n) => n.getAttribute("href")),
          ids: [...document.querySelectorAll("[id]")].map((n) => n.id),
          links: [...new Set([...main.querySelectorAll("a[href]")].filter((n) => n.origin === location.origin && !n.getAttribute("href").startsWith("#")).map((n) => n.pathname))],
          overflow: document.documentElement.scrollWidth > innerWidth + 1 };
      });
      assert.equal(content.title, "香港 Google Ads 帳戶審核清單：投放、追蹤及預算檢查");
      assert.equal(content.headline, "香港 Google Ads 帳戶審核清單");
      assert.equal(content.lang, "zh-Hant-HK");
      assert.equal(content.schema.headline, content.headline);
      assert.equal(content.schema.datePublished, "2026-09-28");
      assert.equal(content.modified, "2026-10-26T12:48:52+08:00");
      assert.equal(content.modified, content.schema.dateModified);
      assert.equal(content.canonical, "https://shumaojs.com/" + articlePath);
      assert.ok(content.alternates.some((n) => n.lang === "en-US" && n.href.endsWith("google-ads-account-audit-usa.html")));
      assert.equal(new Set(content.descriptions).size, 1);
      assert.equal(content.image.loaded, true);
      assert.ok(content.image.src.endsWith(width <= 600 ? "evidence-thumb-v1.webp" : "evidence-v1.jpg"));
      assert.ok(Math.abs(content.image.ratio - 16 / 9) < 0.01);
      assert.equal(content.image.og, content.schema.image);
      assert.equal(content.image.twitter, content.schema.image);
      assert.equal(content.baseline, 3);
      assert.deepEqual(content.evidence, ["chat", "form", "sales"]);
      assert.ok(content.boundaries.every((b) => b.present));
      assert.equal(content.overflow, false);
      assert.equal(content.anchors.length, 3);
      assert.equal(new Set(content.ids).size, content.ids.length);
      for (const href of content.anchors) {
        await page.locator(`main nav a[href="${href}"]`).click();
        assert.equal(await page.locator(href).evaluate((n) => n.getBoundingClientRect().top >= document.querySelector("header").getBoundingClientRect().bottom - 1 && n.getBoundingClientRect().top < 190), true, href);
      }
      if (width <= 390) {
        const region = page.getByRole("region", { name: "香港查詢證據與審核行動", exact: true });
        await region.scrollIntoViewIfNeeded(); await region.focus(); await page.keyboard.press("ArrowRight");
        let moved = false;
        for (let n = 0; n < 30; n += 1) {
          moved = await region.evaluate((el) => document.activeElement === el && el.scrollLeft > 0);
          if (moved) break;
          await new Promise((resolve) => setTimeout(resolve, 50));
        }
        assert.equal(moved, true);
        if (javaScriptEnabled) {
          await page.evaluate(() => scrollTo(0, 0));
          const menu = page.locator(".mobile-menu-toggle");
          await menu.click(); assert.equal(await menu.getAttribute("aria-expanded"), "true");
          await menu.click(); assert.equal(await menu.getAttribute("aria-expanded"), "false");
        }
      }
      if (width === 1440 && javaScriptEnabled) for (const target of content.links) assert.equal((await context.request.get(new URL(target, base).href)).status(), 200, target);
      if (width === 1440 || width === 390) {
        const suffix = javaScriptEnabled ? "js" : "nojs";
        await page.goto(new URL(articlePath, base).href, { waitUntil: "networkidle" });
        await page.screenshot({ path: path.join(output, `article-${width}-${suffix}.png`) });
        await page.locator('main nav a[href="#conversion-evidence"]').click();
        await page.getByRole("region", { name: "香港查詢證據與審核行動", exact: true }).scrollIntoViewIfNeeded();
        await page.screenshot({ path: path.join(output, `evidence-${width}-${suffix}.png`) });
      }
      await page.goto(new URL("articles.html", base).href, { waitUntil: "networkidle" });
      const card = page.locator("[data-article-card]").filter({ has: page.locator(`h3 a[href="${articlePath}"]`) });
      let listingPage = null;
      if (javaScriptEnabled) {
        await page.locator('[data-article-category-button][data-article-category="sem"]').click(); listingPage = 1;
        while (!await card.isVisible()) {
          assert.ok(listingPage < 7); const next = page.locator(".pagination button").last();
          assert.equal(await next.isDisabled(), false); await next.click(); listingPage += 1;
        }
      }
      assert.equal(await card.isVisible(), true);
      assert.ok((await card.locator("small").textContent()).startsWith("2026-10-26"));
      await card.locator("img").scrollIntoViewIfNeeded(); await card.locator("img").evaluate((img) => img.decode());
      assert.ok((await card.locator("img").getAttribute("src")).endsWith("account-audit-evidence-thumb-v1.webp"));
      await card.locator("h3 a").click(); assert.equal(new URL(page.url()).pathname, "/" + articlePath);
      results.push({ width, javaScriptEnabled, ...content, listingPage });
      await context.close(); console.log(`Passed HK audit ${width}px/${javaScriptEnabled ? "JS" : "noJS"}`);
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, "browser.json"), JSON.stringify({ checkedAt: new Date().toISOString(), base: base.href, results, pageErrors: errors }, null, 2) + "\n");
  } finally { await browser.close(); }
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
