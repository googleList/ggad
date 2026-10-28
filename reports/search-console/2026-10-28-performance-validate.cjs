const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const file = path.join(__dirname, "2026-10-28-performance-follow-up.json");
const raw = fs.readFileSync(file, "utf8");
const data = JSON.parse(raw);
const tables = [];
for (const period of ["weekly", "comparison28", "targetQuery"]) {
  for (const [name, table] of Object.entries(data[period].tables)) {
    tables.push([`${period}/${name}`, table]);
  }
}
const sums = {};
let rowsChecked = 0;
for (const [name, table] of tables) {
  const coverage = /^第 1-(\d+) 行，共 (\d+) 行$/.exec(table.footer);
  assert.ok(coverage, name);
  assert.equal(Number(coverage[1]), table.rows.length, name);
  assert.equal(Number(coverage[2]), table.rows.length, name);
  const keys = table.rows.map(row => row[0].split("\n")[0].trim());
  assert.equal(new Set(keys).size, keys.length, name);
  sums[name] = { clicks: [0, 0], impressions: [0, 0] };
  for (const row of table.rows) {
    assert.equal(row.length, data.columns.length, name);
    assert.ok(row[0], name);
    for (const index of [1, 2, 4, 5]) assert.match(row[index], /^\d+$/, name);
    assert.equal(Number(row[3]), Number(row[1]) - Number(row[2]), name);
    assert.equal(Number(row[6]), Number(row[4]) - Number(row[5]), name);
    for (let i = 0; i < 2; i += 1) {
      const clicks = Number(row[1 + i]);
      const impressions = Number(row[4 + i]);
      assert.ok(clicks <= impressions, name);
      assert.match(row[7 + i], /^\d+(\.\d+)?%$/, name);
      const ctr = Number(row[7 + i].replace("%", ""));
      assert.ok(Math.abs(ctr - (impressions ? clicks / impressions * 100 : 0)) <= 0.11, name);
      assert.ok(Number.isFinite(Number(row[10 + i])) && Number(row[10 + i]) >= 0, name);
      sums[name].clicks[i] += clicks;
      sums[name].impressions[i] += impressions;
    }
    // GSC differences can use more precision than its displayed positions.
    assert.ok(Number.isFinite(Number(row[12])), name);
    rowsChecked += 1;
  }
}
for (const [name, days] of [["weekly", 7], ["comparison28", 28]]) {
  const period = data[name];
  assert.equal(period.datesConfirmedAfterApply, true);
  const dates = period.dates.map(value => Date.parse(value + "T00:00:00Z"));
  assert.equal((dates[1] - dates[0]) / 86400000 + 1, days);
  assert.equal((dates[3] - dates[2]) / 86400000 + 1, days);
  assert.equal((dates[0] - dates[3]) / 86400000, 1);
  const expected = {
    clicks: [period.summary.current.clicks, period.summary.previous.clicks],
    impressions: [period.summary.current.impressions, period.summary.previous.impressions],
  };
  assert.deepEqual(sums[name + "/countries"], expected);
  assert.deepEqual(sums[name + "/devices"], expected);
}
assert.deepEqual(data.targetQuery.dates, data.weekly.dates);
assert.deepEqual(sums["targetQuery/pages"], { clicks: [1, 0], impressions: [11, 0] });
assert.deepEqual(sums["targetQuery/countries"], sums["targetQuery/pages"]);
for (const [name, impressions] of [["usaPages", 2], ["hongKongPages", 1]]) {
  assert.deepEqual(sums["targetQuery/" + name], { clicks: [0, 0], impressions: [impressions, 0] });
  assert.equal(data.targetQuery.tables[name].rows[0][0], "https://shumaojs.com/google-ads.html");
}
const countries = new Map(data.targetQuery.tables.countries.rows.map(row => [row[0], row]));
assert.equal(countries.get("美国")[4], "2");
assert.equal(countries.get("中国香港")[4], "1");
assert.equal(countries.get("中国")[1], "1");
assert.equal(countries.get("中国")[4], "7");
assert.equal(data.targetQuery.tables.pages.rows[0][0], "https://shumaojs.com/google-ads.html");
assert.equal(tables.length, 12);
assert.equal(rowsChecked, 180);
assert.ok(!/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i.test(raw));
console.log(JSON.stringify({ tablesChecked: tables.length, rowsChecked, sums, note: "Transcription consistency only, not independent API inspection. Country/device totals reconcile; query/page totals intentionally not forced equal. Direct US/HK joins confirm sparse exposure, not market volume, stable ranking, clicks, clients or release causality." }, null, 2));
