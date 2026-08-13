#!/usr/bin/env python3
"""autoresearch · 跨源去重

用法:
    python dedupe.py arxiv.json github.json web.json [--out merged.json]

输入:多个 adapter 输出的 JSON( 每个 {source, items:[...]} ),或单个 items 数组文件。
输出:合并去重后的统一条目列表 JSON。

去重策略( 双保险,详见 references/filtering.md ):
  1. URL 规范化去重:去掉查询参数/尾部斜杠/arxiv abs→pdf 等价
  2. 标题归一化去重:小写 + 去标点 + 压空格,完全相同视为重复

仅做规则去重;语义级近似去重( 同一事件不同措辞 )交给 agent 在简评阶段判断。
"""
import argparse
import json
import re
import sys
from pathlib import Path


def norm_url(url):
    url = (url or "").strip().lower()
    url = re.sub(r"[?#].*$", "", url)            # 去查询串/锚点
    url = url.rstrip("/")
    # arxiv abs/pdf/html 等价
    url = re.sub(r"arxiv\.org/(abs|pdf|html)/", "arxiv.org/abs/", url)
    return url


def norm_title(title):
    t = (title or "").lower()
    t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE)  # 去标点
    t = re.sub(r"\s+", " ", t).strip()
    return t


def load_items(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    return []


def dedupe(item_lists):
    seen_url, seen_title = set(), set()
    out = []
    for items in item_lists:
        for it in items:
            u = norm_url(it.get("url", ""))
            t = norm_title(it.get("title", ""))
            if u and u in seen_url:
                continue
            if t and t in seen_title:
                continue
            if u:
                seen_url.add(u)
            if t:
                seen_title.add(t)
            out.append(it)
    return out


def main():
    ap = argparse.ArgumentParser(description="autoresearch 跨源去重")
    ap.add_argument("inputs", nargs="+", help="输入 JSON 文件( adapter 输出 )")
    ap.add_argument("--out", default="-", help="输出路径,- 为 stdout")
    args = ap.parse_args()
    try:
        item_lists = [load_items(p) for p in args.inputs]
        before = sum(len(x) for x in item_lists)
        merged = dedupe(item_lists)
        payload = {"count_before": before, "count_after": len(merged), "items": merged}
    except Exception as e:
        print(json.dumps({"error": f"dedupe failed: {e}", "items": []}), file=sys.stderr)
        sys.exit(1)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out == "-":
        print(text)
    else:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"[dedupe] {before} → {len(merged)} 条 → {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
