#!/usr/bin/env python3
"""autoresearch · deep 模式深挖报告渲染

用法:
    python render_deep.py deep_data.json --date 2026-08-12 --out output/<slug>-deep-<日期>.md

输入 deep_data.json( agent 构造,结构见 references/deep.md ):
    {
      "target": "...", "target_url": "...", "one_liner": "...",
      "qa": [{"q","a","sources"}, ...],
      "verdict": "...", "gaps": [...]
    }
输出:结构化深挖报告 Markdown。

本脚本只做格式拼装,不调 LLM —— 多轮深挖的 Q&A 由 agent 在调用前完成。
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def render(data, date):
    target = data.get("target", "")
    url = data.get("target_url", "")
    one_liner = data.get("one_liner", "")
    qa = data.get("qa", [])
    verdict = data.get("verdict", "_( 待 agent 填写综合判断 )_")
    gaps = data.get("gaps", [])

    lines = [
        f"# 深挖报告 · {target}",
        "",
        f"> **目标**:[{target}]({url})  " if url else f"> **目标**:{target}  ",
        f"> **一句话定性**:{one_liner}  ",
        f"> **生成方式**:autoresearch skill · deep 模式  ",
        f"> **生成日期**:{date}",
        "",
        "---",
        "",
        "## 逐轮深挖",
        "",
    ]
    for i, item in enumerate(qa, 1):
        q = item.get("q", "")
        a = item.get("a", "")
        sources = item.get("sources", [])
        lines.append(f"### Q{i}. {q}")
        lines.append("")
        lines.append(a.strip())
        if sources:
            src_str = " · ".join(f"`{s}`" for s in sources)
            lines.append("")
            lines.append(f"**出处**:{src_str}")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## 综合判断")
    lines.append("")
    lines.append(verdict.strip())
    lines.append("")

    if gaps:
        lines.append("## 材料未覆盖 / 待补检索")
        lines.append("")
        for g in gaps:
            lines.append(f"- {g}")
        lines.append("")

    lines.append("---")
    lines.append("*由 autoresearch skill(deep 模式)生成。结论均标注出处;未覆盖项单独列出,不编造。*")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="autoresearch deep 报告渲染")
    ap.add_argument("data", help="深挖数据 JSON")
    ap.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), help="日期")
    ap.add_argument("--out", default="-", help="输出 md 路径,- 为 stdout")
    args = ap.parse_args()
    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    md = render(data, args.date)
    if args.out == "-":
        print(md)
    else:
        Path(args.out).write_text(md, encoding="utf-8")
        print(f"[render_deep] 深挖报告 → {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
