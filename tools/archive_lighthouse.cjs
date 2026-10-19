const fs = require("node:fs");
const path = require("node:path");
const zlib = require("node:zlib");

const [output, ...inputs] = process.argv.slice(2);
if (!output || !inputs.length) throw new Error("Usage: node tools/archive_lighthouse.cjs output-directory report.json [...]");
fs.mkdirSync(output, { recursive: true });
const summary = {
  measurementType: "Mobile Lighthouse laboratory navigation runs",
  limitations: "One cold navigation per phase; scores and timings vary with network and CPU conditions. These are not CrUX field CWV or INP measurements.",
  runs: [],
};
for (const input of inputs) {
  const raw = fs.readFileSync(input);
  const report = JSON.parse(raw);
  if (report.runtimeError) throw new Error(`${input}: ${report.runtimeError.message}`);
  const archived = path.basename(input) + ".gz";
  fs.writeFileSync(path.join(output, archived), zlib.gzipSync(raw, { level: 9 }));
  const audit = report.audits;
  const requests = audit["network-requests"].details.items;
  summary.runs.push({
    label: path.basename(input, ".json"),
    url: report.finalUrl,
    fetchTime: report.fetchTime,
    lighthouseVersion: report.lighthouseVersion,
    hostUserAgent: report.environment.hostUserAgent,
    settings: {
      formFactor: report.configSettings.formFactor,
      throttlingMethod: report.configSettings.throttlingMethod,
      throttling: report.configSettings.throttling,
      screenEmulation: report.configSettings.screenEmulation,
    },
    performanceScore: Math.round(report.categories.performance.score * 100),
    lcpMs: audit["largest-contentful-paint"].numericValue,
    cls: audit["cumulative-layout-shift"].numericValue,
    totalBlockingTimeMs: audit["total-blocking-time"].numericValue,
    totalTransferBytes: requests.reduce((total, request) => total + request.transferSize, 0),
    criticalAssets: requests.filter((request) => /tabler-icons|tabler-subset|photo-1557804506|assets\/hero\//.test(request.url))
      .map((request) => ({ url: request.url, resourceBytes: request.resourceSize, transferBytes: request.transferSize, status: request.statusCode })),
    warnings: report.runWarnings,
    rawArtifact: archived,
  });
}
fs.writeFileSync(path.join(output, "summary.json"), JSON.stringify(summary, null, 2) + "\n");
console.log(JSON.stringify(summary.runs.map(({ label, performanceScore, lcpMs, cls }) => ({ label, performanceScore, lcpMs, cls })), null, 2));
