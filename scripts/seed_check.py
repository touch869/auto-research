#!/usr/bin/env python3
"""autoresearch · 种子核验( known-item reconciliation )

背景:关键词检索有随机性——已知的重要工件( 用户给的链接/记忆里的竞品/综述点名的系统 )
可能因排序噪声/措辞不匹配而漏收;更常见的是**检索到了但写作时没写进报告**。
本脚本在收敛前跑:把「必收清单」与**最终材料清单**比对,报出缺失项,由 agent 直接补料
( curl abs / clone / README / 旧白皮书 ),不依赖检索撞大运。

用法:
    # seeds.json: ["TokenRhythm/InfraRSI", "2611.11558", {"label":"AlphaEvolve repo","match":"google-deepmind/alphaevolve"}]
    python scripts/seed_check.py --materials tmp/research.json --seeds tmp/seeds.json
    # 可选:
    #   --history tmp/history.json  查上游语料是否漏收( 对账主对象仍是 materials )
    #   --extra a.json b.json       其他 json( 单次检索结果 / 补料暂存 )

对账对象分两账:
  --materials 交付对账( 决定是否收敛 ):读 research.json 的 materials[].url / urls[].url / title,
              也接受 {"items":[...]} / {"all_items":[...]} / 裸数组。
  --history / --extra 上游对账( 仅提示 ):上游收录了但没写进 materials 的,标 ⚠️,仍算缺失——
              事故形态恰是"检索到了、写作时没写进报告",不能因上游有就放行。
匹配规则:大小写不敏感 substring,对 url/title/arxiv_id 任一命中即算在库。
退出码:0 = 检查完成( 有缺失也是 0,属 agent 行动信号 );2 = 输入/格式错误。
"""
import argparse
import json
import re
import sys
from pathlib import Path


def load_seeds(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        if isinstance(data.get("seeds"), list):
            data = data["seeds"]
        elif data.get("match"):
            data = [data]
        else:
            raise ValueError(f"{path}: seeds 必须是数组,或 {{\"seeds\": [...]}} / 单个 {{label,match}}")
    if not isinstance(data, list):
        raise ValueError(f"{path}: seeds 必须是数组")
    seeds = []
    for i, s in enumerate(data):
        if isinstance(s, str) and s.strip():
            seeds.append({"label": s.strip(), "match": s.strip()})
        elif isinstance(s, dict) and s.get("match"):
            seeds.append({"label": s.get("label") or s["match"], "match": s["match"]})
        else:
            raise ValueError(f"{path}: 第{i}项不是字符串或 {{label,match}}: {s!r}")
    if not seeds:
        raise ValueError(f"{path}: 必收清单为空")
    return seeds


def load_items(path):
    """兼容 research.json(materials)/ history.json(all_items)/ 单次结果(items)/ 裸数组。"""
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(d, list):
        return d
    if isinstance(d, dict):
        for key in ("materials", "all_items", "items"):
            if isinstance(d.get(key), list):
                return d[key]
    raise ValueError(f"{path}: 找不到 materials/all_items/items 数组")


def item_haystack(item):
    m = item.get("meta") or {}
    parts = [item.get("url", ""), item.get("title", "")]
    # 多工件链接:论文主链接之外的第二链接( 官方 repo / demo )也要能被对账到
    for u in item.get("urls") or []:
        if isinstance(u, dict) and u.get("url"):
            parts.append(u["url"])
        elif isinstance(u, str):
            parts.append(u)
    aid = m.get("arxiv_id", "")
    if aid:
        parts.append(aid)
        parts.append(re.sub(r"v\d+$", "", aid))  # 2611.11558v1 → 2611.11558
    return " | ".join(p for p in parts if p).lower()


def main():
    ap = argparse.ArgumentParser(description="autoresearch 种子核验( 收敛前必收项对账 )")
    ap.add_argument("--materials", help="最终材料清单 research.json( 对账主对象 )")
    ap.add_argument("--history", help="可选:iter_collect 累积语料 history.json( 查上游漏收 )")
    ap.add_argument("--seeds", required=True, help="必收清单 JSON( 字符串数组或 {label,match} 数组 )")
    ap.add_argument("--extra", nargs="*", default=[], help="其他 json( 单次检索结果 / 补料暂存 )")
    ap.add_argument("--out", default="-", help="结果 JSON 路径,- 为 stdout")
    args = ap.parse_args()

    upstream_paths = [p for p in [args.history, *args.extra] if p]
    if not args.materials and not upstream_paths:
        print("[seed_check] 至少给一个 --materials / --history / --extra", file=sys.stderr)
        sys.exit(2)

    try:
        def load_all(paths):
            items = []
            for p in paths:
                items.extend(load_items(p))
            return items

        mat_items = load_all([args.materials]) if args.materials else []
        up_items = load_all(upstream_paths)
        seeds = load_seeds(args.seeds)
    except (ValueError, OSError) as e:
        print(f"[seed_check] 输入错误: {e}", file=sys.stderr)
        sys.exit(2)

    mat_hay = [item_haystack(i) for i in mat_items]
    up_hay = [item_haystack(i) for i in up_items]
    results = []
    for seed in seeds:
        needle = seed["match"].lower()
        in_mat = any(needle in h for h in mat_hay) if args.materials else None
        in_up = any(needle in h for h in up_hay) if upstream_paths else None
        results.append({**seed, "in_materials": in_mat, "in_upstream": in_up,
                        # 有 materials 时以交付物为准;否则退回上游
                        "in_corpus": in_mat if args.materials else bool(in_up)})

    missing = [r for r in results if not r["in_corpus"]]
    scope = " + ".join([Path(args.materials).name] if args.materials else [])
    if upstream_paths:
        extra = " + ".join(Path(p).name for p in upstream_paths)
        scope = f"{scope} | 上游 {extra}" if scope else f"上游 {extra}"
    print(f"[seed_check] 必收 {len(results)} 项( 对账: {scope} ):在库 {len(results) - len(missing)},缺失 {len(missing)}")
    for r in results:
        if r["in_corpus"]:
            mark = "✅"
        elif r["in_upstream"]:
            mark = "⚠️ 上游已收录但未进 materials→写回材料清单后复查( 仍算缺 )"
        else:
            mark = "❌ 缺失→补料( curl abs / clone / README )并写回 materials 后复查"
        print(f"  {mark} {r['label']}  (match: {r['match']})")

    payload = {"count": len(results), "missing": len(missing), "results": results}
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out == "-":
        print(text)
    else:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"[seed_check] → {args.out}", file=sys.stderr)
    # 有缺失也退出 0:这是给 agent 的行动信号,不是错误
    sys.exit(0)


if __name__ == "__main__":
    main()
