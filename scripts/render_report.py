#!/usr/bin/env python3
"""autoresearch · 周报渲染

用法:
    python render_report.py briefs.json --topic "..." [--date 2026-08-12] [--out report.md]

输入 briefs.json:agent 已完成"筛选 Top N + 写简评"后的条目数组,每条含原始字段 + 额外字段:
    { ..., "brief": "做了啥+为啥重要+适合谁( 3-5 句 )", "tag": "paper|blog|repo|..." }
外加可选顶层字段 overview / trends( 若 agent 提供,否则留占位让 agent 后填 )。
输出:周报 Markdown( 概览 / 值得看 / 趋势 / 引用 )。

本脚本只做"格式拼装",不调用 LLM —— 简评由 agent 在调用本脚本前写好。
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

TYPE_CN = {"paper": "论文", "blog": "博客", "repo": "开源项目", "release": "新版本",
           "discussion": "讨论", "report": "报告", "video": "视频"}
SOURCE_CN = {"arxiv": "arXiv", "web": "Web", "github": "GitHub", "community": "社区"}


def render(topic, date, days, payload):
    items = payload.get("items", [])
    overview = payload.get("overview", "_( 待 agent 填写本期概览 )_")
    trends = payload.get("trends", [])
    hotspots = payload.get("hotspots", [])
    window = f"近 {days} 天" if days else "不限"
    lines = [
        f"# 技术动向周报 · {topic}",
        "",
        f"> **主题**:`{topic}`  ",
        f"> **时间窗**:{window}  ",
        f"> **检索源**:arXiv · 开放 Web · GitHub · 社区( 中英 )  ",
        f"> **生成方式**:autoresearch skill · 简单总结模式  ",
        f"> **生成日期**:{date}",
        "",
        "---",
        "",
        "## 本期概览",
        "",
        overview,
        "",
        f"## 值得看( {len(items)} 篇 )",
        "",
    ]
    for i, it in enumerate(items, 1):
        typ = TYPE_CN.get(it.get("type", ""), it.get("type", ""))
        src = SOURCE_CN.get(it.get("source", ""), it.get("source", ""))
        url = it.get("url", "")
        title = it.get("title", "")
        lines.append(f"### {i}. {title}")
        lines.append(f"**类型**:{typ} · **源**:{src} · **链接**:[{url}]({url})")
        lines.append("")
        lines.append(f"> {it.get('brief', '_( 待补简评 )_').strip()}")
        lines.append("")
        lines.append("---")
        lines.append("")
    # 本期热点( 热点检测环节产出 )
    lines.append("## 本期热点")
    lines.append("")
    if hotspots:
        for h in hotspots:
            heat = h.get("heat_type", "")
            reason = h.get("reason", "")
            url = h.get("url", "")
            title = h.get("title", "")
            tag = f"**[{heat}]** " if heat else ""
            lines.append(f"- {tag}[{title}]({url}) — {reason}")
    else:
        lines.append("_( 本期无明显爆发热点 )_")
    lines.append("")
    lines.append("## 趋势观察")
    lines.append("")
    if trends:
        for j, t in enumerate(trends, 1):
            lines.append(f"{j}. {t}")
    else:
        lines.append("_( 待 agent 填写跨条目趋势归纳 )_")
    lines.append("")
    lines.append("## 引用")
    lines.append("")
    lines.append("| # | 来源 | 链接 |")
    lines.append("|---|---|---|")
    for i, it in enumerate(items, 1):
        src = SOURCE_CN.get(it.get("source", ""), it.get("source", ""))
        lines.append(f"| {i} | {src} | {it.get('url','')} |")
    lines.append("")
    lines.append("---")
    lines.append("*由 autoresearch skill(简单总结模式)生成。*")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="autoresearch 周报渲染")
    ap.add_argument("briefs", help="简评后的条目 JSON( 含 brief 字段 )")
    ap.add_argument("--topic", required=True, help="周报主题")
    ap.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), help="日期")
    ap.add_argument("--days", default=None, type=int, help="时间窗天数,填入报告头部")
    ap.add_argument("--out", default="-", help="输出 md 路径,- 为 stdout")
    args = ap.parse_args()
    payload = json.loads(Path(args.briefs).read_text(encoding="utf-8"))
    # 兼容:若文件直接是数组,包成对象
    if isinstance(payload, list):
        payload = {"items": payload}
    md = render(args.topic, args.date, args.days, payload)
    if args.out == "-":
        print(md)
    else:
        Path(args.out).write_text(md, encoding="utf-8")
        print(f"[render] 周报 → {args.out}", file=__import__("sys").stderr)


if __name__ == "__main__":
    main()
