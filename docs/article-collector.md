# 参考博客采集工具

这个工具用于定期采集广告、SEO、GEO、建站和数据追踪相关博客资料，当前来源包括：

- https://www.kickads.co/zh/blog
- https://horntech.com.au/zh/blog/

工具会保存：

- 文章标题
- 文章链接
- 发布时间
- 分类
- 来源名称和目标市场标签（不是已验证的读者需求）
- 独立编辑清单与待审状态

工具不保存原文段落、摘要、目录或图片地址，报告不自动热链图片。标题和来源链接只供识别候选话题，不是已审核事实、原创建议或已验证搜索量。应先匹配既有页面，独立规划标题与大纲，核对官方资料，使用原创或已授权图片；不得虚构价格、资质、案例或效果。真实人工审稿单独记录，工具不自动发布文章。

## 本地运行

```bash
python -B scripts/collect_articles.py --max-pages 5 --max-per-source 40 --detail-limit 0
```

输出文件：

- `data/collected-articles.json`
- `reports/collected-articles.html`

默认只读取列表页。`--detail-limit N` 可选读取前 N 项详情页中的标题元数据，也不会提取正文或来源目录。结果链接只接受不带凭据的 HTTP(S) 网址。

迁移已有旧数据而不访问任何来源：

```bash
python -B scripts/collect_articles.py --sanitize-existing
```

此操作保留原采集时间、候选ID、来源与顺序，移除旧内容和图片字段，重建编辑清单及本地报告；另记 `policyUpdatedAt`，不假称重新采集或人工审核通过。它不改写Git历史、删除远程Actions工件或清理第三方缓存。

## GitHub 自动运行

`.github/workflows/weekly-article-collector.yml` 每周一 09:30（北京时间）运行；采集器代码、来源配置或 workflow 改动时也会自动做一次验证，并支持在 GitHub Actions 页面手动触发。生成数据文件不会触发它自身再次运行。

- 广告学习资源采集器读取可访问的官方及行业 RSS，只更新 `ad-learning.html`、`data/ad-learning.json` 和对应的 sitemap `lastmod`；所有来源都失败时会停止，避免把过期内容标成新内容。
- Kick Ads 和 HornTech 候选结果作为 GitHub Actions 工件保存 90 天，不自动发布到网站。工件只保留题目、链接、日期、分类和独立编辑清单；工作流使用 `--detail-limit 0`，不逐一读取详情页。
- 本地 `data/collected-articles.json` 及 `reports/collected-articles.html` 也不会进入公开网站构建产物；仓库可见性与网站部署范围是两回事。
- 部分来源失败会保留已成功采集的结果并在运行日志/工件中记录；中文 URL 会先进行百分号编码。

## 新增来源

编辑 `data/article-sources.json`，按下面格式添加：

```json
{
  "name": "来源名称",
  "url": "https://example.com/blog/",
  "market": "目标市场",
  "language": "zh",
  "topic": "SEO, Google Ads, Meta Ads"
}
```
