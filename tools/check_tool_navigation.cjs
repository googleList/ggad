const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");

const base = new URL(process.argv[2] || "http://127.0.0.1:8765/");
const output = process.argv[3] || path.join(os.tmpdir(), "shumao-tool-navigation");

async function main() {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH });
  const results = [];
  const errors = [];
  const selected = (page) => page.locator('[data-tool-tab][aria-selected="true"]').getAttribute("data-tool-tab");
  const checkSelection = async (page, name, hash) => {
    await page.locator(`[data-tool-tab="${name}"][aria-selected="true"]`).waitFor();
    assert.equal(await selected(page), name);
    assert.equal(new URL(page.url()).hash, hash);
    assert.equal(await page.locator('[data-tool-panel]:visible').count(), 1);
    assert.equal(await page.locator('[data-tool-tab][tabindex="0"]').count(), 1);
    assert.equal(await page.locator('[data-tool-jump][aria-current="location"]').count(), 1);
    assert.ok(await page.locator(`[data-tool-jump="${name}"].is-active`).count());
  };
  try {
    for (const width of [1440, 768, 390, 320]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: "reduce" });
      const page = await context.newPage();
      page.on("pageerror", (error) => errors.push(`${width}px: ${error.message}`));
      const response = await page.goto(new URL("nav.html#standard-seo", base).href);
      assert.equal(response.status(), 200);
      await checkSelection(page, "standard", "#standard-seo");
      await page.locator('[data-tool-tab="ai"]').click();
      await checkSelection(page, "ai", "#panel-ai-tools");
      await page.reload();
      await checkSelection(page, "ai", "#panel-ai-tools");
      await page.goBack();
      await checkSelection(page, "standard", "#standard-seo");
      await page.goForward();
      await checkSelection(page, "ai", "#panel-ai-tools");

      const jumps = await page.locator("[data-tool-jump]").evaluateAll((links) =>
        links.map((link) => ({ hash: link.getAttribute("href"), panel: link.dataset.toolJump })));
      for (const { hash, panel } of jumps) {
        await page.locator(`[data-tool-jump][href="${hash}"]`).click();
        await checkSelection(page, panel, hash);
        assert.ok(await page.locator(hash).isVisible());
        assert.equal(await page.locator('[data-tool-jump][aria-current="location"]').getAttribute("href"), hash);
        const covered = await page.locator(hash).evaluate((target) => {
          const blocker = document.querySelector(innerWidth <= 980 ? ".tool-side-nav" : "header");
          return target.getBoundingClientRect().top < blocker.getBoundingClientRect().bottom + 7;
        });
        assert.equal(covered, false, `${width}px ${hash} is covered by sticky navigation`);
      }
      await page.goBack();
      await checkSelection(page, "standard", jumps.at(-2).hash);
      await page.goForward();
      await checkSelection(page, "standard", jumps.at(-1).hash);

      const tab = page.locator('[data-tool-tab="standard"]');
      await tab.focus();
      await page.keyboard.press("ArrowRight");
      await checkSelection(page, "ai", "#panel-ai-tools");
      assert.equal(await page.locator(":focus").getAttribute("data-tool-tab"), "ai");
      await page.keyboard.press("ArrowLeft");
      await checkSelection(page, "standard", "#panel-standard-tools");
      await page.keyboard.press("Home");
      await checkSelection(page, "ai", "#panel-ai-tools");
      await page.keyboard.press("End");
      await checkSelection(page, "standard", "#panel-standard-tools");
      await page.keyboard.press("Tab");
      assert.equal(await page.locator(":focus").getAttribute("data-tool-panel"), "standard");

      await page.evaluate(() => { location.hash = "#ai-copy"; });
      await checkSelection(page, "ai", "#ai-copy");
      await page.evaluate(() => { location.hash = "#%E0%A4%A"; });
      assert.equal(await selected(page), "ai");
      await page.evaluate(() => { location.hash = ""; });
      await page.locator('[data-tool-jump][href="#ai-search"][aria-current="location"]').waitFor();
      assert.equal(await selected(page), "ai");
      await page.evaluate(() => scrollTo(0, 0));
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
      assert.equal(overflow, false);
      await page.screenshot({ path: path.join(output, `tools-${width}.png`) });
      results.push({ width, mode: "javascript", anchors: jumps.length, deepLinkReload: true,
        tabReload: true, backForward: true, keyboard: true, hashChange: true, malformedHash: true, overflow });
      await context.close();
    }

    for (const mode of ["no-javascript", "tool-script-blocked"]) {
      for (const width of [1440, 390]) {
        const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: "reduce", javaScriptEnabled: mode !== "no-javascript" });
        if (mode === "tool-script-blocked") await context.route("**/assets/tool-navigation-v1.js", (route) => route.abort());
        const page = await context.newPage();
        page.on("pageerror", (error) => errors.push(`${mode}/${width}px: ${error.message}`));
        await page.goto(new URL("nav.html#standard-seo", base).href);
        assert.equal(await page.locator(".tool-tabs").isVisible(), false);
        assert.equal(await page.locator("[data-tool-panel]:visible").count(), 2);
        const links = await page.locator('[data-tool-panel="standard"] a:visible').count();
        assert.ok(links > 20);
        await page.locator('[data-tool-jump][href="#standard-keywords"]').focus();
        await page.keyboard.press("Enter");
        assert.equal(new URL(page.url()).hash, "#standard-keywords");
        assert.ok(await page.locator("#standard-keywords").isVisible());
        const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
        assert.equal(overflow, false);
        await page.screenshot({ path: path.join(output, `${mode}-${width}.png`) });
        results.push({ width, mode, visiblePanels: 2, standardLinks: links, nativeAnchors: true, overflow });
        await context.close();
      }
    }

    const fileContext = await browser.newContext({ viewport: { width: 390, height: 900 }, reducedMotion: "reduce" });
    const filePage = await fileContext.newPage();
    filePage.on("pageerror", (error) => errors.push(`local-file: ${error.message}`));
    const fileUrl = pathToFileURL(path.resolve(__dirname, "../nav.html"));
    fileUrl.hash = "standard-seo";
    await filePage.goto(fileUrl.href);
    await checkSelection(filePage, "standard", "#standard-seo");
    await filePage.locator('[data-tool-tab="ai"]').click();
    await checkSelection(filePage, "ai", "#panel-ai-tools");
    await filePage.reload();
    await checkSelection(filePage, "ai", "#panel-ai-tools");
    results.push({ width: 390, mode: "local-file", deepLink: true, tabReload: true });
    await fileContext.close();

    const motionContext = await browser.newContext({ viewport: { width: 390, height: 900 } });
    const motionPage = await motionContext.newPage();
    motionPage.on("pageerror", (error) => errors.push(`normal-motion: ${error.message}`));
    await motionPage.goto(new URL("nav.html#standard-seo", base).href);
    await motionPage.evaluate(() => document.fonts.ready);
    await motionPage.waitForFunction(() => Math.abs(document.querySelector("#standard-seo").getBoundingClientRect().top - 160) < 2);
    const anchorLayout = await motionPage.evaluate(() => ({
      targetTop: document.querySelector("#standard-seo").getBoundingClientRect().top,
      stickyBottom: document.querySelector(".tool-side-nav").getBoundingClientRect().bottom,
    }));
    assert.ok(anchorLayout.targetTop >= anchorLayout.stickyBottom + 7);
    await motionPage.screenshot({ path: path.join(output, "tools-anchor-normal-motion-390.png") });
    results.push({ width: 390, mode: "normal-motion", ...anchorLayout, anchorUnobscured: true });
    await motionContext.close();
    assert.deepEqual(errors, []);
    const evidence = { checkedAt: new Date().toISOString(), base: base.href, results, pageErrors: errors };
    fs.writeFileSync(path.join(output, "browser.json"), JSON.stringify(evidence, null, 2) + "\n");
    console.log(JSON.stringify(evidence));
  } finally {
    await browser.close();
  }
}

main().catch((error) => { console.error(error); process.exitCode = 1; });
