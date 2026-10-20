const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { execFileSync } = require("node:child_process");
const { request } = require(process.env.PLAYWRIGHT_MODULE || "playwright");

const root = path.resolve(__dirname, "..");
const input = path.resolve(process.argv[2] || "reports/search-console/indexing-2026-10-20.json");
const output = path.resolve(process.argv[3] || "reports/search-console/indexing-http-2026-10-20.json");

async function main() {
  const snapshot = JSON.parse(fs.readFileSync(input, "utf8"));
  const local = JSON.parse(execFileSync(process.env.PYTHON || "python", ["-B", "-c", [
    "import sys,json; from pathlib import Path; sys.path.insert(0,'scripts')",
    "from internal_link_audit import collect_graph,distances",
    "from content_policy_check import FORBIDDEN_PATHS,FORBIDDEN_PREFIXES",
    "from deployment_drift_audit import parse_sitemap",
    "g,m=collect_graph()",
    "print(json.dumps({'graph':{k:sorted(v) for k,v in g.items()},'metadata':m,'depth':distances(g),'sitemap':sorted(parse_sitemap(Path('sitemap.xml').read_text(encoding='utf-8'))),'retiredPaths':sorted(FORBIDDEN_PATHS),'retiredPrefixes':FORBIDDEN_PREFIXES}))",
  ].join("\n")], { cwd: root, encoding: "utf8" }));
  const rows = Object.entries(snapshot.groups).flatMap(([reason, urls]) => urls.map((url) => ({ reason, url })));
  assert.equal(new Set(rows.map((row) => row.url)).size, rows.length, "Duplicate sample URL");
  for (const row of rows) {
    const url = new URL(row.url);
    assert.equal(url.hostname, "shumaojs.com", "Only the owned website may be checked");
    assert.ok(["http:", "https:"].includes(url.protocol));
  }
  const client = await request.newContext({ timeout: 30000 });
  const results = [];
  try {
    for (const row of rows) {
      const url = new URL(row.url);
      const relative = url.pathname.slice(1);
      const key = ["/", "/index.html"].includes(url.pathname) ? "/"
        : url.pathname.endsWith("/") ? `${url.pathname}index.html` : url.pathname;
      const retired = local.retiredPaths.includes(relative) || local.retiredPrefixes.some((prefix) => relative.startsWith(prefix));
      const sources = Object.entries(local.graph).filter(([, targets]) => targets.includes(key)).map(([source]) => source);
      const category = retired ? "retired" : url.protocol === "http:" ? "http-duplicate"
        : url.pathname === "/feed.xml" ? "rss" : url.pathname === "/index.html" ? "homepage-variant" : "current-html";
      const result = { ...row, category, inSitemap: local.sitemap.includes(row.url),
        inlinkSources: sources, clickDepth: local.depth[key] ?? null,
        expectedCanonical: local.metadata[key]?.canonical ?? null };
      try {
        const response = await client.get(row.url, { maxRedirects: 0 });
        result.status = response.status();
        result.location = response.headers().location || null;
        result.issues = [];
        if (retired) {
          if (![404, 410].includes(result.status)) result.issues.push("Retired URL is still served");
          if (sources.length || result.inSitemap) result.issues.push("Retired URL still has discovery references");
        } else if (category === "http-duplicate") {
          if (![301, 308].includes(result.status) || !result.location?.startsWith("https://shumaojs.com")) {
            result.issues.push("HTTP is not permanently redirected to canonical HTTPS");
          }
        } else if (result.status !== 200) result.issues.push("Expected live resource is not HTTP 200");
        if (category === "current-html" && (!result.inSitemap || !sources.length || !local.metadata[key]?.indexable)) {
          result.issues.push("Current HTML lacks local indexability/discovery signals");
        }
      } catch (error) {
        result.status = null;
        result.issues = ["HTTP verification unavailable"];
        result.error = error.message.split("\n")[0];
      }
      results.push(result);
      if (results.length % 10 === 0) console.log(`Checked ${results.length}/${rows.length} indexing examples`);
    }
  } finally {
    await client.dispose();
  }
  const report = { checkedAt: new Date().toISOString(), source: path.relative(root, input).replaceAll("\\", "/"),
    reportLastUpdated: snapshot.reportLastUpdated,
    summary: { checked: results.length, categories: {}, issueRows: results.filter((row) => row.issues.length).length },
    limits: "HTTP status and static internal-link/sitemap evidence do not establish Google indexing. Reported GSC reasons remain historical.", results };
  for (const row of results) report.summary.categories[row.category] = (report.summary.categories[row.category] || 0) + 1;
  fs.mkdirSync(path.dirname(output), { recursive: true });
  fs.writeFileSync(output, JSON.stringify(report, null, 2) + "\n");
  console.log(JSON.stringify(report.summary, null, 2));
}

main().catch((error) => { console.error(error); process.exitCode = 1; });
