const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const base = new URL(process.argv[2] || "http://127.0.0.1:8780/");
const output = process.argv[3] || path.join(os.tmpdir(), "shumao-tracking-guide-check");
const articlePath = "articles/conversion-tracking-basics.html";

async function main() {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH });
  const results = [];
  const errors = [];
  try {
    for (const width of [1440, 768, 390, 320]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: "reduce" });
      const page = await context.newPage();
      page.setDefaultTimeout(15000);
      page.on("pageerror", (error) => errors.push(`${width}px: ${error.message}`));
      assert.equal((await page.goto(new URL(articlePath, base).href, { waitUntil: "networkidle", timeout: 45000 })).status(), 200);
      const content = await page.evaluate(() => {
        const main = document.querySelector("main");
        const schema = [...document.querySelectorAll('script[type="application/ld+json"]')]
          .map((node) => JSON.parse(node.textContent)).find((item) => item["@type"] === "Article");
        const image = main.querySelector(".article-cover");
        return {
          headline: main.querySelector("h1").textContent.trim(), schemaHeadline: schema.headline,
          canonical: document.querySelector('link[rel="canonical"]').href,
          published: schema.datePublished, modified: schema.dateModified, visibleModified: main.querySelector("time").dateTime,
          description: document.querySelector('meta[name="description"]').content, schemaDescription: schema.description,
          cover: { src: image.currentSrc, loaded: image.complete && image.naturalWidth > 0,
            schema: schema.image, og: document.querySelector('meta[property="og:image"]').content,
            twitter: document.querySelector('meta[name="twitter:image"]').content,
            ratio: image.getBoundingClientRect().width / image.getBoundingClientRect().height },
          eventRows: [...main.querySelectorAll("[data-event-row]")].map((row) => ({ event: row.dataset.eventRow, text: row.textContent })),
          goalCases: [...main.querySelectorAll("[data-goal-case]")].map((row) => ({ goal: row.dataset.goalCase, text: row.textContent })),
          implementationChecks: main.querySelectorAll("[data-implementation-checks] li").length,
          validationSteps: main.querySelectorAll("[data-validation-step] > li").length,
          reconciliationSteps: main.querySelectorAll("[data-reconciliation-step] > li").length,
          faqCount: main.querySelectorAll("#questions h3").length,
          anchors: [...main.querySelectorAll("nav a")].map((link) => link.getAttribute("href")),
          ids: [...document.querySelectorAll("[id]")].map((node) => node.id),
          educationalBoundary: main.textContent.includes("不是已部署的追踪方案"),
          localLinks: [...new Set([...main.querySelectorAll("a[href]")].filter((link) => link.origin === location.origin &&
            !link.getAttribute("href").startsWith("#")).map((link) => link.pathname))],
          overflow: document.documentElement.scrollWidth > innerWidth + 1,
        };
      });
      assert.equal(content.headline, "广告转化追踪基础教程");
      assert.equal(content.schemaHeadline, content.headline);
      assert.equal(content.canonical, "https://shumaojs.com/articles/conversion-tracking-basics.html");
      assert.equal(content.published, "2026-09-11");
      assert.equal(content.modified, "2026-10-24T16:52:44+08:00");
      assert.equal(content.visibleModified, content.modified);
      assert.equal(content.description, content.schemaDescription);
      assert.equal(content.cover.loaded, true);
      assert.ok(content.cover.src.endsWith(width <= 600 ? "plan-thumb-v1.webp" : "plan-v1.jpg"));
      assert.equal(content.cover.schema, content.cover.og);
      assert.equal(content.cover.schema, content.cover.twitter);
      assert.ok(Math.abs(content.cover.ratio - 16 / 9) < 0.01);
      assert.deepEqual(content.eventRows.map((row) => row.event), ["page_view", "chat_click", "phone_click", "form_submit", "generate_lead", "qualify_lead"]);
      assert.ok(content.eventRows[1].text.includes("不证明消息发送"));
      assert.ok(content.eventRows[2].text.includes("不是通话记录"));
      assert.ok(content.eventRows[3].text.includes("不能只凭事件名认定送达"));
      assert.deepEqual(content.goalCases.map((row) => row.goal), ["standard-primary", "standard-secondary", "custom"]);
      assert.ok(content.goalCases[2].text.includes("即使标为次要") && content.goalCases[2].text.includes("参与报告和出价"));
      assert.equal(content.implementationChecks, 4);
      assert.equal(content.validationSteps, 5);
      assert.equal(content.reconciliationSteps, 3);
      assert.equal(content.faqCount, 3);
      assert.equal(content.educationalBoundary, true);
      assert.equal(content.anchors.length, 6);
      assert.equal(new Set(content.ids).size, content.ids.length);
      assert.equal(content.overflow, false);
      for (const href of content.anchors) {
        await page.locator(`main nav a[href="${href}"]`).click();
        await page.waitForFunction((selector) => {
          const top = document.querySelector(selector).getBoundingClientRect().top;
          return top >= document.querySelector("header").getBoundingClientRect().bottom - 1 && top < 180;
        }, href);
      }
      if (width <= 390) {
        for (const label of ["六行询盘事件规划示例", "转化动作与广告系列目标核对"]) {
          const table = page.getByRole("region", { name: label, exact: true });
          await table.scrollIntoViewIfNeeded();
          await table.focus();
          await page.keyboard.press("ArrowRight");
          await page.waitForFunction(() => document.activeElement.scrollLeft > 0);
        }
      }
      if (width === 1440) {
        for (const pathname of content.localLinks) assert.equal((await context.request.get(new URL(pathname, base).href)).status(), 200, pathname);
        await page.goto(new URL("google-ads.html", base).href, { waitUntil: "networkidle" });
        assert.equal(await page.locator(`main a[href="${articlePath}"]`).count(), 1);
      }
      if (width === 1440 || width === 390) {
        await page.goto(new URL(articlePath, base).href, { waitUntil: "networkidle" });
        await page.screenshot({ path: path.join(output, `article-${width}.png`) });
        await page.locator('main nav a[href="#conversion-goals"]').click();
        await page.waitForFunction(() => document.querySelector("#conversion-goals").getBoundingClientRect().top < 180);
        await page.screenshot({ path: path.join(output, `goals-${width}.png`) });
      }
      await page.goto(new URL("articles.html", base).href, { waitUntil: "networkidle" });
      await page.locator('[data-article-category-button][data-article-category="sem"]').click();
      const card = page.locator("[data-article-card]").filter({ has: page.locator(`h3 a[href="${articlePath}"]`) });
      let listingPage = 1;
      while (!await card.isVisible()) {
        assert.ok(listingPage < 7);
        const next = page.locator(".pagination button").last();
        assert.equal(await next.isDisabled(), false);
        await next.click();
        listingPage += 1;
      }
      assert.ok((await card.locator("small").textContent()).startsWith("2026-10-24"));
      await card.locator("img").scrollIntoViewIfNeeded();
      await card.locator("img").evaluate((image) => image.decode());
      assert.ok((await card.locator("img").getAttribute("src")).endsWith("plan-thumb-v1.webp"));
      if (width === 1440 || width === 390) await page.screenshot({ path: path.join(output, `listing-${width}.png`) });
      results.push({ width, ...content, anchorsPassed: true, listingPassed: true, listingPage });
      await context.close();
      console.log(`Passed tracking guide ${width}px`);
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, "browser.json"), JSON.stringify({ checkedAt: new Date().toISOString(), base: base.href, results, pageErrors: errors }, null, 2) + "\n");
  } finally { await browser.close(); }
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
