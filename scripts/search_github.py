#!/usr/bin/env python3
"""autoresearch · GitHub 检索 adapter

用法:
    python search_github.py "autonomous research agent" [--days 7] [--max 20] [--token $GITHUB_TOKEN] [--out results.json]

检索最近更新/创建的仓库( 按 pushed/created 限定时间窗 ),输出统一条目 schema JSON。
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


def fetch(query, days, max_results, token=None):
    q = build_query(query, days)
    params = {"q": q, "sort": "updated", "order": "desc", "per_page": min(max_results, 100)}
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
    ap.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""), help="GitHub token,默认读 $GITHUB_TOKEN")
    ap.add_argument("--out", default="-", help="输出 JSON 路径,- 为 stdout")
    args = ap.parse_args()
    try:
        raw = fetch(args.query, args.days, args.max, args.token or None)
        items = normalize(raw)
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
