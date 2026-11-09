const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const sharp = require(process.env.SHARP_MODULE || "sharp");

const pages = ["google-search-keywords", "conversion-tracking-basics", "landing-page-checklist", "google-search-ads-guide", "seo-title-meta-basics"];
const [base, output, baselinePath] = process.argv.slice(2);
assert.ok(base && output, "Usage: node check_article_cover_density.cjs BASE OUTPUT [baseline.json|--observe]");
const observe = baselinePath === "--observe";
const baseline = baselinePath && !observe ? JSON.parse(fs.readFileSync(baselinePath, "utf8")) : null;

async function main() {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH });
  const results = [], errors = [];
  try {
    for (const slug of pages) {
      const cases = observe ? [[390, 2, true]] : [[1440, 1, true], [390, 1, true], [390, 2, true], [320, 2, true], [390, 2, false]];
      for (const [width, dpr, javaScriptEnabled] of cases) {
        const context = await browser.newContext({ viewport: { width, height: 900 }, deviceScaleFactor: dpr, javaScriptEnabled, reducedMotion: "reduce" });
        const page = await context.newPage();
        page.on("pageerror", error => errors.push(`${slug}/${width}/${dpr}: ${error.message}`));
        if (!javaScriptEnabled) await page.route("**/styles.css", async route => {
          await new Promise(resolve => setTimeout(resolve, 1500));
          await route.continue();
        });
        const response = await page.goto(new URL(`articles/${slug}.html`, base).href, { waitUntil: "load", timeout: 45000 });
        assert.equal(response.status(), 200);
        await page.locator(".article-cover").evaluate(image => image.decode());
        const content = await page.evaluate(source => {
          const parsed = new DOMParser().parseFromString(source, "text/html");
          for (const node of parsed.querySelectorAll("picture source")) {
            node.removeAttribute("srcset");
            node.removeAttribute("sizes");
          }
          // The public edge appends its own beacon; it is not repository HTML.
          const edgeBeacons = [...parsed.querySelectorAll('script[data-cf-beacon][src^="https://static.cloudflareinsights.com/beacon.min.js/"]')];
          for (const node of edgeBeacons) node.remove();
          const walker = parsed.createTreeWalker(parsed.documentElement, NodeFilter.SHOW_TEXT);
          const spacing = [];
          while (walker.nextNode()) if (!walker.currentNode.textContent.trim()) spacing.push(walker.currentNode);
          for (const node of spacing) node.remove();
          const image = document.querySelector(".article-cover"), box = image.getBoundingClientRect();
          const schema = [...document.querySelectorAll('script[type="application/ld+json"]')].map(n => JSON.parse(n.textContent)).find(n => n["@type"] === "Article");
          return {
            protectedHtml: parsed.documentElement.outerHTML,
            excludedEdgeBeacons: edgeBeacons.length,
            canonical: document.querySelector('link[rel="canonical"]').href,
            title: document.title, published: schema.datePublished, modified: schema.dateModified,
            cssReady: [...document.styleSheets].some(s => s.href?.endsWith("/styles.css") && s.cssRules.length > 0),
            src: image.currentSrc, renderedWidth: box.width, renderedHeight: box.height,
            overflow: document.documentElement.scrollWidth > innerWidth + 1,
          };
        }, await response.text());
        const { protectedHtml, ...result } = content;
        result.protectedHash = crypto.createHash("sha256").update(protectedHtml).digest("hex");
        assert.equal(result.cssReady, true);
        assert.equal(result.overflow, false);
        assert.ok(Math.abs(result.renderedWidth / result.renderedHeight - 16 / 9) < 0.01);
        assert.equal(result.canonical, `https://shumaojs.com/articles/${slug}.html`);
        const imageResponse = await context.request.get(result.src);
        assert.equal(imageResponse.status(), 200);
        const bytes = await imageResponse.body();
        const metadata = await sharp(bytes).metadata();
        result.decodedWidth = metadata.width;
        result.bytes = bytes.length;
        result.pixelCoverage = result.decodedWidth / (result.renderedWidth * dpr);
        if (!observe) assert.ok(result.pixelCoverage >= 0.95, JSON.stringify({ slug, width, dpr, ...result }));
        if (baseline) {
          const previous = baseline.results.find(row => row.slug === slug);
          assert.ok(previous, slug);
          assert.equal(result.protectedHash, previous.protectedHash, `${slug}: HTML outside source srcset/sizes changed`);
        }
        if (slug === pages[0] && (width === 1440 || width === 390)) {
          await page.screenshot({ path: path.join(output, `${slug}-${width}-dpr${dpr}-${javaScriptEnabled ? "js" : "nojs"}.png`) });
        }
        results.push({ slug, width, dpr, javaScriptEnabled, ...result });
        console.log(`${slug}: ${width}px DPR${dpr} ${javaScriptEnabled ? "JS" : "noJS"}, ${result.decodedWidth}px / ${result.renderedWidth}px, coverage ${result.pixelCoverage.toFixed(2)}`);
        await context.close();
      }
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, "browser.json"), JSON.stringify({ checkedAt: new Date().toISOString(), base, observe, results, pageErrors: errors }, null, 2) + "\n");
  } finally {
    await browser.close();
  }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
