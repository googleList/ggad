const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const base = new URL(process.argv[2] || "http://127.0.0.1:8796/");
const output = process.argv[3] || path.join(os.tmpdir(), "shumao-identity-check");

async function main() {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH });
  const results = [], errors = [];
  try {
    for (const [width, javaScriptEnabled] of [[2560, true], [1440, true], [768, true], [390, true], [320, true], [1440, false], [390, false]]) {
      const context = await browser.newContext({ viewport: { width, height: 1000 }, javaScriptEnabled, reducedMotion: "reduce" });
      const page = await context.newPage();
      page.setDefaultTimeout(15000);
      page.on("pageerror", (error) => errors.push(`${width}/${javaScriptEnabled}: ${error.message}`));
      for (const route of ["", "company.html"]) {
        const response = await page.goto(new URL(route, base).href, { waitUntil: "networkidle", timeout: 45000 });
        assert.equal(response.status(), 200);
        assert.ok(!(await response.text()).includes("91530103MACQG57N6E"));
        const content = await page.evaluate(() => {
          const text = document.body.innerText;
          const schemas = [...document.querySelectorAll('script[type="application/ld+json"]')].map((n) => JSON.parse(n.textContent));
          const organizations = [];
          function walk(value) {
            if (!value || typeof value !== "object") return;
            if (value["@id"] === "https://shumaojs.com/#organization") organizations.push(value);
            for (const child of Object.values(value)) walk(child);
          }
          schemas.forEach(walk);
          const facts = document.querySelector("#company .facts");
          return { title: document.title, canonical: document.querySelector('link[rel="canonical"]').href,
            robots: document.querySelector('meta[name="robots"]').content, organizations,
            withdrawnTerms: ["91530103MACQG57N6E", "统一社会信用代码", "成立日期", "登记机关", "企业类型"].filter((term) => text.includes(term)),
            declaredCompanyVisible: text.includes("昆明振润达商贸有限公司"),
            notice: text.includes("暂不展示尚未确认的登记字段"),
            logo: { loaded: document.querySelector("header .brand img").complete && document.querySelector("header .brand img").naturalWidth > 0 },
            contact: document.querySelector(".header-cta").href,
            factCount: facts?.querySelectorAll(".fact-card").length ?? null,
            factColumns: facts ? getComputedStyle(facts).gridTemplateColumns.split(" ").length : null,
            registrationListCount: document.querySelectorAll(".company-verification").length,
            overflow: document.documentElement.scrollWidth > innerWidth + 1,
            mainLinks: [...new Set([...document.querySelectorAll("main a[href]")].filter((n) => n.origin === location.origin).map((n) => n.pathname))] };
        });
        assert.equal(content.canonical, "https://shumaojs.com/" + route);
        assert.ok(!content.robots.includes("noindex"));
        assert.equal(content.declaredCompanyVisible, true);
        assert.deepEqual(content.withdrawnTerms, []);
        assert.equal(content.logo.loaded, true);
        assert.equal(content.contact, "https://t.me/qichuanggg");
        assert.equal(content.overflow, false);
        assert.equal(content.registrationListCount, 0);
        for (const organization of content.organizations) for (const field of ["identifier", "taxID", "vatID", "foundingDate"]) assert.equal(field in organization, false, field);
        if (route === "") {
          assert.equal(content.title, "谷歌代投与 Google Ads 投放管理 | 开户协助 | 昆明振润达");
          assert.equal(content.factCount, 3);
          assert.equal(content.factColumns, width > 980 ? 3 : width > 700 ? 2 : 1);
          const definition = content.organizations.find((n) => n["@type"] === "ProfessionalService");
          assert.equal(definition.legalName, "昆明振润达商贸有限公司");
          assert.equal(definition["@id"], "https://shumaojs.com/#organization");
        } else {
          assert.equal(content.title, "企业与服务说明 | 昆明振润达商贸有限公司");
          assert.equal(content.notice, true);
        }
        if (javaScriptEnabled && width <= 390) {
          const menu = page.locator(".mobile-menu-toggle");
          await menu.click(); assert.equal(await menu.getAttribute("aria-expanded"), "true");
          const dropdown = page.locator(".nav-drop-toggle");
          await dropdown.click(); assert.equal(await dropdown.getAttribute("aria-expanded"), "true");
          await menu.click(); assert.equal(await menu.getAttribute("aria-expanded"), "false");
        }
        if (width === 1440 && javaScriptEnabled) for (const href of content.mainLinks) assert.equal((await context.request.get(new URL(href, base).href)).status(), 200, href);
        if (width === 1440 || width === 390 || width === 2560) {
          if (route === "") await page.locator("#company").scrollIntoViewIfNeeded();
          await page.screenshot({ path: path.join(output, `${route ? "company" : "home"}-${width}-${javaScriptEnabled ? "js" : "nojs"}.png`) });
        }
        results.push({ route: route || "/", width, javaScriptEnabled, ...content });
        console.log(`Passed identity ${route || "/"} ${width}px/${javaScriptEnabled ? "JS" : "noJS"}`);
      }
      await context.close();
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, "browser.json"), JSON.stringify({ checkedAt: new Date().toISOString(), base: base.href, results, pageErrors: errors }, null, 2) + "\n");
  } finally { await browser.close(); }
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
