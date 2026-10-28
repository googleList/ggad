const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const sharp = require(process.env.SHARP_MODULE || "sharp");

const base = new URL(process.argv[2]);
const output = process.argv[3];
const baseline = process.argv[4] === "baseline";
assert.ok(output, "Provide an evidence directory");

async function main() {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH, headless: true });
  const results = [], pageErrors = [];
  try {
    for (const [width, dpr] of [[320, 2], [390, 2], [700, 1], [701, 1], [768, 1], [768, 2], [980, 2], [981, 1], [1236, 1], [1237, 1], [1440, 1], [2560, 1]]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, deviceScaleFactor: dpr, reducedMotion: "reduce" });
      try {
        const page = await context.newPage();
        page.setDefaultTimeout(30000);
        page.setDefaultNavigationTimeout(45000);
        page.on("pageerror", error => pageErrors.push(`${width}/${dpr}: ${error.message}`));
        const images = [], pending = [];
        page.on("response", response => {
          if (!response.url().includes("photo-1460925895917-afdab827c52f")) return;
          pending.push((async () => {
            const bytes = await response.body();
            const meta = await sharp(bytes).metadata();
            images.push({ url: response.url(), status: response.status(), bodyBytes: bytes.length,
              pixelWidth: meta.width, pixelHeight: meta.height, format: meta.format });
          })());
        });
        assert.equal((await page.goto(new URL("index.html", base).href, { waitUntil: "domcontentloaded" })).status(), 200);
        await page.waitForFunction(() => [...document.styleSheets].some(sheet => sheet.href && new URL(sheet.href).pathname.endsWith("/styles.css")));
        await page.locator(".hero-background-media img").evaluate(img => img.decode());
        const hero = await page.locator(".hero-background-media img").evaluate(img => ({ src: img.currentSrc,
          loaded: img.naturalWidth > 0, objectFit: getComputedStyle(img).objectFit }));
        const image = page.locator("#policy .policy-image img");
        await image.scrollIntoViewIfNeeded();
        await image.evaluate(img => img.decode());
        const policy = await image.evaluate(img => ({ src: img.currentSrc, sizes: img.sizes,
          renderedWidth: img.getBoundingClientRect().width, renderedHeight: img.getBoundingClientRect().height,
          loaded: img.complete && img.naturalWidth > 0, objectFit: getComputedStyle(img).objectFit,
          requiredPixelWidth: Math.ceil(img.getBoundingClientRect().width * devicePixelRatio) }));
        await Promise.all(pending);
        const response = images.find(item => item.url === policy.src);
        assert.ok(response, "Decoded image response must be measured");
        const result = { width, dpr, hero, policy, response,
          enoughPixels: response.pixelWidth >= policy.requiredPixelWidth * 0.95,
          overflow: await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1) };
        assert.equal(hero.objectFit, "cover");
        assert.equal(policy.objectFit, "cover");
        assert.equal(result.overflow, false);
        if (!baseline) assert.ok(result.enoughPixels, `${width}px/DPR${dpr}: image candidate is too small`);
        if ([390, 768, 2560].includes(width)) await page.screenshot({ path: path.join(output, `policy-${width}-dpr${dpr}.png`) });
        results.push(result);
        console.log(JSON.stringify({ width, dpr, rendered: policy.renderedWidth, requested: response.pixelWidth,
          bytes: response.bodyBytes, enoughPixels: result.enoughPixels }));
      } finally { await context.close(); }
    }
    assert.deepEqual(pageErrors, []);
    fs.writeFileSync(path.join(output, "browser.json"), JSON.stringify({ checkedAt: new Date().toISOString(), base: base.href,
      baseline, measurement: "Isolated browser contexts, no device/network throttling; response body bytes and decoded image dimensions, not CrUX or INP/LCP field measurements", results, pageErrors }, null, 2) + "\n");
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
