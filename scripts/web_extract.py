#!/usr/bin/env python3
"""autoresearch · 网页正文抓取( WebFetch 被拦时的降级方案 )

deep 模式读博客/技术文章用。claude.ai 的 WebFetch 对很多域名被拦,
但 curl 能下;本脚本 curl 下 HTML + bs4 提正文。

用法:
    python web_extract.py "https://developer.nvidia.com/blog/..." --out tmp/web/nvidia.json
    python web_extract.py < urls.txt --out tmp/web/batch.json   # stdin 每行一个 url

输出 JSON: {url, title, text, n_chars, ok}
依赖:requests 或 curl( 系统 )+ beautifulsoup4。缺 bs4 时退回正则提取。
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    from bs4 import BeautifulSoup
    HAVE_BS4 = True
except ImportError:
    HAVE_BS4 = False


def fetch_html(url, timeout=40):
    """curl 下载 HTML( 比 urllib 更能绕基础反爬 )。"""
    result = subprocess.run(
        ["curl", "-sL", "-A", "Mozilla/5.0 autoresearch/0.1", "--max-time", str(timeout), url],
        capture_output=True, timeout=timeout + 10,
    )
    html = result.stdout.decode("utf-8", errors="replace")
    if len(html) < 200:
        raise ValueError(f"HTML 太短( {len(html)} 字符 ),可能被拦/404")
    return html


def extract(html):
    """提取标题 + 正文。bs4 优先,否则正则。"""
    if HAVE_BS4:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()
        title = (soup.title.string.strip() if soup.title and soup.title.string else "")
        # 优先 article/main,否则 body
        main = soup.find("article") or soup.find("main") or soup.body or soup
        text = main.get_text(separator="\n")
    else:
        m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
        title = (m.group(1).strip() if m else "")
        t = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.S | re.I)
        t = re.sub(r"<style[^>]*>.*?</style>", "", t, flags=re.S | re.I)
        t = re.sub(r"<nav[^>]*>.*?</nav>", "", t, flags=re.S | re.I)
        t = re.sub(r"<footer[^>]*>.*?</footer>", "", t, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", "\n", t)
    # 清理空白
    lines = [ln.strip() for ln in text.splitlines()]
    text = "\n".join(ln for ln in lines if ln)
    return title, text


def process(url):
    try:
        html = fetch_html(url)
        title, text = extract(html)
        return {"url": url, "title": title, "text": text, "n_chars": len(text), "ok": True}
    except Exception as e:
        return {"url": url, "title": "", "text": "", "n_chars": 0, "ok": False, "error": str(e)}


def main():
    ap = argparse.ArgumentParser(description="autoresearch 网页正文抓取")
    ap.add_argument("url", nargs="?", help="单个 URL;不传则从 stdin 读( 每行一个 )")
    ap.add_argument("--out", required=True, help="输出 JSON 路径")
    args = ap.parse_args()

    urls = []
    if args.url:
        urls = [args.url]
    else:
        urls = [ln.strip() for ln in sys.stdin if ln.strip()]

    if not HAVE_BS4:
        print("[web] 警告:无 bs4,用正则提取( 质量较低 )。pip install beautifulsoup4", file=sys.stderr)

    results = [process(u) for u in urls]
    payload = {"results": results} if len(results) > 1 else results[0]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for r in results if r.get("ok"))
    print(f"[web] {ok}/{len(results)} 成功 → {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
