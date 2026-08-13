#!/usr/bin/env python3
"""autoresearch · 社区源检索 adapter( 英文 HN/Reddit )

用法:
    python search_community.py "agentic reinforcement learning" [--days 30] [--max 15] [--out tmp/community.json]

英文社区源:
- HackerNews( Algolia API,稳定,带 points/comment 热度信号 ) ← 主力
- Reddit( JSON API,需 UA;不稳定时降级 )
输出统一条目 schema,source=community,type=discussion,meta 含 points/comments( 热点检测用 )。
失败兜底:某源失败跳过,继续其他;全失败输出空 + error。
"""
import argparse
import json
import sys
import subprocess
from datetime import datetime, timedelta, timezone

HN_API = "https://hn.algolia.com/api/v1/search"


def curl_json(url, timeout=30):
    """用 curl 抓 JSON( 比 urllib 更能绕基础反爬,如 Reddit )。"""
    r = subprocess.run(
        ["curl", "-sL", "-A", "Mozilla/5.0 autoresearch/0.1", "--max-time", str(timeout), url],
        capture_output=True, timeout=timeout + 10,
    )
    return json.loads(r.stdout.decode("utf-8", errors="replace"))


def search_hn(query, days, max_results):
    """HN Algolia:tags=story,按时间过滤,带热度。"""
    params = {"query": query, "tags": "story", "hitsPerPage": min(max_results, 50)}
    url = HN_API + "?" + "&".join(f"{k}={v}" for k, v in params.items()).replace(" ", "+")
    data = curl_json(url)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days) if days else None
    items = []
    for h in data.get("hits", []):
        ts = h.get("created_at_i")
        if cutoff and ts and datetime.fromtimestamp(ts, tz=timezone.utc) < cutoff:
            continue
        items.append({
            "source": "community",
            "title": h.get("title") or h.get("story_title") or "",
            "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID','')}",
            "authors_or_owner": h.get("author", ""),
            "date": datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d") if ts else "",
            "summary_raw": (h.get("story_text") or "").strip()[:500],
            "type": "discussion",
            "meta": {
                "platform": "hackernews",
                "points": h.get("points") or 0,
                "comments": h.get("num_comments") or 0,
                "hn_id": h.get("objectID", ""),
            },
        })
    return items


def search_reddit(query, days, max_results, subreddit="MachineLearning"):
    """Reddit JSON search。不稳定,失败抛异常由上层降级。"""
    q = query.replace(" ", "%20")
    url = f"https://www.reddit.com/r/{subreddit}/search.json?q={q}&restrict_sr=1&limit={min(max_results,25)}&sort=new"
    data = curl_json(url)
    items = []
    for p in data.get("data", {}).get("children", []):
        pd = p["data"]
        items.append({
            "source": "community",
            "title": pd.get("title", ""),
            "url": pd.get("url", ""),
            "authors_or_owner": pd.get("author", ""),
            "date": datetime.fromtimestamp(pd.get("created_utc", 0)).strftime("%Y-%m-%d") if pd.get("created_utc") else "",
            "summary_raw": (pd.get("selftext") or "").strip()[:500],
            "type": "discussion",
            "meta": {
                "platform": "reddit",
                "points": pd.get("score", 0),
                "comments": pd.get("num_comments", 0),
                "subreddit": pd.get("subreddit", ""),
            },
        })
    return items


def main():
    ap = argparse.ArgumentParser(description="autoresearch 社区源检索( HN/Reddit )")
    ap.add_argument("query", help="检索词( 建议:英文 )")
    ap.add_argument("--days", type=int, default=30, help="时间窗( 天 ),默认 30")
    ap.add_argument("--max", type=int, default=15, help="每个源最大条数")
    ap.add_argument("--reddit", action="store_true", help="同时查 Reddit( 默认仅 HN )")
    ap.add_argument("--out", default="-", help="输出 JSON,- 为 stdout")
    args = ap.parse_args()

    items, errors = [], []
    try:
        items += search_hn(args.query, args.days, args.max)
    except Exception as e:
        errors.append(f"HN: {e}")
    if args.reddit:
        try:
            items += search_reddit(args.query, args.days, args.max)
        except Exception as e:
            errors.append(f"Reddit: {e}")

    payload = {"source": "community", "query": args.query, "count": len(items), "items": items}
    if errors:
        payload["errors"] = errors
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out == "-":
        print(text)
    else:
        from pathlib import Path
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"[community] {len(items)} 条( errors: {len(errors)} )→ {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
