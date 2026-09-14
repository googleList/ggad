#!/usr/bin/env python3
"""
Weekly article monitor for competitor/blog inspiration.

This script intentionally collects metadata, short summaries, canonical links,
and image reference URLs only. It does not save full article bodies or download
third-party images.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "data" / "article-sources.json"
OUTPUT_PATH = ROOT / "data" / "collected-articles.json"
REPORT_PATH = ROOT / "reports" / "collected-articles.html"

USER_AGENT = (
    "Mozilla/5.0 (compatible; GGAdArticleMonitor/1.0; "
    "+https://qichuanggg.com/contact.html)"
)

KEYWORDS = {
    "Google Ads": ["google ads", "谷歌广告", "ppc", "search ads", "performance max", "pmax"],
    "Meta Ads": ["meta ads", "facebook", "instagram", "messenger"],
    "SEO": ["seo", "谷歌seo", "搜索优化", "organic search"],
    "GEO / AI Search": ["geo", "ai search", "ai 搜索", "chatgpt", "llm", "生成式"],
    "Tracking": ["ga4", "tracking", "conversion", "转化追踪", "attribution"],
    "Website": ["landing page", "网站", "shopify", "web design", "落地页"]
}

MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12
}

TRADITIONAL_TO_SIMPLIFIED = str.maketrans({
    "廣": "广", "告": "告", "學": "学", "習": "习", "與": "与", "設": "设", "報": "报",
    "關": "关", "鍵": "键", "體": "体", "實": "实", "測": "测", "預": "预", "眾": "众",
    "優": "优", "化": "化", "轉": "转", "換": "换", "追": "追", "蹤": "踪", "資": "资",
    "訊": "讯", "頁": "页", "達": "达", "號": "号", "戶": "户", "開": "开", "賬": "账",
    "帳": "账", "費": "费", "標": "标", "題": "题", "範": "范", "圍": "围", "顯": "显",
    "示": "示", "導": "导", "覽": "览", "圖": "图", "視": "视", "頻": "频", "製": "制",
    "產": "产", "業": "业", "貿": "贸", "電": "电", "商": "商", "據": "据", "庫": "库",
    "歸": "归", "類": "类", "線": "线", "離": "离", "構": "构", "應": "应", "對": "对",
    "稱": "称", "選": "选", "擇": "择", "過": "过", "濾": "滤", "擊": "击", "連": "连",
    "結": "结", "準": "准", "備": "备", "錢": "钱", "價": "价", "數": "数", "據": "据",
    "個": "个", "為": "为", "從": "从", "會": "会", "時": "时", "後": "后", "並": "并",
    "將": "将", "讓": "让", "這": "这", "裡": "里", "於": "于", "無": "无", "發": "发",
    "現": "现", "雲": "云", "網": "网", "站": "站", "讀": "读", "寫": "写", "長": "长",
    "術": "术", "務": "务", "險": "险", "變": "变", "詞": "词", "認": "认", "證": "证",
    "檔": "档", "案": "案", "專": "专", "欄": "栏", "層": "层", "議": "议", "線": "线",
    "總": "总", "覽": "览", "請": "请", "聯": "联", "絡": "络", "嗎": "吗", "導": "导",
    "嗎": "吗", "種": "种", "雙": "双", "單": "单", "萬": "万", "員": "员", "場": "场",
    "銷": "销", "討": "讨", "論": "论", "語": "语", "當": "当", "參": "参", "測": "测",
    "縮": "缩", "寫": "写", "順": "顺", "點": "点", "擊": "击", "並": "并", "劃": "划",
    "劑": "剂", "問": "问", "題": "题", "觀": "观", "瀏": "浏", "麼": "么", "決": "决",
    "還": "还", "條": "条", "複": "复", "幫": "帮", "檢": "检", "閱": "阅", "間": "间",
    "創": "创", "辦": "办", "載": "载", "買": "买", "廳": "厅", "絲": "丝", "該": "该",
    "據": "据", "錶": "表", "驗": "验", "獲": "获", "該": "该", "樂": "乐", "強": "强",
    "離": "离", "級": "级", "項": "项", "內": "内", "聽": "听", "講": "讲", "歷": "历",
    "應": "应", "寫": "写", "達": "达", "風": "风", "隻": "只", "張": "张"
})


def fetch(url: str, timeout: int = 25) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<script[\s\S]*?</script>", " ", value, flags=re.I)
    value = re.sub(r"<style[\s\S]*?</style>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    value = value.replace("\u2013", "-").replace("\u2014", "-")
    return to_simplified(value.strip())


def to_simplified(value: str) -> str:
    return (value or "").translate(TRADITIONAL_TO_SIMPLIFIED)


def attr_value(tag: str, name: str) -> str:
    match = re.search(rf"""{name}\s*=\s*["']([^"']+)["']""", tag, flags=re.I)
    return html.unescape(match.group(1).strip()) if match else ""


def meta_content(page_html: str, name: str) -> str:
    patterns = [
        rf"<meta\b[^>]*(?:name|property)\s*=\s*['\"]{re.escape(name)}['\"][^>]*>",
        rf"<meta\b[^>]*content\s*=\s*['\"][^'\"]+['\"][^>]*(?:name|property)\s*=\s*['\"]{re.escape(name)}['\"][^>]*>"
    ]
    for pattern in patterns:
        match = re.search(pattern, page_html, flags=re.I)
        if match:
            content = attr_value(match.group(0), "content")
            if content:
                return clean_text(content)
    return ""


def first_tag_text(block: str, *tags: str) -> str:
    for tag in tags:
        match = re.search(rf"<{tag}\b[^>]*>([\s\S]*?)</{tag}>", block, flags=re.I)
        if match:
            text = clean_text(match.group(1))
            if text:
                return text
    return ""


def tag_texts(block: str, tag_names: str, limit: int = 12) -> list[str]:
    pattern = rf"<(?:{tag_names})\b[^>]*>([\s\S]*?)</(?:{tag_names})>"
    texts = []
    for match in re.finditer(pattern, block, flags=re.I):
        text = clean_text(match.group(1))
        if text and text not in texts:
            texts.append(text[:120])
        if len(texts) >= limit:
            break
    return texts


def is_boilerplate_text(value: str) -> bool:
    text = value.strip().lower()
    if not text:
        return True
    blocked = [
        "本文目录",
        "已读",
        "阅读时间",
        "阅读时間",
        "作者：",
        "立即咨询",
        "联系我们",
        "想有专人",
        "跳至主要内容",
        "copyright"
    ]
    return any(word.lower() in text for word in blocked)


def useful_texts(values: list[str], limit: int) -> list[str]:
    output = []
    for value in values:
        if is_boilerplate_text(value):
            continue
        output.append(value)
        if len(output) >= limit:
            break
    return output


def probable_content_block(page_html: str) -> str:
    for tag in ("article", "main"):
        match = re.search(rf"<{tag}\b[^>]*>([\s\S]*?)</{tag}>", page_html, flags=re.I)
        if match:
            return match.group(1)
    return page_html


def extract_detail_brief(url: str) -> dict[str, Any]:
    body = fetch(url)
    content = probable_content_block(body)
    headings = useful_texts(tag_texts(content, "h2|h3", 20), 14)
    paragraphs = useful_texts(tag_texts(content, "p", 12), 6)
    description = meta_content(body, "description") or meta_content(body, "og:description")
    title = first_tag_text(content, "h1") or meta_content(body, "og:title")

    return {
        "detailTitle": title[:180],
        "detailSummary": (description or " ".join(paragraphs[:2]))[:280],
        "outline": headings,
        "researchNotes": paragraphs[:4],
        "rewriteBrief": make_rewrite_brief(title, headings, description),
        "detailFetchedAt": datetime.now(timezone.utc).isoformat()
    }


def make_rewrite_brief(title: str, headings: list[str], description: str) -> str:
    topic = title or (headings[0] if headings else "广告投放主题")
    outline = "、".join(headings[:4]) if headings else "背景、适用场景、执行步骤、注意事项"
    return (
        f"围绕「{topic}」写一篇原创简体中文文章。保留核心主题和信息结构，"
        f"但换成本网站的服务语境，加入外贸、跨境电商、开户资料、落地页合规和转化追踪案例。"
        f"可参考的结构：{outline}。"
    )[:420]


def first_img(block: str, base_url: str) -> tuple[str, str]:
    match = re.search(r"<img\b[^>]*>", block, flags=re.I)
    if not match:
        return "", ""
    tag = match.group(0)
    src = attr_value(tag, "src") or attr_value(tag, "data-src")
    alt = to_simplified(attr_value(tag, "alt"))
    if src:
        src = urljoin(base_url, src)
    return src, alt


def find_date_text(block: str) -> str:
    time_text = first_tag_text(block, "time")
    if time_text:
        return time_text
    text = clean_text(block)
    patterns = [
        r"\d{4}年\d{1,2}月\d{1,2}日",
        r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}",
        r"\d{4}-\d{1,2}-\d{1,2}"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            return match.group(0)
    return ""


def parse_date(value: str) -> str | None:
    if not value:
        return None
    zh = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", value)
    if zh:
        y, m, d = map(int, zh.groups())
        return datetime(y, m, d, tzinfo=timezone.utc).isoformat()
    en = re.search(r"(\d{1,2})\s+([A-Za-z]{3,})\s+(\d{4})", value)
    if en:
        d = int(en.group(1))
        m = MONTHS.get(en.group(2)[:3].lower())
        y = int(en.group(3))
        if m:
            return datetime(y, m, d, tzinfo=timezone.utc).isoformat()
    iso = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", value)
    if iso:
        y, m, d = map(int, iso.groups())
        return datetime(y, m, d, tzinfo=timezone.utc).isoformat()
    return None


def classify(title: str, summary: str) -> str:
    haystack = f"{title} {summary}".lower()
    for category, words in KEYWORDS.items():
        if any(word.lower() in haystack for word in words):
            return category
    return "Digital Marketing"


def make_id(url: str) -> str:
    parsed = urlparse(url)
    key = f"{parsed.netloc}{parsed.path}".lower().rstrip("/")
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def is_probable_article(url: str, title: str, source_url: str) -> bool:
    if not url or not title or len(title) < 8:
        return False
    parsed = urlparse(url)
    source_host = urlparse(source_url).netloc
    if parsed.netloc and parsed.netloc != source_host:
        return False
    path = parsed.path.lower()
    blocked = ["/contact", "/about", "/service", "/services", "/category/", "/tag/", "/privacy", "/terms"]
    if any(part in path for part in blocked):
        return False
    if "horntech.com.au" in source_host:
        return "/zh/blog/" in path and path.rstrip("/") != "/zh/blog"
    if "kickads.co" in source_host:
        return path.startswith("/zh/") and path.rstrip("/") not in {"/zh", "/zh/blog"}
    return "/blog" in path


def parse_listing(source: dict[str, Any], page_html: str) -> list[dict[str, Any]]:
    base_url = source["url"]
    items: list[dict[str, Any]] = []
    anchor_re = re.compile(r"<a\b([^>]*)>([\s\S]*?)</a>", flags=re.I)

    for match in anchor_re.finditer(page_html):
        open_tag, block = match.groups()
        href = attr_value(open_tag, "href")
        url = urljoin(base_url, href)
        img_url, img_alt = first_img(block, base_url)
        title = first_tag_text(block, "h2", "h3") or img_alt
        summary = first_tag_text(block, "p")
        date_text = find_date_text(block)
        published_at = parse_date(date_text)

        if not is_probable_article(url, title, base_url):
            continue

        items.append({
            "id": make_id(url),
            "title": title[:180],
            "url": url,
            "source": source["name"],
            "sourceUrl": base_url,
            "market": source.get("market", ""),
            "language": source.get("language", ""),
            "category": classify(title, summary),
            "publishedAt": published_at,
            "publishedText": date_text,
            "summary": summary[:260],
            "imageUrl": img_url,
            "imageAlt": img_alt,
            "usage": "Use as topic research and cite the source. Do not republish full text or download the image without permission."
        })

    return dedupe(items)


def pagination_links(source_url: str, page_html: str) -> list[str]:
    source = urlparse(source_url)
    source_path = source.path.rstrip("/")
    links: list[str] = []
    for match in re.finditer(r"<a\b([^>]*)>", page_html, flags=re.I):
        href = attr_value(match.group(1), "href")
        if not href:
            continue
        url = urljoin(source_url, href)
        parsed = urlparse(url)
        if parsed.netloc != source.netloc:
            continue
        if parsed.path.rstrip("/") != source_path:
            continue
        if "page=" not in parsed.query.lower():
            continue
        links.append(url)
    return sorted(set(links))


def crawl_source(source: dict[str, Any], max_pages: int, max_per_source: int) -> list[dict[str, Any]]:
    pending = [source["url"]]
    visited: set[str] = set()
    items: list[dict[str, Any]] = []

    while pending and len(visited) < max_pages and len(items) < max_per_source:
        url = pending.pop(0)
        if url in visited:
            continue
        visited.add(url)
        body = fetch(url)
        items.extend(parse_listing({**source, "url": url}, body))
        for next_url in pagination_links(url, body):
            if next_url not in visited and next_url not in pending:
                pending.append(next_url)

    return dedupe(items)[:max_per_source]


def dedupe(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    for item in items:
        key = item["id"]
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def sort_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: item.get("publishedAt") or "1970-01-01T00:00:00+00:00",
        reverse=True
    )


def enrich_items(items: list[dict[str, Any]], limit: int | None = None) -> list[dict[str, Any]]:
    output = []
    for index, item in enumerate(items):
        enriched = dict(item)
        if limit is None or index < limit:
            try:
                enriched.update(extract_detail_brief(item["url"]))
            except (HTTPError, URLError, TimeoutError, OSError) as exc:
                enriched["detailError"] = str(exc)
        output.append(enriched)
    return output


def topic_ideas(items: list[dict[str, Any]], limit: int = 20) -> list[dict[str, str]]:
    ideas = []
    for item in items[:limit]:
        title = item["title"]
        category = item["category"]
        ideas.append({
            "topic": f"{category}: {title}",
            "angle": "Write an original local-market article with your own examples, checklist, pricing context, and source citation.",
            "source": item["url"]
        })
    return ideas


def escape(value: str) -> str:
    return html.escape(str(value or ""), quote=True)


def render_report(data: dict[str, Any]) -> str:
    cards = []
    for item in data["items"]:
        image = ""
        if item.get("imageUrl"):
            image = (
                f'<a class="collector-thumb" href="{escape(item["imageUrl"])}" target="_blank" rel="noopener">'
                f'<img src="{escape(item["imageUrl"])}" alt="{escape(item.get("imageAlt") or item["title"])}" loading="lazy"></a>'
            )
        outline = "".join(f"<li>{escape(text)}</li>" for text in item.get("outline", [])[:6])
        notes = "".join(f"<li>{escape(text)}</li>" for text in item.get("researchNotes", [])[:3])
        cards.append(f"""
        <article class="collector-card">
          {image}
          <div class="collector-body">
            <span>{escape(item.get("category", ""))} / {escape(item.get("source", ""))}</span>
            <h2>{escape(item["title"])}</h2>
            <p>{escape(item.get("detailSummary") or item.get("summary", ""))}</p>
            <a href="{escape(item["url"])}" target="_blank" rel="noopener">打开参考文章</a>
            <h3>参考目录</h3>
            <ol>{outline or "<li>未提取到目录</li>"}</ol>
            <h3>原创改写方向</h3>
            <p>{escape(item.get("rewriteBrief", ""))}</p>
            <h3>研究笔记</h3>
            <ul>{notes or "<li>未提取到笔记</li>"}</ul>
          </div>
        </article>""")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>参考博客采集报告</title>
  <style>
    body {{ margin: 0; color: #17202a; background: #f8fbfd; font-family: "Microsoft YaHei", Arial, sans-serif; line-height: 1.65; }}
    main {{ width: min(1180px, calc(100% - 36px)); margin: 0 auto; padding: 42px 0 72px; }}
    header {{ margin-bottom: 26px; }}
    h1 {{ margin: 0 0 10px; font-size: clamp(28px, 4vw, 44px); line-height: 1.15; }}
    p {{ color: #5b6875; }}
    .collector-grid {{ display: grid; gap: 18px; }}
    .collector-card {{ display: grid; grid-template-columns: minmax(220px, .42fr) minmax(0, 1fr); gap: 18px; padding: 18px; border: 1px solid #dce7ef; border-radius: 10px; background: #fff; box-shadow: 0 18px 38px rgba(22, 42, 62, .07); }}
    .collector-thumb img {{ width: 100%; aspect-ratio: 16 / 9; object-fit: cover; border-radius: 8px; background: #eef4f8; }}
    .collector-body span {{ color: #0f5f9f; font-size: 13px; font-weight: 800; }}
    .collector-body h2 {{ margin: 8px 0; font-size: 22px; line-height: 1.3; }}
    .collector-body h3 {{ margin: 18px 0 6px; font-size: 16px; }}
    .collector-body a {{ color: #0f5f9f; font-weight: 800; }}
    ol, ul {{ margin: 0; padding-left: 22px; }}
    li {{ margin: 3px 0; }}
    @media (max-width: 760px) {{ .collector-card {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>参考博客采集报告</h1>
      <p>生成时间：{escape(data["generatedAt"])}。本报告只用于选题研究，采集标题、摘要、图片参考地址、目录和少量研究笔记，不保存或发布第三方全文。</p>
    </header>
    <section class="collector-grid">
      {"".join(cards)}
    </section>
  </main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect article metadata from configured blog sources.")
    parser.add_argument("--sources", default=str(SOURCE_PATH), help="Path to article-sources.json")
    parser.add_argument("--output", default=str(OUTPUT_PATH), help="Path to output JSON")
    parser.add_argument("--report", default=str(REPORT_PATH), help="Path to output HTML report")
    parser.add_argument("--max-per-source", type=int, default=40)
    parser.add_argument("--max-pages", type=int, default=5)
    parser.add_argument("--detail-limit", type=int, default=30, help="Number of collected article pages to inspect for outlines")
    args = parser.parse_args()

    source_path = Path(args.sources)
    output_path = Path(args.output)
    config = json.loads(source_path.read_text(encoding="utf-8"))

    all_items: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for source in config.get("sources", []):
        try:
            parsed = crawl_source(source, args.max_pages, args.max_per_source)
            all_items.extend(parsed)
            print(f"{source['name']}: collected {len(parsed)} items")
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            errors.append({"source": source.get("name", source.get("url", "")), "error": str(exc)})
            print(f"{source.get('name', source.get('url'))}: failed: {exc}", file=sys.stderr)

    all_items = enrich_items(sort_items(dedupe(all_items)), args.detail_limit)
    result = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sourcesChecked": len(config.get("sources", [])),
        "copyrightPolicy": config.get("copyrightPolicy"),
        "items": all_items,
        "topicIdeas": topic_ideas(all_items),
        "errors": errors
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(result), encoding="utf-8")
    print(f"Wrote {len(all_items)} articles to {output_path}")
    print(f"Wrote HTML report to {report_path}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
