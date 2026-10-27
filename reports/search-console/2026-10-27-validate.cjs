const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const file = path.join(__dirname, "2026-10-27-performance-follow-up.json");
const data = JSON.parse(fs.readFileSync(file, "utf8"));
const tables = [
  ...Object.entries(data.weekly.tables).map(([key, value]) => ["weekly/" + key, value]),
  ...["pages", "countries", "chinaJointPage", "chinaDaily"].map(key => ["target/" + key, data.weekly.target[key]]),
  ...Object.entries(data.comparison28.tables).map(([key, value]) => ["28day/" + key, value]),
];
const sums = {};
let rowsChecked = 0;
for (const [name, table] of tables) {
  const daily = name.endsWith("chinaDaily");
  const rows = table.rows.slice(1);
  assert.ok(rows.length > 0, name);
  const coverage = /^第 1-(\d+) 行，共 (\d+) 行$/.exec(table.footer);
  assert.ok(coverage, name);
  assert.equal(Number(coverage[1]), rows.length, name);
  assert.equal(Number(coverage[2]), rows.length, name);
  const keys = rows.map(row => row[0].split("\n")[0].trim());
  assert.equal(new Set(keys).size, keys.length, name);
  assert.ok(keys.every(Boolean), name);
  sums[name] = { clicks: [0, 0], impressions: [0, 0] };
  for (const row of rows) {
    assert.equal(row.length, daily ? 5 : 13, name);
    for (const index of daily ? [1, 2] : [1, 2, 4, 5]) {
      assert.match(row[index], /^\d+$/, name);
    }
    if (daily) {
      sums[name].clicks[0] += Number(row[1]);
      sums[name].impressions[0] += Number(row[2]);
      if (Number(row[2]) === 0) {
        assert.equal(row[3], "—");
        assert.equal(row[4], "—");
      }
    } else {
      assert.equal(Number(row[3]), Number(row[1]) - Number(row[2]), name);
      assert.equal(Number(row[6]), Number(row[4]) - Number(row[5]), name);
      for (let i = 0; i < 2; i += 1) {
        sums[name].clicks[i] += Number(row[1 + i]);
        sums[name].impressions[i] += Number(row[4 + i]);
        assert.match(row[7 + i], /^\d+(\.\d+)?%$/, name);
        assert.ok(Number.isFinite(Number(row[10 + i])) && Number(row[10 + i]) >= 0, name);
      }
    }
  }
  rowsChecked += rows.length;
}
for (const [period, days] of [[data.weekly, 7], [data.comparison28, 28]]) {
  const dates = period.dates.map(value => new Date(value + "T00:00:00Z").getTime());
  const day = 86400000;
  assert.equal((dates[1] - dates[0]) / day + 1, days);
  assert.equal((dates[3] - dates[2]) / day + 1, days);
  assert.equal((dates[0] - dates[3]) / day, 1);
}
assert.deepEqual(sums["weekly/countries"], { clicks: [1, 0], impressions: [46, 41] });
assert.deepEqual(sums["28day/countries"], { clicks: [1, 1], impressions: [248, 3] });
assert.deepEqual(sums["target/pages"], { clicks: [1, 0], impressions: [8, 0] });
assert.deepEqual(sums["target/countries"], sums["target/pages"]);
assert.deepEqual(sums["target/chinaJointPage"], { clicks: [1, 0], impressions: [7, 0] });
assert.deepEqual(sums["target/chinaDaily"], sums["target/chinaJointPage"]);
const daily = data.weekly.target.chinaDaily.rows.slice(1);
assert.equal(daily.length, 7);
assert.equal(daily.find(row => Number(row[1]) > 0)[0], "2026年10月25日");
assert.equal(daily.filter(row => Number(row[1]) > 0).length, 1);
assert.equal(rowsChecked, 180);
assert.equal(tables.length, 10);
assert.equal(data.weekly.target.chinaJointPage.rows[1][0], "https://shumaojs.com/google-ads.html");
assert.ok(!/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i.test(fs.readFileSync(file, "utf8")), "Account email must not enter published evidence");
console.log(JSON.stringify({ tablesChecked: tables.length, rowsChecked, sums, note: "Country totals reconcile; query/page totals intentionally not forced equal. Missing-position0 remains raw, never called rank0. No inferred market join or click-to-customer claim." }, null, 2));
