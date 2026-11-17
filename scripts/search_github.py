#!/usr/bin/env python3
"""autoresearch · GitHub 检索 adapter

用法:
    python search_github.py "autonomous research agent" [--days 7] [--max 20]
        [--sort best|stars|updated] [--min-stars 20] [--token $GITHUB_TOKEN] [--out results.json]

检索仓库( 按 pushed 限定时间窗保证"活的" ),输出统一条目 schema JSON。
排序:默认 best( GitHub 相关性,推荐语义 query );updated=最近推送( 只用于窄域查活跃度,
    宽泛语义 query 下会被当天垃圾推送淹没 );stars=按 star 找头部项目。
--min-stars:客户端过滤低星噪声( 语义宽 query 建议 ≥10-20;精确名/组织名 query 不要加,
    否则会把新项目滤掉 )。
依赖:仅标准库。GitHub 未鉴权搜索有速率限制( ~10 次/分钟 ),建议传 GITHUB_TOKEN。
失败兜底:错误时输出 {"error":...} 到 stderr 并非零退出 → SKILL.md fallback( WebSearch 搜 github )。
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

GITHUB_API = "https://api.github.com/search/repositories"


def build_query(query, days):
    # 按最近 push 时间过滤,保证是"活的"项目
    if days:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        q = f"{query} pushed:>{since}"
    else:
        q = query
    return q


def fetch(query, days, sort, token=None):
    q = build_query(query, days)
    # best = 不传 sort( GitHub 默认相关性排序 );updated/stars 显式传。
    # 固定 per_page=100 + 客户端过滤/截断:一次请求,便于 --min-stars 过滤后仍够量。
    params = {"q": q, "order": "desc", "per_page": 100}
    if sort in ("stars", "updated"):
        params["sort"] = sort
    url = GITHUB_API + "?" + urllib.parse.urlencode(params)
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "autoresearch/0.1"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def normalize(raw):
    items = []
    for r in raw.get("items", []):
        items.append({
            "source": "github",
            "title": r.get("full_name", ""),
            "url": r.get("html_url", ""),
            "authors_or_owner": r.get("owner", {}).get("login", ""),
            "date": (r.get("pushed_at") or "")[:10],
            "summary_raw": (r.get("description") or "").strip(),
            "type": "repo",
            "meta": {
                "stars": r.get("stargazers_count", 0),
                "language": r.get("language") or "",
                "topics": r.get("topics", []),
            },
        })
    return items


def main():
    ap = argparse.ArgumentParser(description="autoresearch GitHub 检索")
    ap.add_argument("query", help="检索词")
    ap.add_argument("--days", type=int, default=None, help="时间窗( 按 pushed 过滤 ),不传则不限")
    ap.add_argument("--max", type=int, default=20, help="最大拉取条数")
    ap.add_argument("--sort", choices=["best", "stars", "updated"], default="best",
                    help="排序:best=相关性( 默认,语义 query 用 )|stars=找头部|updated=最近推送( 仅窄域活跃度 )")
    ap.add_argument("--min-stars", type=int, default=0,
                    help="最低 star 过滤( 语义宽 query 建议 10-20;精确名 query 别加,防滤掉新项目 )")
    ap.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""), help="GitHub token,默认读 $GITHUB_TOKEN")
    ap.add_argument("--out", default="-", help="输出 JSON 路径,- 为 stdout")
    args = ap.parse_args()
    try:
        raw = fetch(args.query, args.days, args.sort, args.token or None)
        items = normalize(raw)
        if args.min_stars > 0:
            items = [i for i in items if (i.get("meta") or {}).get("stars", 0) >= args.min_stars]
        items = items[: args.max]
        payload = {"source": "github", "query": args.query, "count": len(items), "items": items}
    except Exception as e:
        print(json.dumps({"error": f"github fetch/parse failed: {e}", "items": []}), file=sys.stderr)
        sys.exit(1)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out == "-":
        print(text)
    else:
        from pathlib import Path
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"[github] {len(items)} 条 → {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
