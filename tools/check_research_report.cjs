const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const report = path.resolve(process.argv[2] || "reports/collected-articles.html");
const output = process.argv[3];
assert.ok(output, "Provide an evidence directory");
const expected = JSON.parse(fs.readFileSync("data/collected-articles.json", "utf8")).items.length;

async function main() {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH, headless: true });
  const results = [], errors = [], externalRequests = [];
  try {
    for (const [width, javaScriptEnabled] of [[1440, true], [768, true], [390, true], [320, true], [390, false]]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, javaScriptEnabled, reducedMotion: "reduce" });
      const page = await context.newPage();
      page.on("pageerror", error => errors.push(error.message));
      page.on("request", request => { if (/^https?:/.test(request.url())) externalRequests.push(request.url()); });
      await page.goto(pathToFileURL(report).href, { waitUntil: "load" });
      const content = await page.evaluate(() => ({ cards: document.querySelectorAll(".collector-card").length,
        images: document.images.length, scripts: document.scripts.length,
        overflow: document.documentElement.scrollWidth > innerWidth + 1,
        links: [...document.querySelectorAll(".collector-card a")].map(a => a.href),
        pendingLabels: [...document.querySelectorAll(".collector-card p")].filter(n => n.textContent.includes("待分别确认")).length,
        clippedHeadings: [...document.querySelectorAll("h1,h2,h3")].filter(n => n.scrollWidth > n.clientWidth + 1).length }));
      assert.equal(content.cards, expected);
      assert.equal(content.images, 0);
      assert.equal(content.scripts, 0);
      assert.equal(content.pendingLabels, expected);
      assert.equal(content.overflow, false);
      assert.equal(content.clippedHeadings, 0);
      for (const href of content.links) {
        const url = new URL(href);
        assert.ok(["http:", "https:"].includes(url.protocol));
        assert.equal(url.username, "");
        assert.equal(url.password, "");
      }
      if ([1440,390].includes(width)) await page.screenshot({ path: path.join(output, `research-${width}-${javaScriptEnabled ? "js" : "nojs"}.png`) });
      results.push({ width, javaScriptEnabled, ...content });
      await context.close();
      console.log(`Passed research report ${width}px/${javaScriptEnabled ? "JS" : "noJS"}`);
    }
    assert.deepEqual(errors, []);
    assert.deepEqual(externalRequests, []);
    fs.writeFileSync(path.join(output, "browser.json"), JSON.stringify({ checkedAt: new Date().toISOString(), results, errors, externalRequests }, null, 2) + "\n");
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
