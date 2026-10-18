# 参考博客采集工具

这个工具用于定期采集广告、SEO、GEO、建站和数据追踪相关博客资料，当前来源包括：

- https://www.kickads.co/zh/blog
- https://horntech.com.au/zh/blog/

工具会保存：

- 文章标题
- 文章链接
- 发布时间
- 分类
- 短摘要
- 图片参考地址
- 文章目录
- 少量研究笔记
- 原创改写方向

工具不会保存或发布第三方全文，也不会下载第三方图片。采集结果适合用于选题研究、内容规划和人工原创改写。

## 本地运行

```bash
python scripts/collect_articles.py --max-pages 5 --max-per-source 40 --detail-limit 30
```

输出文件：

- `data/collected-articles.json`
- `reports/collected-articles.html`

## GitHub 自动运行

`.github/workflows/weekly-article-collector.yml` 每周一 09:30（北京时间）运行，也支持在 GitHub Actions 页面手动触发。

- 广告学习资源采集器读取可访问的官方及行业 RSS，只更新 `ad-learning.html`、`data/ad-learning.json` 和对应的 sitemap `lastmod`；所有来源都失败时会停止，避免把过期内容标成新内容。
- Kick Ads 和 HornTech 文章研究采集结果作为 GitHub Actions 工件保存 90 天，不自动发布到网站。工件只包含标题、短摘要、来源链接、图片参考地址和研究提纲，不抓取或发布全文。
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
