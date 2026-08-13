#!/usr/bin/env python3
"""autoresearch · arXiv 检索 adapter

用法:
    python search_arxiv.py "world model for agent" [--days 7] [--max 20] [--out results.json]

输出统一条目 schema 的 JSON 数组(详见 references/filtering.md):
    [{source, title, url, authors_or_owner, date, summary_raw, type, meta}, ...]

依赖:仅标准库( urllib + json + xml.etree ),零安装。
失败兜底:网络/解析错误时输出 {"error": "...", "items": []} 到 stderr 并以非零码退出,
        让 SKILL.md 的 fallback 逻辑接管( 改用 WebSearch 搜 arxiv )。
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

ARXIV_API = "http://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom"}


def fetch(query, start=0, max_results=20, fields="ti_abs"):
    """fields:
       ti_abs( 默认 ) = 标题+摘要精确匹配,降噪( 避免 all: 全文噪声 )
       all            = 全文模糊匹配,召回广但噪声大
    """
    if fields == "all":
        q = f"all:{query}"
    else:
        # 把多词 query 拆成 ti: 和 abs: 的 AND,提高相关性
        terms = [t for t in query.split() if t]
        if len(terms) > 1:
            ti_part = " AND ".join(f"ti:{t}" for t in terms)
            abs_part = " AND ".join(f"abs:{t}" for t in terms)
            q = f"({ti_part}) OR ({abs_part})"
        else:
            q = f"(ti:{query} OR abs:{query})"
    params = {
        "search_query": q,
        "start": str(start),
        "max_results": str(max_results),
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = ARXIV_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "autoresearch/0.1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse(xml_text, days=None):
    root = ET.fromstring(xml_text)
    cutoff = None
    if days:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    items = []
    for e in root.findall("a:entry", NS):
        # 更新时间:<updated>2026-08-10T00:00:00Z</updated>
        updated_raw = e.findtext("a:updated", default="", namespaces=NS)
        try:
            dt = datetime.strptime(updated_raw[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except Exception:
            dt = None
        if cutoff and dt and dt < cutoff:
            continue  # 超出时间窗,跳过
        arxiv_id = (e.findtext("a:id", default="", namespaces=NS) or "").rsplit("/", 1)[-1]
        authors = [a.findtext("a:name", default="", namespaces=NS) for a in e.findall("a:author", NS)]
        items.append({
            "source": "arxiv",
            "title": (e.findtext("a:title", default="", namespaces=NS) or "").strip().replace("\n", " "),
            "url": f"https://arxiv.org/abs/{arxiv_id}",
            "authors_or_owner": ", ".join(authors[:5]) + ("…" if len(authors) > 5 else ""),
            "date": updated_raw[:10],
            "summary_raw": (e.findtext("a:summary", default="", namespaces=NS) or "").strip().replace("\n", " "),
            "type": "paper",
            "meta": {"arxiv_id": arxiv_id, "categories": [t.get("term", "") for t in e.findall("a:category", NS)]},
        })
    return items


def main():
    ap = argparse.ArgumentParser(description="autoresearch arXiv 检索")
    ap.add_argument("query", help="检索词")
    ap.add_argument("--days", type=int, default=None, help="时间窗( 天 ),不传则不限")
    ap.add_argument("--max", type=int, default=20, help="最大拉取条数")
    ap.add_argument("--fields", default="ti_abs", choices=["ti_abs", "all"],
                    help="ti_abs=标题+摘要精确(默认,降噪);all=全文模糊(召回广噪声大)")
    ap.add_argument("--out", default="-", help="输出 JSON 路径,- 为 stdout")
    args = ap.parse_args()
    try:
        xml_text = fetch(args.query, max_results=args.max, fields=args.fields)
        items = parse(xml_text, days=args.days)
        payload = {"source": "arxiv", "query": args.query, "count": len(items), "items": items}
    except Exception as e:
        print(json.dumps({"error": f"arxiv fetch/parse failed: {e}", "items": []}), file=sys.stderr)
        sys.exit(1)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out == "-":
        print(text)
    else:
        from pathlib import Path
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"[arxiv] {len(items)} 条 → {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
