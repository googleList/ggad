# HTTP Canonicalization: Owner Action Required

## 需要你处理的步骤

1. 登录 Cloudflare，选择 `shumaojs.com` 域名，然后回复刚才的授权问题。不要在聊天或仓库提供密码、验证码或 API Token。
2. 拟检查并设置一条仅针对 HTTP 主域名及 www 的永久301跳转，目标为 `https://shumaojs.com` 加原路径，并保留查询参数；已经是 HTTPS 主域名的请求不能再次匹配。先检查已有规则，不重复创建冲突规则。
3. 本次不改 DNS、证书、TLS 模式或其他子域名；未获得这次授权前不会代你改控制台。GitHub 提交代码不能证明 Cloudflare 跳转已启用。
4. 配置后按下面矩阵核验实际 GET/HEAD，再观察后续 Search Console。无需删除 Search Console 属性、历史记录或 HTTP 网址来掩盖问题。

## Evidence

The latest owner-authorized GSC comparison reads October17-23 versusOctober10-16. It reports `http://shumaojs.com/` with2impressions/0clicks/average1.0 in the current week; HTTPS homepage separately has2/0/6.0. These are reported URL rows, not proof of a stable first place, a crawl/indexing diagnosis or the cause of zero clicks. [Snapshot](../search-console/2026-10-25-settled-follow-up.json) keeps both URLs distinct.

Fresh [deployment audit](2026-10-25-http-search-signal.json):64local and64production sitemap URLs, zero missing/production-only. HTTP apex HEAD returns200 with no redirect; HTTP www301 ends at HTTP apex; HTTPS www301 ends at HTTPS apex. `--fail-on-drift` correctly exits1 for unresolved protocol/alias enforcement, not a missing website deployment. This audit checks sitemap parity and redirects, not successful fetching of every listed page.

[Additional probes](2026-10-25-path-query-probes.json): HTTP service path/query remainsHTTP200, HTTPwww preserves path/query but endsHTTP, HTTPSwww ends at correctHTTPS path/query. Separate root GET returns200, noLocation, servercloudflare. An earlier Python GET loop timed out without usable per-URL evidence; do not label those service GETs passed. No JavaScript analytics executed by these requests.

## Proposed Narrow Change, Not Applied

After the owner signs into Cloudflare and authorizes this specific change, inspect current rules first. Prefer one hostname-scoped Single Redirect over a global all-subdomain switch if other subdomains are not audited:

1. Select the `shumaojs.com` zone, open Rules and Single Redirects; confirm current rules/order and the two existing hostnames. Do not modify DNS, the custom-domain CNAME, origin TLS mode, certificates or unrelated rules.
2. Limit matching to either HTTP requests on the apex, or requests on `www.shumaojs.com`. Explicitly exclude the already-canonical HTTPS apex to avoid a loop. This describes the intended predicate, not a rule already tested/deployed in the dashboard.
3. Set the destination dynamically to the HTTPS apex plus the original URI path: `concat("https://shumaojs.com", http.request.uri.path)`; status301; enable Preserve query string. Review the generated rule and its real request traces before enabling it. This narrow implementation combines the canonical-host and protocol intent; it must not affect other subdomains.
4. Recheck the matrix below with both GET and HEAD, not just a green dashboard toggle. Keep a record of the previous state so the owner can disable this exact rule if it causes a loop or unexpected routing.

Cloudflare documents [WWW-to-root redirects with path/query preservation](https://developers.cloudflare.com/rules/url-forwarding/examples/redirect-www-to-root/) and [subdomain redirect expressions](https://developers.cloudflare.com/fundamentals/manage-domains/manage-subdomains/). The combined hostname-scoped predicate above is a proposed adaptation, not a claim that the stock HTTPS-only WWW example handles HTTP. [Always Use HTTPS](https://developers.cloudflare.com/ssl/edge-certificates/additional-options/always-use-https/) is another supported option, but applies to every hostname/subdomain in the zone; do not turn it on globally without checking that scope.

GitHub also supports [Pages Enforce HTTPS](https://docs.github.com/en/pages/getting-started-with-github-pages/securing-your-github-pages-site-with-https). Current unauthenticated Pages API returned404 and the opened settings UI showed Sign in/404: the setting's actual value is unknown, not proven off or absent. Do not remove/re-add the domain or bypass permissions to expose this control. Git SSH push access alone is not Pages administration. The currently observed HTTP response is served through Cloudflare, so edge validation remains necessary even if an origin checkbox is later changed.

## Acceptance Matrix

| Request | Required end state |
|---|---|
| `http://shumaojs.com/` | Permanent301/308 to `https://shumaojs.com/`, then200 |
| `http://www.shumaojs.com/` | Permanent redirect(s) ending at HTTPS apex, then200 |
| `https://www.shumaojs.com/` | Permanent redirect ending at HTTPS apex, then200 |
| `https://shumaojs.com/` |200, no redirect loop |
| Each service path above with `?seo-probe=protocol` | Path and query retained exactly at HTTPS apex |
| Missing or retired URL over HTTP | HTTPS normalization may precede the existing404; never redirect every missing URL home |

Re-run `python -B scripts/deployment_drift_audit.py --fail-on-drift` with new after-change report paths, preserving the failing baseline. Verify canonical HTML/sitemap/feed remainHTTPS, then observe a later GSC window/crawl. Do not use Search Console removal, property deletion or a JavaScript/meta-refresh workaround to hide the HTTP row, and do not claim the issue fixed before live redirects pass.

## Access and Authorization

Asked the owner specifically to sign into the Cloudflare zone and authorize a301 normalization for only HTTP apex/www, preserving path/query and not changingDNS/other subdomains. Awaiting reply. No Cloudflare configuration, GitHub Pages setting, login credential or GSC indexing/removal setting changed. Do not request/store an API token or password in this public repository.
