#!/usr/bin/env python3
"""autoresearch · deepresearch 模式深度综述渲染

用法:
    python render_deepresearch.py data.json --date 2026-08-12 --out output/<slug>-research-<日期>.md

输入 data.json( agent 构造,结构见 references/deepresearch.md ):
    {topic, materials, sections, comparison_table, gaps}
输出:分章节深度技术综述长文。

本脚本只做格式拼装,不调 LLM —— 多 agent 的检索/分析/综合由 agent 在调用前完成。
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def render(data, date):
    topic = data.get("topic", "")
    materials = data.get("materials", [])
    sections = data.get("sections", [])
    table = data.get("comparison_table", [])
    gaps = data.get("gaps", [])
    overview = data.get("overview", "")
    rounds = data.get("rounds", [])  # 检索过程:[{round, queries, new_count}], 可选

    lines = [
        f"# 深度综述 · {topic}",
        "",
        f"> **主题**:{topic}  ",
        f"> **材料数**:{len(materials)} 篇/项  ",
        f"> **检索源**:arXiv · GitHub · Web · 社区( 中英 )  ",
        f"> **生成方式**:autoresearch skill · deepresearch 模式( 迭代循环 + 多 agent )  ",
        f"> **生成日期**:{date}",
        "",
        "---",
        "",
    ]

    # 0. 概览
    lines.append("## 0. 概览")
    lines.append("")
    lines.append(overview or f"本综述围绕「{topic}」,深度分析 {len(materials)} 个核心工作/项目,按技术路线分类并横向对比。")
    lines.append("")

    # 检索过程( 可选,展示迭代循环以增可信度/可复现 )
    if rounds:
        total_n = sum(r.get("new_count", 0) for r in rounds)
        lines.append("<details><summary>📋 检索过程( 迭代循环,{0} 轮 / 累计 {1} 条 )</summary>".format(len(rounds), total_n))
        lines.append("")
        for r in rounds:
            qs = "、".join(f"`{q}`" for q in r.get("queries", []))
            lines.append(f"- **第{r.get('round', '?')}轮**(+{r.get('new_count', 0)}):{qs}")
        lines.append("")
        lines.append("</details>")
        lines.append("")

    # 正文章节( 写作 agent 产出 )
    for sec in sections:
        title = sec.get("title", "")
        body = sec.get("body", "").strip()
        sources = sec.get("sources", [])
        lines.append(f"## {title}")
        lines.append("")
        lines.append(body)
        if sources:
            lines.append("")
            lines.append("**出处**:" + " · ".join(f"`{s}`" for s in sources))
        lines.append("")
        lines.append("---")
        lines.append("")

    # 横向对比表
    if table and len(table) >= 2:
        lines.append("## 横向对比")
        lines.append("")
        header = table[0]
        lines.append("| " + " | ".join(str(c) for c in header) + " |")
        lines.append("|" + "|".join("---" for _ in header) + "|")
        for row in table[1:]:
            lines.append("| " + " | ".join(str(c) for c in row) + " |")
        lines.append("")
        lines.append("---")
        lines.append("")

    # 开放问题 / 未覆盖
    lines.append("## 开放问题 / 未覆盖")
    lines.append("")
    if gaps:
        for g in gaps:
            lines.append(f"- {g}")
    else:
        lines.append("_( 暂无,或材料覆盖完整 )_")
    lines.append("")

    # 附录:材料清单
    lines.append("## 附录:材料清单")
    lines.append("")
    lines.append("| # | 材料 | 来源 | 阅读程度 | 链接 |")
    lines.append("|---|---|---|---|---|")
    for i, m in enumerate(materials, 1):
        src = m.get("source", "")
        read = m.get("read", "")
        title = m.get("title", "")
        url = m.get("url", "")
        lines.append(f"| {i} | {title} | {src} | {read} | {url} |")
    lines.append("")
    lines.append("---")
    lines.append("*由 autoresearch skill(deepresearch 模式)生成。结论标注出处;未覆盖项单独列出,不编造。*")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="autoresearch deepresearch 综述渲染")
    ap.add_argument("data", help="综述数据 JSON")
    ap.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), help="日期")
    ap.add_argument("--out", default="-", help="输出 md,- 为 stdout")
    args = ap.parse_args()
    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    md = render(data, args.date)
    if args.out == "-":
        print(md)
    else:
        Path(args.out).write_text(md, encoding="utf-8")
        print(f"[render_deepresearch] 综述 → {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
