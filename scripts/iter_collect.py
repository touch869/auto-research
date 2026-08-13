#!/usr/bin/env python3
"""autoresearch · 迭代检索的累积去重器

维护跨轮的检索历史,支持增量去重。dedupe.py 是一次性合并,本脚本管持久化历史。

用法:
    # 第1轮:初始化历史 + 加入新结果
    python iter_collect.py --history tmp/history.json --add tmp/round1_arxiv.json tmp/round1_github.json

    # 第2轮:读历史 + 加入新轮结果( 自动跳过已收集的 )
    python iter_collect.py --history tmp/history.json --add tmp/round2_arxiv.json

    # 查看历史统计
    python iter_collect.py --history tmp/history.json --stat

history.json 结构:
    {
      "rounds": [
        {"round": 1, "queries": [...], "new_count": N, "items": [...]},
        {"round": 2, ...}
      ],
      "all_items": [...],   # 累积去重后的全部条目
      "total": N
    }
"""
import argparse
import json
import sys
from pathlib import Path

# 复用 dedupe 的归一化逻辑
sys.path.insert(0, str(Path(__file__).parent))
from dedupe import norm_url, norm_title, load_items  # noqa: E402


def load_history(path):
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"rounds": [], "all_items": [], "total": 0, "seen_url": [], "seen_title": []}


def add_round(history, new_item_files, round_num, queries=None):
    """加入一轮的新结果,累积去重。返回 (该轮新增数, 历史总数)。"""
    seen_url = set(history.get("seen_url", []))
    seen_title = set(history.get("seen_title", []))
    new_items = []
    for f in new_item_files:
        try:
            items = load_items(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[iter] 跳过缺失/损坏文件 {f}: {e}", file=sys.stderr)
            continue
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
            new_items.append(it)
    history["rounds"].append({
        "round": round_num,
        "queries": queries or [],
        "new_count": len(new_items),
        "items": new_items,
    })
    history["all_items"] = (history.get("all_items", []) or []) + new_items
    history["seen_url"] = list(seen_url)
    history["seen_title"] = list(seen_title)
    history["total"] = len(history["all_items"])
    return len(new_items), history["total"]


def main():
    ap = argparse.ArgumentParser(description="autoresearch 迭代累积去重")
    ap.add_argument("--history", required=True, help="历史 JSON 路径( 持久化 )")
    ap.add_argument("--add", nargs="*", help="本轮新增的 adapter 输出文件")
    ap.add_argument("--round", type=int, default=None, help="轮次号( 不传则自动 +1 )")
    ap.add_argument("--queries", nargs="*", default=[], help="本轮用的 query( 记录用 )")
    ap.add_argument("--stat", action="store_true", help="只打印历史统计")
    args = ap.parse_args()

    history = load_history(args.history)

    if args.stat:
        print(f"总条目: {history.get('total', 0)}")
        for r in history.get("rounds", []):
            print(f"  第{r['round']}轮: +{r['new_count']} ( queries: {r.get('queries', [])} )")
        return

    if not args.add:
        print("需要 --add 或 --stat", file=sys.stderr)
        sys.exit(1)

    round_num = args.round if args.round is not None else (len(history["rounds"]) + 1)
    new_n, total = add_round(history, args.add, round_num, args.queries)
    Path(args.history).write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[iter] 第{round_num}轮: +{new_n} 新 → 累计 {total} 条 → {args.history}", file=sys.stderr)


if __name__ == "__main__":
    main()
