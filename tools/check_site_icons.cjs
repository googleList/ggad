const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");

const root = path.resolve(__dirname, "..");
const base = new URL(process.argv[2] || "http://127.0.0.1:8765/");
const output = process.argv[3] || path.join(os.tmpdir(), "shumao-icon-check");
const manifest = JSON.parse(fs.readFileSync(path.join(root, "assets/icons/manifest.json"), "utf8"));

async function inspect(page) {
  await page.waitForFunction(() => {
    const sheet = [...document.querySelectorAll('link[rel="stylesheet"]')]
      .find((link) => link.href.includes("tabler-subset-v1.css"));
    return sheet && sheet.media === "all";
  });
  await page.evaluate(() => document.fonts.ready);
  return page.evaluate((glyphs) => {
    const errors = [];
    const icons = [...document.querySelectorAll("[data-site-icon]")];
    if (!icons.length) errors.push("No icons were inserted");
    const font = [...document.fonts].find((face) => face.family.replaceAll('"', "") === "tabler-icons");
    if (!font || font.status !== "loaded") errors.push("Local icon font did not load");
    for (const icon of icons) {
      const name = [...icon.classList].find((value) => value.startsWith("ti-"))?.slice(3);
      const content = getComputedStyle(icon, "::before").content.replaceAll('"', "");
      const codepoint = content.codePointAt(0)?.toString(16);
      if (!glyphs[name] || glyphs[name] !== codepoint) errors.push(`Missing glyph: ${name}`);
    }
    if (document.documentElement.scrollWidth > innerWidth + 1) errors.push("Horizontal overflow");
    const hero = document.querySelector(".hero-background-media img");
    if (hero && getComputedStyle(hero).objectFit !== "cover") errors.push("Hero image is stretched");
    return {
      count: icons.length, names: [...new Set(icons.map((icon) => icon.className))], errors,
      heroImage: hero ? { source: hero.currentSrc, naturalWidth: hero.naturalWidth, loaded: hero.complete && hero.naturalWidth > 0 } : undefined,
    };
  }, manifest.glyphs);
}

async function capture(page, file) {
  await page.locator("img").evaluateAll((images) => Promise.all(images
    .filter((image) => image.loading !== "lazy" && image.getBoundingClientRect().top < innerHeight)
    .map((image) => image.decode())));
  await page.screenshot({ path: file });
}

async function main() {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH });
  const results = [];
  const failedIconRequests = [];
  try {
    const desktop = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const page = await desktop.newPage();
    page.setDefaultTimeout(15000);
    page.setDefaultNavigationTimeout(45000);
    page.on("requestfailed", (request) => {
      if (/tabler|icons\/.*woff/.test(request.url())) failedIconRequests.push(request.url());
    });
    await page.goto(new URL("sitemap.xml", base).href, { waitUntil: "domcontentloaded" });
    const urls = await page.evaluate(() => [...document.querySelectorAll("loc")].map((node) => node.textContent));
    if (!urls.length) throw new Error("The sitemap contains no URLs");
    for (const url of urls) {
      const pathname = new URL(url).pathname;
      const response = await page.goto(new URL(pathname, base).href, { waitUntil: "domcontentloaded" });
      if (!response || response.status() !== 200) throw new Error(`HTTP ${response?.status()}: ${pathname}`);
      if (pathname === "/" || pathname === "/google-ads.html") {
        await capture(page, path.join(output, `${pathname === "/" ? "home" : "service"}-desktop.png`));
      }
      const result = { path: pathname, viewport: "desktop", httpStatus: response.status(), ...(await inspect(page)) };
      results.push(result);
      if (results.length % 10 === 0) console.log(`Checked ${results.length}/${urls.length} desktop pages`);
    }
    const mobile = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true });
    const phone = await mobile.newPage();
    phone.setDefaultNavigationTimeout(45000);
    for (const pathname of ["/", "/google-ads.html", "/articles.html", "/articles/google-ads-basics.html", "/nav.html"]) {
      await phone.goto(new URL(pathname, base).href, { waitUntil: "domcontentloaded" });
      if (pathname === "/" || pathname === "/google-ads.html") {
        await capture(phone, path.join(output, `${pathname === "/" ? "home" : "service"}-mobile.png`));
      }
      const toggle = phone.locator(".mobile-menu-toggle");
      await toggle.click();
      if (await toggle.getAttribute("aria-expanded") !== "true") throw new Error(`Menu did not open: ${pathname}`);
      results.push({ path: pathname, viewport: "mobile-menu-open", ...(await inspect(phone)) });
      const dropdown = phone.locator(".nav-drop-toggle").first();
      if (await dropdown.count()) {
        await dropdown.click();
        if (await dropdown.getAttribute("aria-expanded") !== "true") throw new Error(`Dropdown did not open: ${pathname}`);
      }
      await toggle.click();
      if (await toggle.getAttribute("aria-expanded") !== "false") throw new Error(`Menu did not close: ${pathname}`);
      results.push({ path: pathname, viewport: "mobile-menu-closed", ...(await inspect(phone)) });
    }
    for (const relative of ["index.html", "articles/google-ads-basics.html"]) {
      await page.goto(pathToFileURL(path.join(root, relative)).href, { waitUntil: "domcontentloaded" });
      results.push({ path: relative, viewport: "local-file", ...(await inspect(page)) });
    }
    for (const viewport of [{ width: 320, height: 740 }, { width: 2560, height: 1440 }]) {
      await page.setViewportSize(viewport);
      await page.goto(base.href, { waitUntil: "domcontentloaded" });
      await capture(page, path.join(output, `home-${viewport.width}.png`));
      results.push({ path: "/", viewport: `${viewport.width}x${viewport.height}`, ...(await inspect(page)) });
    }
    await page.locator('.hero-background-media source').evaluateAll((sources) => sources.forEach((source) => source.remove()));
    await page.locator('.hero-background-media img').evaluate((image) => image.decode());
    const fallback = await inspect(page);
    if (!fallback.heroImage.loaded || !fallback.heroImage.source.endsWith(".jpg")) fallback.errors.push("JPEG hero fallback failed");
    results.push({ path: "/", viewport: "jpeg-fallback", ...fallback });
    const stableContext = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true });
    const stablePage = await stableContext.newPage();
    stablePage.setDefaultNavigationTimeout(45000);
    let releaseScript;
    const scriptGate = new Promise((resolve) => { releaseScript = resolve; });
    await stablePage.route("**/site-v20260930.js", async (route) => {
      await scriptGate;
      await route.continue();
    });
    const navigation = stablePage.goto(new URL("google-ads.html", base).href, { waitUntil: "domcontentloaded" });
    let beforeTop;
    try {
      await stablePage.waitForFunction(() => document.querySelector('link[href*="styles.css"]')?.sheet
        && document.querySelector(".managed-visual"));
      beforeTop = await stablePage.locator(".managed-visual").evaluate((node) => node.getBoundingClientRect().top);
    } finally {
      releaseScript();
    }
    await navigation;
    const stability = await inspect(stablePage);
    const afterTop = await stablePage.locator(".managed-visual").evaluate((node) => node.getBoundingClientRect().top);
    const shift = Math.abs(afterTop - beforeTop);
    if (shift > 1) stability.errors.push(`Hero moved ${shift}px after icon insertion`);
    results.push({ path: "/google-ads.html", viewport: "delayed-script-mobile", shiftPixels: shift, ...stability });
    if (process.argv.includes("--public-artifact")) {
      const excluded = ["/reports/seo-growth-state.json", "/scripts/seo_quality_check.py",
        "/tests/test_structured_data_check.py", "/data/collected-articles.json", "/data/seo-keywords.json"];
      for (const pathname of excluded) {
        for (const cacheBust of [false, true]) {
          const url = new URL(pathname, base);
          if (cacheBust) url.searchParams.set("audit", "public-artifact-20261020");
          const response = await desktop.request.get(url.href, { maxRedirects: 0, timeout: 30000 });
          results.push({ path: pathname, viewport: cacheBust ? "publication-cache-busted" : "publication-scope",
            httpStatus: response.status(), errors: response.status() === 404 ? [] : ["Repository-only file is publicly served"] });
        }
      }
      for (const pathname of ["/styles.css", "/site-v20260930.js", "/budget-calculator.js", "/favicon.ico",
        "/CNAME", "/robots.txt", "/sitemap.xml", "/feed.xml", "/site.webmanifest", "/llms.txt",
        "/data/ad-learning.json", "/assets/icons/tabler-subset-v1.woff2"]) {
        const response = await desktop.request.get(new URL(pathname, base).href, { timeout: 30000 });
        results.push({ path: pathname, viewport: "public-resource", httpStatus: response.status(),
          errors: response.status() === 200 ? [] : ["Required public resource is missing"] });
      }
    }
    const report = { generatedAt: new Date().toISOString(), base: base.href, results, failedIconRequests };
    fs.writeFileSync(path.join(output, "results.json"), JSON.stringify(report, null, 2) + "\n");
    const failed = results.filter((result) => result.errors.length);
    console.log(JSON.stringify({ checks: results.length, failed, failedIconRequests, output }, null, 2));
    if (failed.length || failedIconRequests.length) process.exitCode = 1;
  } finally {
    await browser.close();
  }
}

main().catch((error) => { console.error(error); process.exitCode = 1; });
