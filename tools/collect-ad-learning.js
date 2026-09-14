const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const dataPath = path.join(root, "data", "ad-learning.json");
const outputHtmlPath = path.join(root, "ad-learning.html");
const stateDir = path.join(root, ".agents", "loops");
const statePath = path.join(stateDir, "ad-learning-collector.json");
const logPath = path.join(stateDir, "ad-learning-collector.log");

const sources = [
  { name: "Google Ads & Commerce Blog", url: "https://blog.google/products/ads-commerce/rss/" },
  { name: "Think with Google", url: "https://www.thinkwithgoogle.com/rss/" },
  { name: "Search Engine Land", url: "https://searchengineland.com/feed" },
  { name: "WordStream", url: "https://www.wordstream.com/blog/feed" },
  { name: "PPC Hero", url: "https://www.ppchero.com/feed/" },
  { name: "Social Media Examiner", url: "https://www.socialmediaexaminer.com/feed/" }
];

const keywords = [
  "google ads",
  "meta ads",
  "facebook ads",
  "ppc",
  "paid search",
  "paid media",
  "performance max",
  "conversion tracking",
  "landing page",
  "keyword",
  "bidding",
  "roas",
  "广告",
  "投放",
  "转化"
];

const excludeKeywords = [
  "conference",
  "hero conf",
  "jobs",
  "career",
  "seo dehumanization",
  "dehumanization of seo"
];

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function readJson(file, fallback) {
  try {
    return JSON.parse(fs.readFileSync(file, "utf8"));
  } catch {
    return fallback;
  }
}

function stripTags(value) {
  return String(value || "")
    .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1")
    .replace(/<[^>]*>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function decodeEntities(value) {
  const named = {
    "&amp;": "&",
    "&lt;": "<",
    "&gt;": ">",
    "&quot;": "\"",
    "&#39;": "'",
    "&apos;": "'"
  };
  let output = String(value || "");
  for (let i = 0; i < 3; i += 1) {
    const next = output
      .replace(/&(amp|lt|gt|quot|#39|apos);/g, (m) => named[m] || m)
      .replace(/&#(\d+);/g, (_, code) => String.fromCharCode(Number(code)))
      .replace(/&#x([0-9a-f]+);/gi, (_, code) => String.fromCharCode(parseInt(code, 16)));
    if (next === output) break;
    output = next;
  }
  return output;
}

function cleanText(value) {
  return stripTags(decodeEntities(stripTags(value)))
    .replace(/\bThe post\b[\s\S]*$/i, "")
    .replace(/\bContinue reading\b[\s\S]*$/i, "")
    .replace(/[\u2013\u2014]/g, "-")
    .replace(/\s+/g, " ")
    .trim();
}

function getTag(block, tag) {
  const re = new RegExp(`<${tag}[^>]*>([\\s\\S]*?)<\\/${tag}>`, "i");
  return cleanText((block.match(re) || [])[1] || "");
}

function getLink(block) {
  const href = (block.match(/<link[^>]+href=["']([^"']+)["']/i) || [])[1];
  if (href) return decodeEntities(href.trim());
  return decodeEntities(stripTags((block.match(/<link[^>]*>([\s\S]*?)<\/link>/i) || [])[1] || ""));
}

function parseFeed(xml, sourceName) {
  const blocks = xml.includes("<entry")
    ? [...xml.matchAll(/<entry[\s\S]*?<\/entry>/gi)].map((m) => m[0])
    : [...xml.matchAll(/<item[\s\S]*?<\/item>/gi)].map((m) => m[0]);

  return blocks.map((block) => {
    const title = getTag(block, "title");
    const url = getLink(block);
    const publishedAt = getTag(block, "pubDate") || getTag(block, "published") || getTag(block, "updated");
    const description = getTag(block, "description") || getTag(block, "summary") || getTag(block, "content:encoded");
    return {
      title,
      url,
      source: sourceName,
      publishedAt: publishedAt ? new Date(publishedAt).toISOString() : new Date().toISOString(),
      category: classify(`${title} ${description}`),
      summary: description.slice(0, 180)
    };
  }).filter((item) => item.title && item.url);
}

function classify(text) {
  const t = text.toLowerCase();
  if (t.includes("meta") || t.includes("facebook") || t.includes("instagram")) return "Meta / Facebook";
  if (t.includes("landing page") || t.includes("conversion")) return "转化与落地页";
  if (t.includes("keyword") || t.includes("search")) return "搜索广告";
  if (t.includes("google")) return "Google Ads";
  return "广告投放";
}

function isRelevant(item) {
  const haystack = `${item.title} ${item.summary}`.toLowerCase();
  if (excludeKeywords.some((keyword) => haystack.includes(keyword))) return false;
  return keywords.some((keyword) => haystack.includes(keyword));
}

function itemKey(item) {
  return item.url.replace(/[#?].*$/, "").toLowerCase();
}

function normalizeItem(item) {
  return {
    title: cleanText(item.title),
    url: String(item.url || "").trim(),
    source: cleanText(item.source),
    publishedAt: item.publishedAt || new Date().toISOString(),
    category: item.category || classify(`${item.title} ${item.summary}`),
    summary: cleanText(item.summary).slice(0, 180)
  };
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderHtml(data) {
  const cards = data.items.slice(0, 18).map((item) => {
    const isLocal = !/^https?:\/\//i.test(item.url);
    const target = isLocal ? "" : " target=\"_blank\" rel=\"noopener\"";
    const action = isLocal ? "查看站内教程" : "查看原文";
    return `        <article class="article-card">
          <span>${escapeHtml(item.category || item.source)}</span>
          <h3><a href="${escapeHtml(item.url)}"${target}>${escapeHtml(item.title)}</a></h3>
          <p>${escapeHtml(item.summary)}</p>
          <small>${escapeHtml(item.source)} · ${escapeHtml((item.publishedAt || "").slice(0, 10))}</small>
          <a class="text-link" href="${escapeHtml(item.url)}"${target}>${action}</a>
        </article>`;
  }).join("\n");

  const ideas = (data.topicIdeas || []).slice(0, 6).map((idea) => `        <article class="resource-card">
          <span>选题</span>
          <strong>${escapeHtml(idea)}</strong>
          <p>可根据采集到的资料继续写成原创教程，并链接回相关服务页。</p>
        </article>`).join("\n");

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>每周广告投放技巧与教材 | 自动采集资源 | 昆明振润达商贸有限公司</title>
  <meta name="description" content="每周自动采集广告投放技巧、Google Ads 教材、Meta 广告学习资源、落地页优化和转化追踪相关文章摘要，保留原文链接。">
  <meta name="robots" content="index,follow">
  <meta name="theme-color" content="#0f5f9f">
  <link rel="icon" href="favicon.ico" sizes="any">
  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
  <link rel="manifest" href="site.webmanifest">
  <link rel="stylesheet" href="styles.css">
  <script src="script.js" defer></script>
</head>
<body class="legal-page">
  <header class="legal-header">
    <a class="brand" href="index.html" aria-label="返回首页">
      <img src="assets/logo.svg" alt="振润达">
      <span><strong>振润达</strong><small>独立广告咨询机构</small></span>
    </a>
    <nav class="legal-nav" aria-label="页面导航">
      <a href="index.html">首页</a>
      <a href="index.html#scope">服务</a>
      <div class="nav-dropdown">
        <button class="nav-drop-toggle" type="button" aria-expanded="false" aria-haspopup="true">广告代投</button>
        <div class="nav-dropdown-menu" role="menu">
          <a href="google-ads.html" role="menuitem">Google开户代投</a>
          <a href="meta-ads.html" role="menuitem">Meta开户代投</a>
          <a href="facebook-ads.html" role="menuitem">Facebook开户代投</a>
          <a href="x-ads.html" role="menuitem">X/Twitter开户代投</a>
          <a href="managed-ads.html" role="menuitem">多平台开户代投</a>
          <a href="account-guidance.html" role="menuitem">开户资料指导</a>
        </div>
      </div>
      <a href="articles.html">文章</a>
      <a href="nav.html">工具</a>
      <a href="compliance.html">合规</a>
      <a href="contact.html">联系</a>
    </nav>
    <a class="button button-primary header-cta" href="https://t.me/qichuanggg" target="_blank" rel="noopener">Telegram 咨询</a>
  </header>

  <main class="legal-content resource-page">
    <p class="label">Weekly Learning</p>
    <h1>每周广告投放技巧与教材</h1>
    <p class="legal-updated">最近更新：${escapeHtml(data.generatedAt.slice(0, 10))}。这个页面由 GitHub Actions 每周自动更新，只保存标题、摘要、来源和原文链接。</p>

    <section>
      <h2>本周资源</h2>
      <div class="article-list">
${cards}
      </div>
    </section>

    <section>
      <h2>可继续写成站内文章的选题</h2>
      <div class="resource-grid compact-grid">
${ideas}
      </div>
    </section>

    <section>
      <h2>自动采集说明</h2>
      <ul>
        <li>频率：每周一自动运行一次，也可以在 GitHub Actions 手动触发。</li>
        <li>来源：优先采集官方、行业媒体和广告学习站点的 RSS 或公开摘要。</li>
        <li>去重：脚本会记录已处理链接，避免每周重复堆叠相同内容。</li>
        <li>边界：不自动发布广告，不抓取全文，不替代人工判断。</li>
      </ul>
    </section>

    <section class="legal-cta" aria-label="咨询广告学习资源">
      <h2>想把资源整理成你的投放方案？</h2>
      <p>发送网站、业务类型和目标市场，我们会先帮你判断适合学习和执行的优先级。</p>
      <div class="legal-actions">
        <a class="button button-primary" href="https://t.me/qichuanggg" target="_blank" rel="noopener">获取投放诊断</a>
        <a class="button button-secondary" href="nav.html">打开工具导航</a>
      </div>
    </section>
  </main>

  <footer class="site-footer">
    <div><strong>昆明振润达商贸有限公司</strong><p>独立广告咨询机构，提供多平台广告代投咨询服务。非广告平台官方机构，不销售广告账户，不代持广告账户，遵守平台审核规则。</p></div>
    <nav class="footer-nav" aria-label="页脚导航">
      <a href="index.html">首页</a>
      <a href="index.html#scope">服务范围</a>
      <a href="nav.html">工具导航</a>
      <a href="articles.html">文章</a>
      <a href="compliance.html">合规边界</a>
      <a href="privacy.html">隐私政策</a>
      <a href="terms.html">服务条款</a>
      <a href="contact.html">联系</a>
    </nav>
  </footer>
</body>
</html>
`;
}

async function main() {
  ensureDir(path.dirname(dataPath));
  ensureDir(stateDir);
  const existing = readJson(dataPath, { items: [], topicIdeas: [] });
  const state = readJson(statePath, { loop: "ad-learning-collector", handled: [] });
  const handled = new Set([...(state.handled || []), ...existing.items.map(itemKey)]);
  const collected = [];
  const errors = [];

  for (const source of sources) {
    try {
      const res = await fetch(source.url, { headers: { "user-agent": "zrd-ad-learning-collector/1.0" } });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const xml = await res.text();
      collected.push(...parseFeed(xml, source.name).filter(isRelevant));
    } catch (error) {
      errors.push(`${source.name}: ${error.message}`);
    }
  }

  const fresh = [];
  for (const item of collected.sort((a, b) => new Date(b.publishedAt) - new Date(a.publishedAt))) {
    const key = itemKey(item);
    if (handled.has(key)) continue;
    handled.add(key);
    fresh.push(item);
  }

  const items = [...fresh, ...(existing.items || [])]
    .map(normalizeItem)
    .filter(isRelevant)
    .filter((item, index, arr) => arr.findIndex((other) => itemKey(other) === itemKey(item)) === index)
    .slice(0, 36);

  const topicIdeas = [
    ...new Set([
      ...fresh.slice(0, 8).map((item) => `${item.category}：${item.title}`),
      ...(existing.topicIdeas || [])
    ])
  ]
    .map(cleanText)
    .filter((idea) => {
      const lower = idea.toLowerCase();
      return idea && !excludeKeywords.some((keyword) => lower.includes(keyword));
    })
    .slice(0, 18);

  const data = {
    generatedAt: new Date().toISOString(),
    sourcesChecked: sources.length,
    items,
    topicIdeas
  };

  fs.writeFileSync(dataPath, `${JSON.stringify(data, null, 2)}\n`);
  fs.writeFileSync(outputHtmlPath, renderHtml(data));
  fs.writeFileSync(statePath, `${JSON.stringify({
    loop: "ad-learning-collector",
    lastRun: data.generatedAt,
    handled: [...handled].slice(-250),
    lastErrors: errors
  }, null, 2)}\n`);
  fs.appendFileSync(logPath, `${data.generatedAt} checked=${collected.length} acted=${fresh.length} note="${errors.length ? `updated with ${errors.length} source errors` : "updated"}"\n`);

  console.log(`Collected ${collected.length} relevant items, added ${fresh.length} new items.`);
  if (errors.length) {
    console.log(`Source errors: ${errors.join("; ")}`);
  }
}

main().catch((error) => {
  ensureDir(stateDir);
  fs.appendFileSync(logPath, `${new Date().toISOString()} checked=0 acted=0 note="failed: ${String(error.message).replace(/"/g, "'")}"\n`);
  console.error(error);
  process.exit(1);
});



